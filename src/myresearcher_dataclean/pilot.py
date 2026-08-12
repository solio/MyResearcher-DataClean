"""Deterministic, semantic-agnostic ROUND-003 real-observation pilot sampler.

This module deliberately operates on Collector observations, not CLEAN records.
It never changes title/content and never assigns quality, sentiment, or labels.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from .collector_sqlite import CollectorContractError, read_collector_records
from .pipeline import canonical_json_bytes

PILOT_SAMPLER_VERSION = "round-003.pilot.v1"
DEFAULT_SEED = 20260812
PILOT_SIZE = 300

_BUCKET_TARGETS = {
    "GENERAL_RANDOM": 120,
    "VERY_SHORT": 50,
    "MEDIUM_LENGTH": 40,
    "LONGER_TEXT": 30,
    "EXACT_CONTENT_REPEAT": 20,
    "METADATA_EXTREME": 20,
    "STRUCTURAL_PATTERN": 20,
}
_CSV_FIELDS = (
    "observation_id",
    "source",
    "source_item_id",
    "observation_version",
    "observed_at_utc",
    "published_at",
    "author_id",
    "author_name",
    "title",
    "content",
    "text_length",
    "read_count",
    "reply_count",
    "like_count",
    "forward_count",
    "exact_content_key",
    "exact_content_group",
    "exact_content_count",
    "sampling_reasons",
    "collector_lineage",
)
_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_TICKER_RE = re.compile(r"(?:\$?[0-9]{6}|[A-Za-z]{1,8}\.[A-Za-z]{1,8}|#[^#\s]{1,32})")
_WHITESPACE_RE = re.compile(r"\s")
_REPEATED_CHAR_RE = re.compile(r"(.)\1{3,}", re.DOTALL)
_PUNCT_RE = re.compile(r"[^\w\u3400-\u9fff\s]", re.UNICODE)


def _database_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_key(seed: int, bucket: str, observation_id: str) -> bytes:
    payload = f"{PILOT_SAMPLER_VERSION}|{seed}|{bucket}|{observation_id}".encode()
    return hashlib.sha256(payload).digest()


def _ordered(records: Iterable[Mapping[str, Any]], seed: int, bucket: str) -> list[dict[str, Any]]:
    return sorted(
        (dict(record) for record in records),
        key=lambda record: _stable_key(seed, bucket, str(record["observation_id"])),
    )


def _text(record: Mapping[str, Any]) -> str:
    """Use Collector content, falling back only when it is null.

    The fallback handles list-title records represented with a null content
    column while leaving both source fields untouched in the output.
    """

    content = record.get("content")
    if content is not None:
        return str(content)
    title = record.get("title")
    return "" if title is None else str(title)


def _text_length(record: Mapping[str, Any]) -> int:
    # Python's Unicode length is a stable visible-character proxy for this
    # pilot. No normalization, stripping, or semantic interpretation occurs.
    return len(_text(record))


def _exact_content_key(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        canonical_json_bytes({"title": record.get("title"), "content": record.get("content")})
    ).hexdigest()


def _metadata_value(record: Mapping[str, Any], field: str) -> int | float | None:
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _structural_features(record: Mapping[str, Any]) -> dict[str, bool]:
    text = _text(record)
    return {
        "PUNCTUATION": bool(_PUNCT_RE.search(text)),
        "DIGITS": any(character.isdigit() for character in text),
        "URL": bool(_URL_RE.search(text)),
        "TICKER_OR_TAG": bool(_TICKER_RE.search(text)),
        "SPECIAL_UNICODE": any(
            ord(character) > 0xFFFF or (0x2000 <= ord(character) <= 0x2BFF)
            for character in text
        ),
        "REPEATED_CHARACTERS": bool(_REPEATED_CHAR_RE.search(text)),
        "UNUSUAL_WHITESPACE": bool(_WHITESPACE_RE.search(text)) and (
            text != " ".join(text.split())
        ),
        "LONG_SYMBOL_RUN": bool(re.search(r"[^\w\u3400-\u9fff\s]{4,}", text)),
    }


def _select(records: Iterable[Mapping[str, Any]], count: int, seed: int, bucket: str) -> list[dict[str, Any]]:
    if count <= 0:
        return []
    return _ordered(records, seed, bucket)[:count]


def _select_metadata_extremes(records: list[dict[str, Any]], count: int, seed: int) -> list[dict[str, Any]]:
    fields = [field for field in ("reply_count", "read_count", "like_count") if any(
        _metadata_value(record, field) is not None for record in records
    )]
    if not fields:
        return []
    ranked: dict[str, dict[str, int]] = {}
    for field in fields:
        ordered = sorted(
            (record for record in records if _metadata_value(record, field) is not None),
            key=lambda record: (
                -float(_metadata_value(record, field) or 0),
                _stable_key(seed, f"METADATA_{field}", str(record["observation_id"])),
            ),
        )
        ranked[field] = {str(record["observation_id"]): index for index, record in enumerate(ordered)}
    scored = sorted(
        records,
        key=lambda record: (
            min((ranked[field].get(str(record["observation_id"]), len(records)) for field in fields)),
            _stable_key(seed, "METADATA_EXTREME", str(record["observation_id"])),
        ),
    )
    return scored[:count]


def _make_lineage(record: Mapping[str, Any], database_path: Path, database_sha256: str) -> dict[str, Any]:
    keys = (
        "collector_storage_version",
        "schema_version",
        "collector_version",
        "parser_version",
        "fact_fingerprint",
        "drift_from_observation_id",
        "content_sha256",
        "url",
        "source_times_raw",
        "source_metadata",
        "raw_evidence",
        "scopes",
    )
    lineage = {key: record.get(key) for key in keys}
    lineage["collector_database"] = str(database_path)
    lineage["source_db_fingerprint"] = database_sha256
    return lineage


def _output_record(
    record: Mapping[str, Any],
    reasons: list[str],
    exact_count: int,
    database_path: Path,
    database_sha256: str,
) -> dict[str, Any]:
    key = _exact_content_key(record)
    return {
        "observation_id": record["observation_id"],
        "source": record.get("source"),
        "source_item_id": record.get("source_item_id"),
        "observation_version": record.get("observation_version"),
        "observed_at_utc": record.get("observed_at_utc"),
        "published_at": record.get("published_at_utc"),
        "author_id": record.get("author_id"),
        "author_name": record.get("author_name"),
        "title": record.get("title"),
        "content": record.get("content"),
        "text_length": _text_length(record),
        "read_count": record.get("read_count"),
        "reply_count": record.get("reply_count"),
        "like_count": record.get("like_count"),
        "forward_count": record.get("forward_count"),
        "exact_content_key": key,
        "exact_content_group": key,
        "exact_content_count": exact_count,
        "sampling_reasons": sorted(set(reasons)),
        "collector_lineage": _make_lineage(record, database_path, database_sha256),
    }


def _date_value(record: Mapping[str, Any]) -> str | None:
    value = record.get("published_at_utc") or record.get("observed_at_utc")
    return str(value) if value is not None else None


def sample_pilot(
    records: list[dict[str, Any]],
    *,
    database_path: Path,
    database_sha256: str,
    seed: int = DEFAULT_SEED,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return exactly 300 unique, semantically unclassified observations."""

    if len({str(record.get("observation_id")) for record in records}) != len(records):
        raise ValueError("duplicate observation_id in Collector input")
    if len(records) < PILOT_SIZE:
        raise ValueError(f"Collector input has only {len(records)} observations; need {PILOT_SIZE}")

    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[_exact_content_key(record)].append(record)

    selected: dict[str, list[str]] = defaultdict(list)
    general = _select(records, _BUCKET_TARGETS["GENERAL_RANDOM"], seed, "GENERAL_RANDOM")
    for record in general:
        selected[str(record["observation_id"])].append("GENERAL_RANDOM")

    buckets: list[tuple[str, list[dict[str, Any]]]] = [
        ("VERY_SHORT", [record for record in records if _text_length(record) <= 8]),
        ("MEDIUM_LENGTH", [record for record in records if 9 <= _text_length(record) <= 20]),
        ("LONGER_TEXT", [record for record in records if _text_length(record) > 20]),
        ("EXACT_CONTENT_REPEAT", [record for key, group in groups.items() if len(group) > 1 for record in group]),
    ]
    for bucket, candidates in buckets:
        for record in _select(candidates, _BUCKET_TARGETS[bucket], seed, bucket):
            selected[str(record["observation_id"])].append(bucket)

    for record in _select_metadata_extremes(records, _BUCKET_TARGETS["METADATA_EXTREME"], seed):
        selected[str(record["observation_id"])].append("METADATA_EXTREME")

    pattern_candidates = [record for record in records if any(_structural_features(record).values())]
    for record in _select(pattern_candidates, _BUCKET_TARGETS["STRUCTURAL_PATTERN"], seed, "STRUCTURAL_PATTERN"):
        selected[str(record["observation_id"])].append("STRUCTURAL_PATTERN")

    if len(selected) < PILOT_SIZE:
        for record in _ordered(records, seed, "GENERAL_RANDOM_SUPPLEMENT"):
            observation_id = str(record["observation_id"])
            if observation_id not in selected:
                selected[observation_id].append("GENERAL_RANDOM_SUPPLEMENT")
            if len(selected) == PILOT_SIZE:
                break
    if len(selected) != PILOT_SIZE:
        raise ValueError(f"sampling produced {len(selected)} unique observations, expected {PILOT_SIZE}")

    exact_counts = {key: len(group) for key, group in groups.items()}
    by_id = {str(record["observation_id"]): record for record in records}
    output = [
        _output_record(by_id[observation_id], reasons, exact_counts[_exact_content_key(by_id[observation_id])], database_path, database_sha256)
        for observation_id, reasons in selected.items()
    ]
    output.sort(key=lambda record: (str(record.get("source") or ""), str(record.get("source_item_id") or ""), int(record.get("observation_version") or 0), str(record["observation_id"])))

    metadata_fields = [
        field for field in ("author_id", "author_name", "read_count", "reply_count", "like_count", "forward_count")
        if records and field in records[0]
    ]
    lengths = Counter(
        "VERY_SHORT" if _text_length(record) <= 8 else "MEDIUM" if _text_length(record) <= 20 else "LONGER"
        for record in records
    )
    dates = sorted(value for value in (_date_value(record) for record in records) if value)
    profile = {
        "sampler_version": PILOT_SAMPLER_VERSION,
        "seed": seed,
        "source_db_fingerprint": database_sha256,
        "total_source_observations": len(records),
        "pilot_size": len(output),
        "date_min": dates[0] if dates else None,
        "date_max": dates[-1] if dates else None,
        "length_distribution": dict(lengths),
        "sampling_bucket_targets": dict(_BUCKET_TARGETS),
        "sampling_bucket_counts": dict(Counter(reason for record in output for reason in record["sampling_reasons"])),
        "exact_content_repeat_count": sum(record["exact_content_count"] > 1 for record in output),
        "exact_content_repeat_group_count": len({record["exact_content_key"] for record in output if record["exact_content_count"] > 1}),
        "available_metadata_fields": metadata_fields,
        "content_source_observed": sorted({
            str(record.get("source_metadata", {}).get("content_source"))
            for record in records
            if isinstance(record.get("source_metadata"), dict) and record.get("source_metadata", {}).get("content_source") is not None
        }),
        "quality_labels_present": False,
        "synthetic_observations_present": False,
    }
    return output, profile


def _write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    path.write_bytes(b"".join(canonical_json_bytes(record) + b"\n" for record in records))


def _write_csv(path: Path, records: list[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["sampling_reasons"] = json.dumps(row["sampling_reasons"], ensure_ascii=False, separators=(",", ":"))
            row["collector_lineage"] = json.dumps(row["collector_lineage"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            writer.writerow(row)


def run(database: str | Path, output_directory: str | Path, seed: int = DEFAULT_SEED) -> dict[str, Any]:
    database_path = Path(database).resolve()
    output_path = Path(output_directory)
    records = read_collector_records(database_path)
    fingerprint = _database_sha256(database_path)
    pilot, profile = sample_pilot(records, database_path=database_path, database_sha256=fingerprint, seed=seed)
    output_path.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_path / "pilot-300.jsonl", pilot)
    _write_csv(output_path / "pilot-300.csv", pilot)
    (output_path / "pilot-profile.json").write_bytes(canonical_json_bytes(profile) + b"\n")
    return profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create the ROUND-003 real-observation pilot dataset.")
    parser.add_argument("collector_db", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile = run(args.collector_db, args.output_directory, args.seed)
    except (CollectorContractError, ValueError) as exc:
        print(f"ROUND-003 pilot error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(profile, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
