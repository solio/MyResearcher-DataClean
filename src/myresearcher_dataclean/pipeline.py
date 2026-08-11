"""Minimal deterministic cleaning pipeline with explicit audit metadata."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .normalization import merge_rule_lists, normalize_text


CLEANING_VERSION = "minimal.v1"
CLEAN_SCHEMA_VERSION = "dataclean.clean.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(eq=True)
class CleaningResult:
    clean_records: list[dict[str, Any]]
    rejections: list[dict[str, Any]]
    report: dict[str, Any]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _valid_utc(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 27 or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return (
        parsed.tzinfo == timezone.utc
        and parsed.isoformat(timespec="microseconds").replace("+00:00", "Z") == value
    )


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validation_errors(record: Any) -> list[str]:
    if not isinstance(record, Mapping):
        return ["record must be an object"]
    errors: list[str] = []
    for name in (
        "observation_id",
        "source",
        "source_item_id",
        "url",
        "schema_version",
        "collector_version",
        "parser_version",
    ):
        if not _is_nonempty_string(record.get(name)):
            errors.append(f"{name} must be a non-empty string")
    version = record.get("observation_version")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        errors.append("observation_version must be a positive integer")
    storage_version = record.get("collector_storage_version")
    if storage_version is not None and storage_version not in {1, 2}:
        errors.append("collector_storage_version must be 1 or 2 when present")
    for name in ("observed_at_utc", "published_at_utc"):
        if not _valid_utc(record.get(name)):
            errors.append(f"{name} must be canonical UTC")
    for name in ("source_updated_at_utc", "display_time_utc"):
        value = record.get(name)
        if value is not None and not _valid_utc(value):
            errors.append(f"{name} must be null or canonical UTC")
    if record.get("title") is not None and not isinstance(record.get("title"), str):
        errors.append("title must be null or a string")
    if not isinstance(record.get("content"), str):
        errors.append("content must be a string")
    content_digest = record.get("content_sha256")
    if content_digest is not None:
        if not isinstance(content_digest, str) or not _SHA256.fullmatch(content_digest):
            errors.append("content_sha256 must be null or a lowercase SHA-256")
        elif isinstance(record.get("content"), str):
            actual_content_digest = hashlib.sha256(
                record["content"].encode("utf-8")
            ).hexdigest()
            if actual_content_digest != content_digest:
                errors.append("content_sha256 does not match content")
    if not isinstance(record.get("source_times_raw"), Mapping):
        errors.append("source_times_raw must be an object")
    if not isinstance(record.get("source_metadata"), Mapping):
        errors.append("source_metadata must be an object")
    fingerprint = record.get("fact_fingerprint")
    if not isinstance(fingerprint, str) or not _SHA256.fullmatch(fingerprint):
        errors.append("fact_fingerprint must be a lowercase SHA-256")
    evidence = record.get("raw_evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("raw_evidence must contain at least one lineage reference")
    else:
        for index, item in enumerate(evidence):
            if not isinstance(item, Mapping):
                errors.append(f"raw_evidence[{index}] must be an object")
                continue
            for name in (
                "evidence_id",
                "evidence_role",
                "run_id",
                "filesystem_path",
                "storage_version",
            ):
                if not _is_nonempty_string(item.get(name)):
                    errors.append(f"raw_evidence[{index}].{name} must be non-empty")
            digest = item.get("content_sha256")
            if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
                errors.append(
                    f"raw_evidence[{index}].content_sha256 must be a lowercase SHA-256"
                )
            byte_size = item.get("byte_size")
            if (
                isinstance(byte_size, bool)
                or not isinstance(byte_size, int)
                or byte_size < 0
            ):
                errors.append(
                    f"raw_evidence[{index}].byte_size must be a non-negative integer"
                )
    scopes = record.get("scopes")
    if not isinstance(scopes, list) or not scopes:
        errors.append("scopes must contain at least one Collector scope")
    return errors


def _available_lineage(record: Any) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        return {"observation_id": None, "raw_evidence": []}
    return {
        "observation_id": record.get("observation_id"),
        "source": record.get("source"),
        "source_item_id": record.get("source_item_id"),
        "observation_version": record.get("observation_version"),
        "raw_evidence": copy.deepcopy(record.get("raw_evidence", [])),
        "scopes": copy.deepcopy(record.get("scopes", [])),
    }


def _full_lineage(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "observation_id": record["observation_id"],
        "observation_version": record["observation_version"],
        "collector_storage_version": record.get("collector_storage_version"),
        "collector_schema_version": record["schema_version"],
        "collector_version": record["collector_version"],
        "parser_version": record["parser_version"],
        "fact_fingerprint": record["fact_fingerprint"],
        "drift_from_observation_id": record.get("drift_from_observation_id"),
        "raw_evidence": copy.deepcopy(record["raw_evidence"]),
        "scopes": copy.deepcopy(record["scopes"]),
    }


def _text_digest(title: Any, content: Any) -> str:
    return _sha256({"title": title, "content": content})


def _safe_text_digest(title: Any, content: Any) -> str | None:
    try:
        return _text_digest(title, content)
    except (TypeError, ValueError):
        return None


def _rejection(
    record: Any,
    reason: str,
    *,
    detail: str,
    rules: list[str] | None = None,
    input_digest: str | None = None,
    output_digest: str | None = None,
    duplicate_of: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "reason": reason,
        "detail": detail,
        "cleaning_version": CLEANING_VERSION,
        "rules_applied": rules or [],
        "input_text_sha256": input_digest,
        "output_text_sha256": output_digest,
        "lineage": _available_lineage(record),
    }
    if isinstance(record, Mapping):
        result["record_metadata"] = {
            "observed_at_utc": record.get("observed_at_utc"),
            "published_at_utc": record.get("published_at_utc"),
            "author_id": record.get("author_id"),
            "author_name": record.get("author_name"),
            "url": record.get("url"),
            "source_metadata": copy.deepcopy(record.get("source_metadata")),
        }
    if duplicate_of is not None:
        result["duplicate_of"] = duplicate_of
    return result


def _clean_record(
    record: Mapping[str, Any],
    *,
    title: str | None,
    content: str,
    rules: list[str],
    input_digest: str,
    output_digest: str,
    duplicate_key: str,
) -> dict[str, Any]:
    clean_id = _sha256(
        {
            "clean_schema_version": CLEAN_SCHEMA_VERSION,
            "cleaning_version": CLEANING_VERSION,
            "observation_id": record["observation_id"],
            "fact_fingerprint": record["fact_fingerprint"],
        }
    )
    return {
        "clean_schema_version": CLEAN_SCHEMA_VERSION,
        "clean_id": clean_id,
        "observation_id": record["observation_id"],
        "observation_version": record["observation_version"],
        "source": record["source"],
        "source_item_id": record["source_item_id"],
        "observed_at_utc": record["observed_at_utc"],
        "published_at_utc": record["published_at_utc"],
        "source_updated_at_utc": record.get("source_updated_at_utc"),
        "display_time_utc": record.get("display_time_utc"),
        "author_id": record.get("author_id"),
        "author_name": record.get("author_name"),
        "title": title,
        "content": content,
        "url": record["url"],
        "source_metadata": {
            "canonical_bar_code": record.get("canonical_bar_code"),
            "canonical_bar_name": record.get("canonical_bar_name"),
            "post_type": record.get("post_type"),
            "post_state": record.get("post_state"),
            "post_top_status": record.get("post_top_status"),
            "read_count": record.get("read_count"),
            "reply_count": record.get("reply_count"),
            "like_count": record.get("like_count"),
            "forward_count": record.get("forward_count"),
            "source_times_raw": copy.deepcopy(record["source_times_raw"]),
            "collector": copy.deepcopy(record["source_metadata"]),
        },
        "lineage": _full_lineage(record),
        "cleaning": {
            "version": CLEANING_VERSION,
            "rules_applied": rules,
            "input_text_sha256": input_digest,
            "output_text_sha256": output_digest,
            "exact_duplicate_key": duplicate_key,
        },
    }


def clean_records(records: Iterable[Mapping[str, Any]]) -> CleaningResult:
    """Clean one deterministic ordered batch and retain all rejection reasons."""

    inputs = list(records)
    clean: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    duplicate_first: dict[str, str] = {}
    unchanged = 0
    modified = 0

    for record in inputs:
        errors = _validation_errors(record)
        if errors:
            title = record.get("title") if isinstance(record, Mapping) else None
            content = record.get("content") if isinstance(record, Mapping) else None
            rejected.append(
                _rejection(
                    record,
                    "INVALID_RECORD",
                    detail="; ".join(errors),
                    input_digest=_safe_text_digest(title, content),
                )
            )
            continue

        title_value = record.get("title")
        normalized_title = (
            normalize_text(title_value) if title_value is not None else None
        )
        normalized_content = normalize_text(record["content"])
        title = normalized_title.text if normalized_title is not None else None
        content = normalized_content.text
        rules = merge_rule_lists(
            normalized_title.rules_applied if normalized_title is not None else (),
            normalized_content.rules_applied,
        )
        input_digest = _text_digest(title_value, record["content"])
        output_digest = _text_digest(title, content)

        if not (title or content):
            rejected.append(
                _rejection(
                    record,
                    "EMPTY_CONTENT",
                    detail="title and content are empty after minimal normalization",
                    rules=rules,
                    input_digest=input_digest,
                    output_digest=output_digest,
                )
            )
            continue

        duplicate_key = output_digest
        if duplicate_key in duplicate_first:
            rejected.append(
                _rejection(
                    record,
                    "EXACT_DUPLICATE",
                    detail="normalized title and content exactly match an earlier batch record",
                    rules=rules,
                    input_digest=input_digest,
                    output_digest=output_digest,
                    duplicate_of=duplicate_first[duplicate_key],
                )
            )
            continue

        output = _clean_record(
            record,
            title=title,
            content=content,
            rules=rules,
            input_digest=input_digest,
            output_digest=output_digest,
            duplicate_key=duplicate_key,
        )
        duplicate_first[duplicate_key] = output["clean_id"]
        clean.append(output)
        if rules:
            modified += 1
        else:
            unchanged += 1

    reasons = Counter(item["reason"] for item in rejected)
    report = {
        "cleaning_version": CLEANING_VERSION,
        "clean_schema_version": CLEAN_SCHEMA_VERSION,
        "input_count": len(inputs),
        "cleaned_count": len(clean),
        "unchanged_count": unchanged,
        "modified_count": modified,
        "rejected_count": len(rejected),
        "duplicate_count": reasons.get("EXACT_DUPLICATE", 0),
        "reason_distribution": dict(sorted(reasons.items())),
    }
    return CleaningResult(clean, rejected, report)
