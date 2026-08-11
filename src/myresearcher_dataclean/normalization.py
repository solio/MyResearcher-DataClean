"""Conservative, semantic-ignorant text normalization rules."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Sequence


_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "div",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "section",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}
_INLINE_TAGS = {
    "a",
    "abbr",
    "b",
    "big",
    "cite",
    "code",
    "del",
    "em",
    "font",
    "i",
    "ins",
    "mark",
    "s",
    "small",
    "span",
    "strike",
    "strong",
    "sub",
    "sup",
    "time",
    "u",
}
_HORIZONTAL_SPACE = re.compile(r"[\t\f\v \u00a0\u2000-\u200a\u202f\u205f\u3000]+")


@dataclass(frozen=True)
class NormalizedText:
    text: str
    rules_applied: tuple[str, ...]


class _ConservativeHTMLTextExtractor(HTMLParser):
    """Remove known markup while preserving unknown angle-bracket text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._anchors: list[tuple[str | None, int]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        attributes = dict(attrs)
        if lowered == "br":
            self.parts.append("\n")
        elif lowered == "img":
            alt = attributes.get("alt")
            if alt:
                self.parts.append(alt)
            source = attributes.get("src")
            if source and source.startswith(("http://", "https://")):
                self.parts.append(f" ({source})" if alt else source)
        elif lowered in _BLOCK_TAGS:
            self.parts.append("\n")
        elif lowered == "a":
            self._anchors.append((attributes.get("href"), len(self.parts)))
        elif lowered not in _INLINE_TAGS:
            self.parts.append(self.get_starttag_text() or f"<{tag}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered == "br":
            self.parts.append("\n")
        elif lowered == "img":
            attributes = dict(attrs)
            alt = attributes.get("alt")
            if alt:
                self.parts.append(alt)
            source = attributes.get("src")
            if source and source.startswith(("http://", "https://")):
                self.parts.append(f" ({source})" if alt else source)
        elif lowered in _BLOCK_TAGS:
            self.parts.append("\n")
        elif lowered not in _INLINE_TAGS:
            self.parts.append(self.get_starttag_text() or f"<{tag}/>")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "a":
            href, start = (
                self._anchors.pop() if self._anchors else (None, len(self.parts))
            )
            anchor_text = "".join(self.parts[start:])
            if href and href not in anchor_text:
                self.parts.append(f" ({href})" if anchor_text.strip() else href)
        elif lowered in _BLOCK_TAGS:
            self.parts.append("\n")
        elif lowered not in _INLINE_TAGS and lowered not in {"br", "img"}:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        # convert_charrefs normally routes entities through handle_data. These
        # fallbacks preserve malformed parser edge cases rather than dropping.
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        del data

    def result(self) -> str:
        return "".join(self.parts)


def _html_to_text(value: str) -> str:
    parser = _ConservativeHTMLTextExtractor()
    parser.feed(value)
    parser.close()
    return parser.result()


def _normalize_whitespace(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_HORIZONTAL_SPACE.sub(" ", line).strip() for line in value.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    result: list[str] = []
    previous_blank = False
    for line in lines:
        blank = not line
        if blank and previous_blank:
            continue
        result.append(line)
        previous_blank = blank
    return "\n".join(result)


def normalize_text(value: str) -> NormalizedText:
    """Apply only deterministic surface normalization, never semantic rules."""

    rules: list[str] = []
    current = unicodedata.normalize("NFC", value)
    if current != value:
        rules.append("UNICODE_NFC")

    without_bom = current.lstrip("\ufeff")
    if without_bom != current:
        rules.append("LEADING_BOM_REMOVED")
    current = without_bom

    without_markup = _html_to_text(current)
    if without_markup != current:
        rules.append("HTML_TO_TEXT")
    current = without_markup

    normalized_space = _normalize_whitespace(current)
    if normalized_space != current:
        rules.append("WHITESPACE_NORMALIZED")

    return NormalizedText(normalized_space, tuple(rules))


def merge_rule_lists(*rule_lists: Sequence[str]) -> list[str]:
    """Return stable first-seen rule order across title and content."""

    merged: list[str] = []
    for rules in rule_lists:
        for rule in rules:
            if rule not in merged:
                merged.append(rule)
    return merged
