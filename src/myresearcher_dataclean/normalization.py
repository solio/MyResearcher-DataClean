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
_SAFE_PRESENTATION_TAGS = {
    "b",
    "big",
    "em",
    "font",
    "i",
    "small",
    "span",
    "strong",
    "u",
}
_MEANING_BEARING_TAGS = {"del", "s", "strike"}
_VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
_HORIZONTAL_SPACE = re.compile(r"[\t\f\v \u00a0\u2000-\u200a\u202f\u205f\u3000]+")


@dataclass(frozen=True)
class NormalizedText:
    text: str
    rules_applied: tuple[str, ...]


class _ConservativeHTMLTextExtractor(HTMLParser):
    """Apply the narrow HTML policy while preserving unproved structure."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._open_tags: list[tuple[str, str]] = []

    def _remember(self, tag: str, mode: str) -> None:
        if tag not in _VOID_TAGS:
            self._open_tags.append((tag, mode))

    def _take_mode(self, tag: str) -> str | None:
        for index in range(len(self._open_tags) - 1, -1, -1):
            if self._open_tags[index][0] == tag:
                _, mode = self._open_tags.pop(index)
                return mode
        return None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        raw_tag = self.get_starttag_text() or f"<{tag}>"
        if lowered == "br" and not attrs:
            self.parts.append("\n")
        elif lowered in _BLOCK_TAGS and not attrs:
            self.parts.append("\n")
            self._remember(lowered, "layout")
        elif lowered in _SAFE_PRESENTATION_TAGS and not attrs:
            self._remember(lowered, "presentation")
        else:
            # Meaning-bearing tags, tags with unproved attributes, and all
            # unknown tags retain a visible/recoverable marker.
            self.parts.append(raw_tag)
            mode = "preserved_layout" if lowered in _BLOCK_TAGS else "preserved"
            if mode == "preserved_layout":
                self.parts.append("\n")
            self._remember(lowered, mode)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered == "br" and not attrs:
            self.parts.append("\n")
        elif lowered in _BLOCK_TAGS and not attrs:
            self.parts.append("\n")
        elif lowered in _SAFE_PRESENTATION_TAGS and not attrs:
            return
        else:
            self.parts.append(self.get_starttag_text() or f"<{tag}/>")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        mode = self._take_mode(lowered)
        if mode == "layout":
            self.parts.append("\n")
        elif mode == "presentation":
            return
        elif mode == "preserved_layout":
            self.parts.append("\n")
            self.parts.append(f"</{tag}>")
        elif mode == "preserved" or lowered in _MEANING_BEARING_TAGS:
            self.parts.append(f"</{tag}>")
        elif lowered not in _VOID_TAGS:
            # An unmatched end tag cannot be proven to be presentation-only.
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

    def handle_decl(self, decl: str) -> None:
        self.parts.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        self.parts.append(f"<?{data}>")

    def unknown_decl(self, data: str) -> None:
        self.parts.append(f"<![{data}]>")

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
