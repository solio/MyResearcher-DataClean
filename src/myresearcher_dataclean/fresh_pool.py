"""Create a deterministic, semantic-agnostic ROUND-004 fresh text pool.

The Collector ``posts`` table is a mutable list/backfill view rather than the
canonical ``source_item_observations`` contract.  This module deliberately
keeps that distinction explicit: it reads the posts adapter, applies only
surface/text-completeness rules, and emits answer-free records for a later
DataClean/ModelTraining hand-off.  No model, label, or financial meaning is
used during selection.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sqlite3
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .collector_sqlite import CollectorContractError, read_collector_posts
from .normalization import normalize_text
from .pipeline import canonical_json_bytes

FRESH_POOL_VERSION = "round-004.fresh-pool.v2"
# Keep source-selection ordering compatible with v1 while v2 changes only the
# model-facing text representation.
SELECTION_VERSION = "round-004.fresh-pool.v1"
DEFAULT_SEED = 20260914
DEFAULT_SIZE = 2000
TITLE_ONLY_MAX_LENGTH = 38  # equivalent to the requested normalized length <39

_STOCK_NAMES = {
    "002028": "思源电气",
    "002463": "沪电股份",
    "002648": "卫星化学",
    "002891": "中宠股份",
    "300054": "鼎龙股份",
    "300487": "蓝晓科技",
    "300666": "江丰电子",
    "600312": "平高电气",
    "601012": "隆基绿能",
    "601888": "中国中免",
    "603039": "泛微网络",
    "603179": "新泉股份",
    "603806": "福斯特",
    "603997": "继峰股份",
    "605020": "永和股份",
    "688676": "金盘科技",
}

_OPENING_PUNCTUATION = frozenset(
    ",，、:：;；([{（［｛《「『“‘"
)
_BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
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
)
_INVISIBLE_TAGS = frozenset({"script", "style", "noscript", "template"})


class _ForumVisibleTextExtractor(HTMLParser):
    """Extract visible forum text while discarding markup and attributes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._invisible_depth = 0
        self.had_markup = False

    def _newline(self) -> None:
        if self.parts and self.parts[-1] != "\n":
            self.parts.append("\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        lowered = tag.lower()
        self.had_markup = True
        if self._invisible_depth:
            if lowered in _INVISIBLE_TAGS:
                self._invisible_depth += 1
            return
        if lowered in _INVISIBLE_TAGS:
            self._invisible_depth = 1
            return
        if lowered in _BLOCK_TAGS:
            self._newline()

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        del attrs
        self.had_markup = True
        if not self._invisible_depth and tag.lower() in _BLOCK_TAGS:
            self._newline()

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        self.had_markup = True
        if self._invisible_depth:
            if lowered in _INVISIBLE_TAGS:
                self._invisible_depth -= 1
            return
        if lowered in _BLOCK_TAGS:
            self._newline()

    def handle_data(self, data: str) -> None:
        if not self._invisible_depth:
            self.parts.append(data)

    def handle_comment(self, data: str) -> None:
        del data

    def result(self) -> str:
        return "".join(self.parts)


def _forum_visible_text(value: str) -> str:
    """Return text visible to a reader, with HTML structure removed."""

    return _forum_visible_text_details(value)[0]


def _forum_visible_text_details(value: str) -> tuple[str, bool]:
    """Return visible text plus whether an HTML tag was encountered."""

    parser = _ForumVisibleTextExtractor()
    parser.feed(value)
    parser.close()
    return parser.result(), parser.had_markup


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_key(seed: int, namespace: str, value: str) -> bytes:
    return hashlib.sha256(f"{SELECTION_VERSION}|{seed}|{namespace}|{value}".encode()).digest()


def _exact_content_group(title: Any, content: Any) -> str:
    return _sha256_bytes(canonical_json_bytes({"title": title, "content": content}))


def _normalized_group(model_text: str) -> str:
    return _sha256_bytes(model_text.encode("utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValueError(f"JSONL input does not exist: {path}")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"JSONL record must be an object at {path}:{line_number}")
        records.append(value)
    return records


def _read_legacy_source_item_ids(database: Path) -> set[str]:
    if not database.is_file():
        raise CollectorContractError(f"Collector database does not exist: {database}")
    uri = database.resolve().as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as exc:
        raise CollectorContractError(
            f"cannot open legacy Collector database read-only: {database}"
        ) from exc
    try:
        columns = {
            row[1]
            for row in connection.execute(
                'PRAGMA table_info("source_item_observations")'
            ).fetchall()
        }
        if "source_item_id" not in columns:
            raise CollectorContractError(
                "legacy Collector table source_item_observations is missing source_item_id"
            )
        try:
            return {
                str(row[0])
                for row in connection.execute(
                    "SELECT DISTINCT source_item_id FROM source_item_observations"
                )
            }
        except sqlite3.DatabaseError as exc:
            raise CollectorContractError(
                "cannot read legacy Collector source_item_ids"
            ) from exc
    finally:
        connection.close()


def _is_nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _effective_raw_text(row: Mapping[str, Any]) -> tuple[str, str]:
    content = row.get("content")
    if _is_nonempty(content):
        return str(content), "CONTENT"
    title = row.get("title")
    return (str(title) if title is not None else ""), "TITLE_ONLY"


def _normalized_model_text(raw_text: str, text_source: str) -> tuple[str, bool]:
    """Normalize visible text and report whether HTML structure was removed."""

    if text_source == "CONTENT":
        visible_text, had_markup = _forum_visible_text_details(raw_text)
    else:
        visible_text, had_markup = raw_text, False
    return normalize_text(visible_text).text, had_markup


def _text_is_word_bearing(value: str) -> bool:
    return any(character.isalnum() or "\u3400" <= character <= "\u9fff" for character in value)


def _fragment_reason(value: str) -> str | None:
    """Return a structural rejection reason, never a semantic judgement."""

    if not value.strip():
        return "EMPTY_AFTER_NORMALIZE"
    if not _text_is_word_bearing(value):
        return "PURE_PUNCTUATION"
    if value[-1] in _OPENING_PUNCTUATION:
        return "OBVIOUS_FRAGMENT"
    return None


def _length_bucket(value: str) -> str:
    length = len(value)
    if length <= 8:
        return "VERY_SHORT"
    if length <= 20:
        return "MEDIUM_LENGTH"
    return "LONGER_TEXT"


def _month_bucket(value: Any) -> str:
    text = str(value or "")
    return text[:7] if len(text) >= 7 else "UNKNOWN"


def _load_covered_normalized_groups(
    pilot_records: Sequence[Mapping[str, Any]], covered_groups: set[str]
) -> set[str]:
    """Recover normalized identities for covered ROUND-003 groups when possible."""

    normalized: set[str] = set()
    for record in pilot_records:
        title = record.get("title")
        content = record.get("content")
        raw_group = record.get("exact_content_group") or _exact_content_group(title, content)
        if raw_group not in covered_groups:
            continue
        value = content if _is_nonempty(content) else title
        text_source = "CONTENT" if _is_nonempty(content) else "TITLE_ONLY"
        model_text = normalize_text(str(value or "")).text
        if model_text:
            normalized.add(_normalized_group(model_text))
    return normalized


def _allocate_counts(sizes: Mapping[Any, int], total: int) -> dict[Any, int]:
    """Allocate ``total`` proportionally with deterministic largest remainders."""

    keys = sorted(sizes, key=lambda item: str(item))
    if total < 0 or total > sum(sizes.values()):
        raise ValueError("allocation total is outside available capacity")
    if not keys or total == 0:
        return {key: 0 for key in keys}

    counts = {key: 0 for key in keys}
    if total < len(keys):
        chosen = sorted(keys, key=lambda key: (-sizes[key], str(key)))[:total]
        for key in chosen:
            counts[key] = 1
        return counts

    # Give every non-empty stratum one slot, then distribute the remainder by
    # residual capacity.  This preserves representation without forcing equal
    # stock/source proportions.
    for key in keys:
        counts[key] = 1
    remaining = total - len(keys)
    capacities = {key: sizes[key] - 1 for key in keys}
    capacity_total = sum(capacities.values())
    if remaining == 0 or capacity_total == 0:
        return counts

    floors: dict[Any, int] = {}
    fractions: list[tuple[float, str, Any]] = []
    assigned = 0
    for key in keys:
        share = remaining * capacities[key] / capacity_total
        floor = min(capacities[key], int(share))
        floors[key] = floor
        assigned += floor
        fractions.append((share - floor, str(key), key))
    for key, floor in floors.items():
        counts[key] += floor
    for _, _, key in sorted(fractions, key=lambda item: (-item[0], item[1]))[: remaining - assigned]:
        if counts[key] < sizes[key]:
            counts[key] += 1
    return counts


def _representatives(
    groups: Mapping[str, Sequence[dict[str, Any]]], seed: int
) -> list[dict[str, Any]]:
    representatives: list[dict[str, Any]] = []
    for selection_group, rows in groups.items():
        representative = min(
            rows,
            key=lambda row: _stable_key(
                seed,
                "REPRESENTATIVE",
                f"{row.get('source', '')}\0{row.get('source_item_id', '')}",
            ),
        )
        candidate = dict(representative)
        candidate["_selection_group"] = selection_group
        representatives.append(candidate)
    return representatives


def _select_representatives(
    representatives: Sequence[dict[str, Any]], target_size: int, seed: int
) -> list[dict[str, Any]]:
    if target_size > len(representatives):
        raise ValueError(
            f"only {len(representatives)} distinct eligible groups available; need {target_size}"
        )
    by_stock: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in representatives:
        by_stock[str(row.get("stock_code") or "UNKNOWN")].append(row)
    stock_quota = _allocate_counts(
        {stock: len(rows) for stock, rows in by_stock.items()}, target_size
    )

    selected: list[dict[str, Any]] = []
    for stock in sorted(by_stock):
        rows = by_stock[stock]
        strata: defaultdict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            key = (
                str(row["_text_source"]),
                str(row["_selection_length_bucket"]),
                str(row["_month_bucket"]),
            )
            strata[key].append(row)
        stratum_quota = _allocate_counts(
            {key: len(values) for key, values in strata.items()}, stock_quota[stock]
        )
        for key in sorted(strata, key=lambda value: str(value)):
            quota = stratum_quota[key]
            ordered = sorted(
                strata[key],
                key=lambda row: _stable_key(
                    seed,
                    f"SELECT|{stock}|{key}",
                    str(row["_selection_group"]),
                ),
            )
            selected.extend(ordered[:quota])
    if len(selected) != target_size:
        raise AssertionError(f"selection produced {len(selected)} rows, expected {target_size}")
    return selected


def _output_record(row: Mapping[str, Any], collector_db_sha256: str) -> dict[str, Any]:
    model_text = str(row["_model_text"])
    source = str(row.get("source") or "")
    source_item_id = str(row.get("source_item_id") or "")
    sample_id = "fresh-" + _sha256_bytes(f"{source}\0{source_item_id}".encode())
    return {
        "sample_id": sample_id,
        "source": row.get("source"),
        "source_item_id": row.get("source_item_id"),
        "stock_code": row.get("stock_code"),
        "stock_name": _STOCK_NAMES.get(str(row.get("stock_code") or ""), ""),
        "published_at": row.get("published_at"),
        "title": row.get("title"),
        "content": row.get("content"),
        "model_text": model_text,
        "text_length": len(model_text),
        "text_source": row["_text_source"],
        "exact_content_group": row["_exact_content_group"],
        "normalized_model_text_group": row["_normalized_group"],
        "url": row.get("url"),
        "author_id": row.get("author_id"),
        "author_name": row.get("author_name"),
        "read_count": row.get("read_count"),
        "reply_count": row.get("reply_count"),
        "like_count": row.get("like_count"),
        "forward_count": row.get("forward_count"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "collector_row_locator": {
            "table": "posts",
            "source": row.get("source"),
            "source_item_id": row.get("source_item_id"),
        },
        "collector_db_sha256": collector_db_sha256,
    }


def _distribution(records: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(collections.Counter(str(record.get(key) or "UNKNOWN") for record in records).items()))


def build_fresh_pool(
    posts: Sequence[Mapping[str, Any]],
    *,
    legacy_source_item_ids: set[str],
    pilot_source_item_ids: set[str],
    covered_groups: set[str],
    pilot_records: Sequence[Mapping[str, Any]],
    collector_db_sha256: str,
    target_size: int = DEFAULT_SIZE,
    seed: int = DEFAULT_SEED,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build the selected pool and a deterministic profile from in-memory rows."""

    filter_counts: collections.Counter[str] = collections.Counter()
    filter_counts["collector_posts_total"] = len(posts)
    covered_normalized_groups = _load_covered_normalized_groups(
        pilot_records, covered_groups
    )
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_fresh_ids: set[str] = set()
    for original in posts:
        source_item_id = str(original.get("source_item_id") or "")
        if source_item_id in legacy_source_item_ids:
            filter_counts["excluded_legacy_source_item"] += 1
            continue
        if source_item_id in pilot_source_item_ids:
            filter_counts["excluded_round003_pilot_source_item"] += 1
            continue
        filter_counts["fresh_source_rows"] += 1
        if source_item_id in seen_fresh_ids:
            filter_counts["excluded_duplicate_source_item"] += 1
            continue
        seen_fresh_ids.add(source_item_id)

        title = original.get("title")
        content = original.get("content")
        body_present = _is_nonempty(content)
        raw_text, text_source = _effective_raw_text(original)
        raw_normalized = normalize_text(raw_text).text
        normalized, html_had_markup = _normalized_model_text(raw_text, text_source)
        html_cleaned = html_had_markup and raw_normalized != normalized
        prefilter_exact_group = _exact_content_group(
            title,
            content if body_present else title,
        )
        prefilter_selection_group = _normalized_group(raw_normalized)
        if (
            prefilter_exact_group in covered_groups
            or prefilter_selection_group in covered_normalized_groups
        ):
            filter_counts[
                "fresh_rows_matching_covered_group_before_text_filters"
            ] += 1
        if not body_present and len(raw_normalized) > TITLE_ONLY_MAX_LENGTH:
            filter_counts["excluded_title_only_39_40_or_longer"] += 1
            continue
        if not raw_normalized:
            filter_counts["excluded_empty_after_normalize"] += 1
            continue
        reason = _fragment_reason(raw_normalized)
        if reason == "PURE_PUNCTUATION":
            filter_counts["excluded_pure_punctuation"] += 1
            continue
        if reason == "OBVIOUS_FRAGMENT":
            filter_counts["excluded_obvious_fragment"] += 1
            continue
        if reason == "EMPTY_AFTER_NORMALIZE":
            filter_counts["excluded_empty_after_normalize"] += 1
            continue

        exact_group = prefilter_exact_group
        cleaned_group = _normalized_group(normalized)
        if exact_group in covered_groups or prefilter_selection_group in covered_normalized_groups:
            filter_counts["excluded_human_covered_content_group"] += 1
            continue

        candidate = dict(original)
        candidate["_model_text"] = normalized
        candidate["_text_source"] = text_source
        candidate["_length_bucket"] = _length_bucket(normalized)
        candidate["_selection_length_bucket"] = _length_bucket(raw_normalized)
        candidate["_month_bucket"] = _month_bucket(original.get("published_at"))
        candidate["_exact_content_group"] = exact_group
        candidate["_selection_group"] = prefilter_selection_group
        candidate["_normalized_group"] = cleaned_group
        candidate["_html_had_markup"] = html_had_markup
        candidate["_html_cleaned"] = html_cleaned
        groups[candidate["_selection_group"]].append(candidate)

    for name in (
        "excluded_round003_pilot_source_item",
        "excluded_duplicate_source_item",
        "excluded_empty_after_normalize",
        "excluded_pure_punctuation",
        "excluded_obvious_fragment",
        "excluded_human_covered_content_group",
    ):
        filter_counts.setdefault(name, 0)
    filter_counts["eligible_rows_before_normalized_dedupe"] = sum(
        len(values) for values in groups.values()
    )
    filter_counts["normalized_duplicate_rows_removed"] = sum(
        max(0, len(values) - 1) for values in groups.values()
    )
    filter_counts["eligible_distinct_selection_groups"] = len(groups)
    filter_counts["eligible_distinct_cleaned_model_text_groups"] = len(
        {
            row["_normalized_group"]
            for values in groups.values()
            for row in values
        }
    )
    eligible_rows_with_html_cleaned_content = sum(
        bool(row.get("_html_cleaned"))
        for values in groups.values()
        for row in values
    )
    representatives = _representatives(groups, seed)
    selected_rows = _select_representatives(representatives, target_size, seed)
    if len({row["_normalized_group"] for row in selected_rows}) != target_size:
        raise ValueError("HTML extraction created a duplicate selected model_text group")
    selected = [
        _output_record(row, collector_db_sha256)
        for row in sorted(
            selected_rows,
            key=lambda row: (
                str(row.get("stock_code") or ""),
                str(row.get("published_at") or ""),
                str(row.get("source_item_id") or ""),
            ),
        )
    ]
    profile = {
        "profile_version": FRESH_POOL_VERSION,
        "seed": seed,
        "target_size": target_size,
        "selection_unit": "existing v1 representative set retained; v2 only replaces model_text representation",
        "semantic_labels_present": False,
        "model_predictions_present": False,
        "filter_counts": dict(sorted(filter_counts.items())),
        "selected_count": len(selected),
        "html_tag_records_seen_in_selected_pool": sum(
            bool(row.get("_html_had_markup")) for row in selected_rows
        ),
        "html_cleaned_content_records_in_eligible_rows": eligible_rows_with_html_cleaned_content,
        "html_cleaned_content_records_in_selected_pool": sum(
            bool(row.get("_html_cleaned")) for row in selected_rows
        ),
        "selected_stock_distribution": _distribution(selected, "stock_code"),
        "selected_month_distribution": _distribution(selected, "published_at_month"),
        "selected_text_source_distribution": _distribution(selected, "text_source"),
        "selected_length_distribution": _distribution(selected, "length_bucket"),
        "selection_policy": {
            "fresh_source_item": "source_item_id absent from legacy canonical observations and ROUND-003 pilot",
            "title_only_max_normalized_length": TITLE_ONLY_MAX_LENGTH,
            "body_length_policy": "nonempty content is retained after normalize_text regardless of length",
            "invalid_text_policy": [
                "empty after normalization",
                "pure punctuation/symbols",
                "obvious trailing-open-punctuation fragment",
            ],
            "deduplication": "v1 selection identity retained; cleaned model_text groups are re-hashed and must remain unique",
            "stratification": "stock-proportional quotas, then proportional source/length/month strata with deterministic largest remainders",
        },
        "stock_name_source": "fixed mapping for the 16 configured Collector stock codes; unknown codes remain empty",
    }
    # The temporary selection metadata is intentionally not emitted in records.
    for record, row in zip(selected, sorted(selected_rows, key=lambda row: (
        str(row.get("stock_code") or ""),
        str(row.get("published_at") or ""),
        str(row.get("source_item_id") or ""),
    ))):
        record["published_at_month"] = row.get("_month_bucket")
        record["length_bucket"] = row.get("_length_bucket")
    # Recompute distributions after attaching derived profile-only fields and
    # then remove those fields from the public records.
    profile["selected_month_distribution"] = _distribution(selected, "published_at_month")
    profile["selected_length_distribution"] = _distribution(selected, "length_bucket")
    for record in selected:
        record.pop("published_at_month", None)
        record.pop("length_bucket", None)
    return selected, profile


def _jsonl(records: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(canonical_json_bytes(record) + b"\n" for record in records)


def run(
    collector_db: str | Path,
    legacy_db: str | Path,
    pilot_jsonl: str | Path,
    coverage_jsonl: str | Path,
    output_directory: str | Path,
    *,
    target_size: int = DEFAULT_SIZE,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    collector_path = Path(collector_db).resolve()
    legacy_path = Path(legacy_db).resolve()
    pilot_path = Path(pilot_jsonl).resolve()
    coverage_path = Path(coverage_jsonl).resolve()
    output_path = Path(output_directory)
    posts = read_collector_posts(collector_path)
    legacy_ids = _read_legacy_source_item_ids(legacy_path)
    pilot_records = _read_jsonl(pilot_path)
    pilot_ids = {str(record.get("source_item_id")) for record in pilot_records if record.get("source_item_id") is not None}
    coverage_records = _read_jsonl(coverage_path)
    covered_groups = {
        str(record["exact_content_group"])
        for record in coverage_records
        if record.get("exact_content_group")
    }
    selected, profile = build_fresh_pool(
        posts,
        legacy_source_item_ids=legacy_ids,
        pilot_source_item_ids=pilot_ids,
        covered_groups=covered_groups,
        pilot_records=pilot_records,
        collector_db_sha256=_sha256_path(collector_path),
        target_size=target_size,
        seed=seed,
    )
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "fresh-pool-2000.jsonl"
    output_bytes = _jsonl(selected)
    output_file.write_bytes(output_bytes)
    profile.update(
        {
            "inputs": {
                "collector_db": str(collector_path),
                "collector_db_sha256": _sha256_path(collector_path),
                "legacy_db": str(legacy_path),
                "legacy_db_sha256": _sha256_path(legacy_path),
                "pilot_jsonl": str(pilot_path),
                "pilot_jsonl_sha256": _sha256_path(pilot_path),
                "coverage_jsonl": str(coverage_path),
                "coverage_jsonl_sha256": _sha256_path(coverage_path),
                "coverage_rows": len(coverage_records),
                "coverage_exact_content_groups": len(covered_groups),
            },
            "output": {
                "path": str(output_file),
                "sha256": _sha256_bytes(output_bytes),
                "bytes": len(output_bytes),
            },
        }
    )
    (output_path / "fresh-pool-profile.json").write_bytes(
        canonical_json_bytes(profile) + b"\n"
    )
    return profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create the ROUND-004 fresh text pool.")
    parser.add_argument("collector_db", type=Path)
    parser.add_argument("legacy_db", type=Path)
    parser.add_argument("pilot_jsonl", type=Path)
    parser.add_argument("coverage_jsonl", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        profile = run(
            arguments.collector_db,
            arguments.legacy_db,
            arguments.pilot_jsonl,
            arguments.coverage_jsonl,
            arguments.output_directory,
            target_size=arguments.size,
            seed=arguments.seed,
        )
    except (CollectorContractError, ValueError) as exc:
        print(f"ROUND-004 fresh-pool error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(profile, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
