"""Deterministic ROUND-002 dataset and experiment infrastructure.

This module deliberately contains no label policy, prompt, financial-text
heuristic, network access, or mutable artifact store.  Its public functions
create JSON-serializable, content-addressed values which callers may persist.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import random
from typing import Any, Iterable, Mapping


DISPOSITIONS = ("KEEP", "EXCLUDE", "REVIEW")
REASON_TAGS = (
    "ADVERTISEMENT",
    "BOT_TEMPLATE",
    "LOW_INFORMATION",
    "OFF_TOPIC",
    "MARKET_QUOTE_ONLY",
    "REPOST",
    "BROKEN_CONTENT",
    "OTHER",
)
_ANNOTATOR_TYPES = {"HUMAN", "TEACHER_MODEL"}
_STATES = {"candidate", "reviewed", "golden"}
_PREDICTION_FORBIDDEN = {
    "prediction_id",
    "predicted_disposition",
    "model_output",
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _content_id(value: Mapping[str, Any], own_id: str) -> str:
    payload = {key: deepcopy(item) for key, item in value.items() if key != own_id}
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


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


def _require_utc(value: Any, field: str) -> None:
    _require(_valid_utc(value), f"{field} must be canonical UTC")


def _require_disposition(value: Any, field: str = "disposition") -> None:
    _require(value in DISPOSITIONS, f"invalid {field}")


def _validate_reason_tags(value: Any) -> list[str]:
    _require(isinstance(value, list), "reason_tags must be a list")
    _require(all(item in REASON_TAGS for item in value), "invalid reason tag")
    _require(value == sorted(set(value)), "reason tags must be sorted and unique")
    return list(value)


def _clean_from_sample(sample: Mapping[str, Any]) -> Mapping[str, Any]:
    _require(
        sample.get("sample_record_schema_version") == "dataclean.sample-record.v1",
        "invalid sample record schema",
    )
    _require(_nonempty(sample.get("sample_record_id")), "missing sample_record_id")
    clean = sample.get("clean_record")
    _require(isinstance(clean, Mapping), "sample record missing clean_record")
    _validate_clean(clean)
    expected = _content_id(sample, "sample_record_id")
    _require(sample["sample_record_id"] == expected, "sample_record_id content hash mismatch")
    return clean


def _validate_clean(clean: Mapping[str, Any]) -> None:
    _require(
        clean.get("clean_schema_version") == "dataclean.clean.v1",
        "invalid CLEAN schema",
    )
    for field in ("clean_id", "observation_id", "source", "source_item_id", "content"):
        _require(_nonempty(clean.get(field)), f"missing CLEAN {field}")
    _require_utc(clean.get("observed_at_utc"), "observed_at_utc")
    _require_utc(clean.get("published_at_utc"), "published_at_utc")
    cleaning = clean.get("cleaning")
    _require(isinstance(cleaning, Mapping), "missing CLEAN cleaning metadata")
    _require(_nonempty(cleaning.get("version")), "missing CLEANing version")
    _require(_nonempty(cleaning.get("exact_content_key")), "missing exact_content_key")
    lineage = clean.get("lineage")
    _require(isinstance(lineage, Mapping), "missing CLEAN lineage")
    _require(_nonempty(lineage.get("fact_fingerprint")), "missing fact_fingerprint")
    _require(isinstance(lineage.get("raw_evidence"), list) and lineage["raw_evidence"], "missing raw evidence")
    _require(isinstance(lineage.get("scopes"), list) and lineage["scopes"], "missing scopes")
    _require(lineage.get("observation_id") == clean.get("observation_id"), "lineage observation mismatch")


def _cleaning_version(clean: Mapping[str, Any]) -> str:
    return str(clean["cleaning"]["version"])


def _sample_record(clean: Mapping[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "sample_record_schema_version": "dataclean.sample-record.v1",
        "clean_record": deepcopy(dict(clean)),
    }
    record["sample_record_id"] = _content_id(record, "sample_record_id")
    return record


def _sample_binding(sample: Mapping[str, Any]) -> dict[str, Any]:
    clean = _clean_from_sample(sample)
    lineage = _source_lineage(clean)
    return {
        "sample_record_id": sample["sample_record_id"],
        "observation_id": clean["observation_id"],
        "clean_id": clean["clean_id"],
        "exact_content_key": clean["cleaning"]["exact_content_key"],
        "source_record_lineage_sha256": hashlib.sha256(
            _canonical_bytes(lineage)
        ).hexdigest(),
    }


def sample_clean_records(
    clean_records: Iterable[Mapping[str, Any]],
    *,
    input_clean_artifact_id: str,
    seed: int,
    requested_count: int,
    sources: Iterable[str] | None = None,
    observed_at_start: str | None = None,
    observed_at_end: str | None = None,
    minimum_text_length: int | None = None,
    grouping_mode: str = "record",
) -> dict[str, Any]:
    """Filter and deterministically sample full immutable CLEAN snapshots."""

    _require(_nonempty(input_clean_artifact_id), "missing input_clean_artifact_id")
    _require(isinstance(seed, int) and not isinstance(seed, bool), "seed must be an integer")
    _require(isinstance(requested_count, int) and requested_count >= 0, "invalid requested_count")
    _require(grouping_mode in {"record", "exact_content_group"}, "invalid grouping_mode")
    if observed_at_start is not None:
        _require_utc(observed_at_start, "observed_at_start")
    if observed_at_end is not None:
        _require_utc(observed_at_end, "observed_at_end")
    _require(
        observed_at_start is None or observed_at_end is None or observed_at_start <= observed_at_end,
        "invalid observed_at range",
    )
    _require(
        minimum_text_length is None
        or (isinstance(minimum_text_length, int) and minimum_text_length >= 0),
        "invalid minimum_text_length",
    )
    source_set = None if sources is None else set(sources)
    _require(source_set is None or all(_nonempty(item) for item in source_set), "invalid source filter")

    all_clean_records: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []
    seen_observations: set[str] = set()
    for incoming in clean_records:
        _require(isinstance(incoming, Mapping), "CLEAN record must be an object")
        clean = deepcopy(dict(incoming))
        _validate_clean(clean)
        observation_id = clean["observation_id"]
        _require(observation_id not in seen_observations, "duplicate observation_id")
        seen_observations.add(observation_id)
        all_clean_records.append(clean)
        if source_set is not None and clean["source"] not in source_set:
            continue
        observed = clean["observed_at_utc"]
        if observed_at_start is not None and observed < observed_at_start:
            continue
        if observed_at_end is not None and observed > observed_at_end:
            continue
        if minimum_text_length is not None and len(clean["content"]) < minimum_text_length:
            continue
        eligible.append(clean)

    all_clean_records.sort(key=lambda item: item["observation_id"])
    input_schema_version = "dataclean.clean.v1"
    input_cleaning_version = "minimal.v1"
    if all_clean_records:
        input_schema_version = str(all_clean_records[0]["clean_schema_version"])
        input_cleaning_version = _cleaning_version(all_clean_records[0])
        _require(
            all(item["clean_schema_version"] == input_schema_version for item in all_clean_records),
            "CLEAN schema version mismatch",
        )
        _require(
            all(_cleaning_version(item) == input_cleaning_version for item in all_clean_records),
            "CLEANing version mismatch",
        )
    eligible.sort(key=lambda item: item["observation_id"])
    chooser = random.Random(seed)
    if grouping_mode == "record":
        selected = chooser.sample(eligible, min(requested_count, len(eligible)))
    else:
        groups: dict[str, list[dict[str, Any]]] = {}
        for clean in eligible:
            groups.setdefault(clean["cleaning"]["exact_content_key"], []).append(clean)
        ordered_groups = sorted(groups.items())
        selected_keys = {
            key for key, _ in chooser.sample(ordered_groups, min(requested_count, len(ordered_groups)))
        }
        selected = [clean for clean in eligible if clean["cleaning"]["exact_content_key"] in selected_keys]
    selected.sort(key=lambda item: item["observation_id"])
    records = [_sample_record(clean) for clean in selected]
    bindings = sorted(
        (_sample_binding(record) for record in records),
        key=lambda item: item["observation_id"],
    )
    config = {
        "sources": None if source_set is None else sorted(source_set),
        "observed_at_start": observed_at_start,
        "observed_at_end": observed_at_end,
        "minimum_text_length": minimum_text_length,
        "grouping_mode": grouping_mode,
        "seed": seed,
        "requested_count": requested_count,
    }
    manifest: dict[str, Any] = {
        "sample_manifest_schema_version": "dataclean.sample-manifest.v1",
        "input_clean_artifact_id": input_clean_artifact_id,
        "input_clean_schema_version": input_schema_version,
        "input_cleaning_version": input_cleaning_version,
        "input_clean_snapshot_sha256": hashlib.sha256(
            _canonical_bytes(all_clean_records)
        ).hexdigest(),
        "sampler_config": config,
        "sample_record_ids": [item["sample_record_id"] for item in records],
        "sample_bindings": bindings,
        "record_count": len(records),
    }
    manifest["sample_manifest_id"] = _content_id(manifest, "sample_manifest_id")
    return {"manifest": manifest, "records": records}


def _source_lineage(clean: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "clean_id": clean["clean_id"],
        "clean_schema_version": clean["clean_schema_version"],
        "cleaning_version": clean.get("cleaning", {}).get("version"),
        "observation_id": clean["observation_id"],
        "source": clean["source"],
        "source_item_id": clean["source_item_id"],
        "observation_version": clean.get("observation_version"),
        "exact_content_key": clean["cleaning"]["exact_content_key"],
        "lineage": deepcopy(dict(clean["lineage"])),
    }


def _validate_golden_review(value: Any) -> None:
    _require(isinstance(value, Mapping), "golden_review is required")
    _require(value.get("reviewer_type") == "HUMAN", "golden_review reviewer_type must be HUMAN")
    _require(_nonempty(value.get("reviewer_id")), "golden_review reviewer_id is required")
    _require_utc(value.get("reviewed_at_utc"), "golden_review reviewed_at_utc")
    _require(_nonempty(value.get("review_rule_version")), "golden_review review_rule_version is required")


def create_annotation_record(
    sample_record: Mapping[str, Any],
    *,
    dataset_state: str,
    disposition: str,
    reason_tags: list[str],
    annotator_type: str,
    annotator_id: str,
    annotation_version: str,
    annotated_at_utc: str,
    supersedes_annotation_id: str | None = None,
    golden_review: Mapping[str, Any] | None = None,
    confidence: float | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Create one immutable human or teacher annotation record."""

    clean = _clean_from_sample(sample_record)
    _require(dataset_state in _STATES, "invalid dataset_state")
    _require(annotator_type in _ANNOTATOR_TYPES, "invalid annotator_type")
    _require_disposition(disposition)
    _validate_reason_tags(reason_tags)
    _require(_nonempty(annotator_id), "missing annotator_id")
    _require(_nonempty(annotation_version), "missing annotation_version")
    _require_utc(annotated_at_utc, "annotated_at_utc")
    _require(
        confidence is None
        or (
            isinstance(confidence, (int, float))
            and not isinstance(confidence, bool)
            and math.isfinite(confidence)
            and 0 <= confidence <= 1
        ),
        "invalid confidence",
    )
    _require(note is None or isinstance(note, str), "invalid note")
    if dataset_state == "candidate":
        _require(golden_review is None, "candidate annotation cannot have golden_review")
    else:
        _require(annotator_type == "HUMAN", f"TEACHER_MODEL cannot be {dataset_state}")
        _require(_nonempty(supersedes_annotation_id), f"{dataset_state} requires supersedes_annotation_id")
    if dataset_state == "golden":
        _validate_golden_review(golden_review)
    else:
        _require(golden_review is None, "golden_review only allowed for golden")
    annotation: dict[str, Any] = {
        "annotation_schema_version": "dataclean.annotation-record.v1",
        "sample_record_id": sample_record["sample_record_id"],
        "observation_id": clean["observation_id"],
        "exact_content_key": clean["cleaning"]["exact_content_key"],
        "dataset_state": dataset_state,
        "disposition": disposition,
        "reason_tags": list(reason_tags),
        "annotator_type": annotator_type,
        "annotator_id": annotator_id,
        "annotation_version": annotation_version,
        "annotated_at_utc": annotated_at_utc,
        "confidence": confidence,
        "note": note,
        "supersedes_annotation_id": supersedes_annotation_id,
        "source_record_lineage": _source_lineage(clean),
        "golden_review": deepcopy(dict(golden_review)) if golden_review is not None else None,
    }
    annotation["annotation_id"] = _content_id(annotation, "annotation_id")
    return annotation


def _validate_annotation(annotation: Mapping[str, Any]) -> None:
    _require(
        annotation.get("annotation_schema_version") == "dataclean.annotation-record.v1",
        "invalid annotation schema",
    )
    _require(not (_PREDICTION_FORBIDDEN & set(annotation)), "prediction fields cannot mix into annotation")
    state = annotation.get("dataset_state")
    actor = annotation.get("annotator_type")
    _require(state in _STATES, "invalid annotation state")
    _require(actor in _ANNOTATOR_TYPES, "invalid annotator_type")
    _require_disposition(annotation.get("disposition"))
    _validate_reason_tags(annotation.get("reason_tags"))
    for field in ("annotation_id", "sample_record_id", "observation_id", "exact_content_key", "annotator_id", "annotation_version"):
        _require(_nonempty(annotation.get(field)), f"missing annotation {field}")
    _require_utc(annotation.get("annotated_at_utc"), "annotated_at_utc")
    confidence = annotation.get("confidence")
    _require(confidence is None or (isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and math.isfinite(confidence) and 0 <= confidence <= 1), "invalid confidence")
    source = annotation.get("source_record_lineage")
    _require(isinstance(source, Mapping), "missing annotation source_record_lineage")
    _require(source.get("observation_id") == annotation.get("observation_id"), "annotation lineage observation mismatch")
    _require(source.get("exact_content_key") == annotation.get("exact_content_key"), "annotation lineage content mismatch")
    nested = source.get("lineage")
    _require(isinstance(nested, Mapping) and _nonempty(nested.get("fact_fingerprint")), "missing annotation lineage fingerprint")
    if state == "candidate":
        _require(annotation.get("golden_review") is None, "candidate cannot have golden_review")
    else:
        _require(actor == "HUMAN", f"TEACHER_MODEL cannot be {state}")
        _require(_nonempty(annotation.get("supersedes_annotation_id")), f"{state} requires supersedes_annotation_id")
    if state == "golden":
        _validate_golden_review(annotation.get("golden_review"))
    else:
        _require(annotation.get("golden_review") is None, "golden_review only allowed for golden")
    _require(annotation.get("annotation_id") == _content_id(annotation, "annotation_id"), "annotation_id content hash mismatch")


def _validate_sample_manifest(manifest: Mapping[str, Any]) -> None:
    _require(manifest.get("sample_manifest_schema_version") == "dataclean.sample-manifest.v1", "invalid sample manifest schema")
    _require(_nonempty(manifest.get("sample_manifest_id")), "missing sample_manifest_id")
    _require(
        manifest.get("input_clean_schema_version") == "dataclean.clean.v1",
        "invalid input CLEAN schema version",
    )
    _require(_nonempty(manifest.get("input_cleaning_version")), "missing input CLEANing version")
    snapshot_digest = manifest.get("input_clean_snapshot_sha256")
    _require(
        isinstance(snapshot_digest, str) and len(snapshot_digest) == 64,
        "missing input CLEAN snapshot digest",
    )
    bindings = manifest.get("sample_bindings")
    _require(isinstance(bindings, list), "missing sample manifest bindings")
    _require(
        bindings == sorted(bindings, key=lambda item: item.get("observation_id", "")),
        "sample manifest bindings must be canonical order",
    )
    _require(
        manifest.get("sample_record_ids") == [item.get("sample_record_id") for item in bindings],
        "sample manifest binding IDs mismatch",
    )
    _require(manifest["sample_manifest_id"] == _content_id(manifest, "sample_manifest_id"), "sample manifest content hash mismatch")


def _validate_annotation_binding(
    annotation: Mapping[str, Any], binding: Mapping[str, Any]
) -> None:
    for field in ("sample_record_id", "observation_id", "exact_content_key"):
        _require(
            annotation.get(field) == binding.get(field),
            "annotation sample manifest binding mismatch",
        )
    source = annotation.get("source_record_lineage")
    _require(
        isinstance(source, Mapping)
        and hashlib.sha256(_canonical_bytes(source)).hexdigest()
        == binding.get("source_record_lineage_sha256"),
        "annotation source lineage mismatch",
    )


def _validate_prior_transition(
    annotation: Mapping[str, Any], prior_annotations: Mapping[str, Mapping[str, Any]]
) -> None:
    if annotation["dataset_state"] == "candidate":
        return
    prior_id = annotation["supersedes_annotation_id"]
    _require(prior_id in prior_annotations, "supersedes annotation is missing")
    prior = prior_annotations[prior_id]
    _require(
        prior["dataset_state"] in {"candidate", "reviewed"},
        "supersedes annotation has invalid state",
    )
    _require(
        prior["observation_id"] == annotation["observation_id"]
        and prior["sample_record_id"] == annotation["sample_record_id"],
        "supersedes annotation identity mismatch",
    )


def build_annotation_dataset(
    sample_manifest: Mapping[str, Any],
    annotations: Iterable[Mapping[str, Any]],
    *,
    prior_annotations: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    _validate_sample_manifest(sample_manifest)
    bindings = {
        item["sample_record_id"]: item for item in sample_manifest["sample_bindings"]
    }
    _require(
        len(bindings) == len(sample_manifest["sample_bindings"]),
        "duplicate sample manifest binding",
    )
    priors: dict[str, Mapping[str, Any]] = {}
    for prior in prior_annotations:
        _validate_annotation(prior)
        prior_id = prior["annotation_id"]
        _require(prior_id not in priors, "duplicate prior annotation_id")
        priors[prior_id] = prior
    records = [deepcopy(dict(item)) for item in annotations]
    for record in records:
        _validate_annotation(record)
        binding = bindings.get(record["sample_record_id"])
        _require(binding is not None, "annotation sample manifest binding is missing")
        _validate_annotation_binding(record, binding)
        _validate_prior_transition(record, priors)
    observation_ids = [item["observation_id"] for item in records]
    _require(len(observation_ids) == len(set(observation_ids)), "duplicate annotation observation_id")
    records.sort(key=lambda item: (item["observation_id"], item["annotation_id"]))
    states = {item["dataset_state"] for item in records}
    _require(len(states) <= 1, "mixed dataset states")
    dataset_state = next(iter(states), "candidate")
    manifest: dict[str, Any] = {
        "annotation_dataset_schema_version": "dataclean.annotation-dataset.v1",
        "sample_manifest_id": sample_manifest["sample_manifest_id"],
        "sample_bindings": deepcopy(sample_manifest["sample_bindings"]),
        "annotation_ids": [item["annotation_id"] for item in records],
        "record_count": len(records),
        "dataset_state": dataset_state,
    }
    manifest["dataset_content_sha256"] = hashlib.sha256(_canonical_bytes(records)).hexdigest()
    manifest["dataset_version"] = _content_id(manifest, "dataset_version")
    return {"manifest": manifest, "annotations": records}


def export_teacher_candidates(
    sample_manifest: Mapping[str, Any],
    sample_records: Iterable[Mapping[str, Any]],
    *,
    request_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_sample_manifest(sample_manifest)
    _require(isinstance(request_metadata, Mapping), "request_metadata must be an object")
    records = [deepcopy(dict(item)) for item in sample_records]
    for item in records:
        _clean_from_sample(item)
    records.sort(key=lambda item: item["sample_record_id"])
    exported: dict[str, Any] = {
        "teacher_export_schema_version": "dataclean.teacher-export.v1",
        "sample_manifest_id": sample_manifest["sample_manifest_id"],
        "sample_records": records,
        "sample_record_ids": [item["sample_record_id"] for item in records],
        "request_metadata": deepcopy(dict(request_metadata)),
    }
    exported["teacher_export_id"] = _content_id(exported, "teacher_export_id")
    return exported


def import_teacher_candidates(
    teacher_export: Mapping[str, Any],
    teacher_import: Mapping[str, Any],
    *,
    annotation_version: str,
    annotated_at_utc: str,
) -> list[dict[str, Any]]:
    _require(teacher_export.get("teacher_export_schema_version") == "dataclean.teacher-export.v1", "invalid teacher export schema")
    _require(teacher_export.get("teacher_export_id") == _content_id(teacher_export, "teacher_export_id"), "teacher export content hash mismatch")
    _require(teacher_import.get("teacher_import_schema_version") == "dataclean.teacher-import.v1", "invalid teacher import schema")
    _require(
        teacher_import.get("teacher_import_id") == _content_id(teacher_import, "teacher_import_id"),
        "teacher import content hash mismatch",
    )
    _require(
        teacher_import.get("teacher_export_id") == teacher_export.get("teacher_export_id"),
        "teacher import source mismatch",
    )
    _require(_nonempty(teacher_import.get("teacher_model_id")), "missing teacher_model_id")
    revision = teacher_import.get("teacher_model_revision")
    _require(revision is None or _nonempty(revision), "invalid teacher_model_revision")
    response_items = teacher_import.get("response_items")
    _require(isinstance(response_items, list), "response_items must be a list")
    by_sample = {item["sample_record_id"]: item for item in teacher_export.get("sample_records", [])}
    _require(len(by_sample) == len(teacher_export.get("sample_records", [])), "duplicate teacher export sample")
    seen: set[str] = set()
    annotations: list[dict[str, Any]] = []
    for response in response_items:
        _require(isinstance(response, Mapping), "teacher response item must be an object")
        record_id = response.get("sample_record_id")
        _require(record_id in by_sample and record_id not in seen, "teacher response source mismatch or duplicate")
        seen.add(record_id)
        sample = by_sample[record_id]
        clean = _clean_from_sample(sample)
        _require(response.get("observation_id") == clean["observation_id"], "teacher response observation mismatch")
        annotations.append(
            create_annotation_record(
                sample,
                dataset_state="candidate",
                disposition=response.get("disposition"),
                reason_tags=response.get("reason_tags"),
                annotator_type="TEACHER_MODEL",
                annotator_id=teacher_import["teacher_model_id"],
                annotation_version=annotation_version,
                annotated_at_utc=annotated_at_utc,
            )
        )
    return sorted(annotations, key=lambda item: (item["observation_id"], item["annotation_id"]))


def _dataset_maps(
    dataset: Mapping[str, Any], sample_records: Iterable[Mapping[str, Any]]
) -> tuple[Mapping[str, Any], dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    manifest = dataset.get("manifest")
    annotations = dataset.get("annotations")
    _require(isinstance(manifest, Mapping) and isinstance(annotations, list), "invalid dataset")
    _require(manifest.get("annotation_dataset_schema_version") == "dataclean.annotation-dataset.v1", "invalid dataset manifest schema")
    _require(manifest.get("dataset_version") == _content_id(manifest, "dataset_version"), "dataset version content hash mismatch")
    ordered_annotations = sorted(
        annotations, key=lambda item: (item.get("observation_id", ""), item.get("annotation_id", ""))
    )
    _require(annotations == ordered_annotations, "dataset annotations must be canonical order")
    _require(manifest.get("record_count") == len(annotations), "dataset record count mismatch")
    _require(
        manifest.get("dataset_content_sha256") == hashlib.sha256(_canonical_bytes(annotations)).hexdigest(),
        "dataset content hash mismatch",
    )
    states = {item.get("dataset_state") for item in annotations}
    _require(len(states) <= 1, "mixed dataset states")
    _require(manifest.get("dataset_state") == next(iter(states), "candidate"), "dataset state mismatch")
    _require(
        manifest.get("annotation_ids") == [item.get("annotation_id") for item in annotations],
        "dataset annotation ordering mismatch",
    )
    bindings_value = manifest.get("sample_bindings")
    _require(isinstance(bindings_value, list), "dataset sample bindings missing")
    bindings = {item.get("sample_record_id"): item for item in bindings_value}
    _require(len(bindings) == len(bindings_value), "duplicate dataset sample binding")
    samples: dict[str, Mapping[str, Any]] = {}
    for sample in sample_records:
        clean = _clean_from_sample(sample)
        binding = bindings.get(sample["sample_record_id"])
        _require(binding is not None, "sample is not bound to dataset manifest")
        expected_binding = _sample_binding(sample)
        _require(binding == expected_binding, "sample manifest binding mismatch")
        _require(clean["observation_id"] not in samples, "duplicate sample observation_id")
        samples[clean["observation_id"]] = sample
    by_observation: dict[str, Mapping[str, Any]] = {}
    for annotation in annotations:
        _validate_annotation(annotation)
        observation_id = annotation["observation_id"]
        _require(observation_id not in by_observation, "duplicate annotation observation_id")
        _require(observation_id in samples, "annotation sample is missing")
        sample = samples[observation_id]
        clean = sample["clean_record"]
        _require(annotation["sample_record_id"] == sample["sample_record_id"], "annotation sample mismatch")
        _require(annotation["exact_content_key"] == clean["cleaning"]["exact_content_key"], "annotation content key mismatch")
        _validate_annotation_binding(annotation, bindings[annotation["sample_record_id"]])
        _require(
            annotation["source_record_lineage"] == _source_lineage(clean),
            "annotation source lineage mismatch",
        )
        by_observation[observation_id] = annotation
    return manifest, by_observation, samples


def _split_assignments(
    annotations: Mapping[str, Mapping[str, Any]],
    samples: Mapping[str, Mapping[str, Any]],
    *,
    strategy: str,
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    _require(strategy in {"random_stratified", "time_holdout", "source_holdout"}, "invalid split strategy")
    _require(annotations and all(item["dataset_state"] == "golden" for item in annotations.values()), "split requires golden dataset")
    groups: dict[str, list[tuple[str, Mapping[str, Any], Mapping[str, Any]]]] = {}
    for observation_id, annotation in annotations.items():
        clean = samples[observation_id]["clean_record"]
        groups.setdefault(annotation["exact_content_key"], []).append((observation_id, annotation, clean))

    group_split: dict[str, str] = {}
    if strategy == "random_stratified":
        _require(set(config) == {"seed", "test_fraction"}, "invalid random_stratified config")
        seed = config.get("seed")
        test_fraction = config.get("test_fraction")
        _require(isinstance(seed, int) and not isinstance(seed, bool), "random_stratified requires seed")
        _require(isinstance(test_fraction, (float, int)) and not isinstance(test_fraction, bool) and 0 < test_fraction < 1, "random_stratified requires test_fraction")
        for members in groups.values():
            labels = {item[1]["disposition"] for item in members}
            _require(len(labels) == 1, "SPLIT_GROUP_LABEL_CONFLICT")
        groups_by_label: dict[str, list[str]] = {}
        for key, members in groups.items():
            label = members[0][1]["disposition"]
            groups_by_label.setdefault(label, []).append(key)
        chooser = random.Random(seed)
        singleton_groups: list[str] = []
        for label in DISPOSITIONS:
            keys = sorted(groups_by_label.get(label, []))
            if len(keys) < 2:
                singleton_groups.extend(keys)
                continue
            test_count = min(
                len(keys) - 1,
                max(1, math.floor(len(keys) * float(test_fraction))),
            )
            test_groups = set(chooser.sample(keys, test_count))
            group_split.update(
                {key: ("test" if key in test_groups else "train") for key in keys}
            )
        if singleton_groups:
            test_count = min(
                len(singleton_groups) - 1,
                max(1, math.floor(len(singleton_groups) * float(test_fraction))),
            ) if len(singleton_groups) > 1 else 0
            singleton_test = set(chooser.sample(sorted(singleton_groups), test_count))
            group_split.update(
                {
                    key: ("test" if key in singleton_test else "train")
                    for key in singleton_groups
                }
            )
    elif strategy == "time_holdout":
        _require(set(config) == {"cutoff_utc"}, "invalid time_holdout config")
        cutoff_utc = config.get("cutoff_utc")
        _require_utc(cutoff_utc, "time_holdout cutoff_utc")
        for key, members in groups.items():
            sides = {"train" if item[2]["observed_at_utc"] < cutoff_utc else "test" for item in members}
            _require(len(sides) == 1, "SPLIT_GROUP_BOUNDARY_CONFLICT")
            group_split[key] = sides.pop()
    else:
        _require(set(config) == {"held_out_sources"}, "invalid source_holdout config")
        held_value = config.get("held_out_sources")
        _require(isinstance(held_value, list), "source_holdout requires held_out_sources")
        held = list(held_value)
        _require(held and held == sorted(set(held)) and all(_nonempty(item) for item in held), "source_holdout held_out_sources must be sorted and non-empty")
        held_set = set(held)
        for key, members in groups.items():
            sides = {"test" if item[2]["source"] in held_set else "train" for item in members}
            _require(len(sides) == 1, "SPLIT_GROUP_BOUNDARY_CONFLICT")
            group_split[key] = sides.pop()
    assignments = [
        {
            "observation_id": observation_id,
            "annotation_id": annotation["annotation_id"],
            "exact_content_key": key,
            "split": group_split[key],
        }
        for key, members in groups.items()
        for observation_id, annotation, _ in members
    ]
    assignments.sort(key=lambda item: (item["exact_content_key"], item["observation_id"]))
    return assignments


def create_split_manifest(
    dataset: Mapping[str, Any],
    sample_records: Iterable[Mapping[str, Any]],
    *,
    strategy: str,
    seed: int | None = None,
    test_fraction: float | None = None,
    cutoff_utc: str | None = None,
    held_out_sources: Iterable[str] | None = None,
) -> dict[str, Any]:
    manifest, annotations, samples = _dataset_maps(dataset, sample_records)
    if strategy == "random_stratified":
        config: dict[str, Any] = {"seed": seed, "test_fraction": test_fraction}
    elif strategy == "time_holdout":
        config = {"cutoff_utc": cutoff_utc}
    elif strategy == "source_holdout":
        config = {"held_out_sources": None if held_out_sources is None else list(held_out_sources)}
    else:
        raise ValueError("invalid split strategy")
    assignments = _split_assignments(
        annotations, samples, strategy=strategy, config=config
    )
    split: dict[str, Any] = {
        "split_manifest_schema_version": "dataclean.split-manifest.v1",
        "dataset_version": manifest["dataset_version"],
        "dataset_content_sha256": manifest["dataset_content_sha256"],
        "strategy": strategy,
        "config": config,
        "assignments": assignments,
    }
    split["split_manifest_id"] = _content_id(split, "split_manifest_id")
    validate_split_manifest(split, dataset, samples.values())
    return split


def validate_split_manifest(
    split_manifest: Mapping[str, Any], dataset: Mapping[str, Any], sample_records: Iterable[Mapping[str, Any]]
) -> None:
    manifest, annotations, samples = _dataset_maps(dataset, sample_records)
    _require(split_manifest.get("split_manifest_schema_version") == "dataclean.split-manifest.v1", "invalid split manifest schema")
    _require(split_manifest.get("dataset_version") == manifest["dataset_version"], "split dataset version mismatch")
    _require(split_manifest.get("dataset_content_sha256") == manifest["dataset_content_sha256"], "split dataset hash mismatch")
    assignments = split_manifest.get("assignments")
    _require(isinstance(assignments, list), "split assignments must be a list")
    _require(assignments == sorted(assignments, key=lambda item: (item.get("exact_content_key"), item.get("observation_id"))), "split assignments must be canonical order")
    seen: set[str] = set()
    group_splits: dict[str, str] = {}
    for item in assignments:
        _require(isinstance(item, Mapping), "invalid split assignment")
        observation_id = item.get("observation_id")
        _require(observation_id in annotations and observation_id not in seen, "split duplicate or unknown observation")
        seen.add(observation_id)
        annotation = annotations[observation_id]
        _require(item.get("annotation_id") == annotation["annotation_id"], "split annotation mismatch")
        _require(item.get("exact_content_key") == annotation["exact_content_key"], "split content key mismatch")
        _require(item.get("split") in {"train", "test"}, "invalid split name")
        existing = group_splits.setdefault(item["exact_content_key"], item["split"])
        _require(existing == item["split"], "leakage: exact-content group crosses split")
    _require(seen == set(annotations), "split missing observation")
    _require(split_manifest.get("split_manifest_id") == _content_id(split_manifest, "split_manifest_id"), "split manifest content hash mismatch")
    expected = _split_assignments(
        annotations,
        samples,
        strategy=split_manifest.get("strategy"),
        config=split_manifest.get("config") if isinstance(split_manifest.get("config"), Mapping) else {},
    )
    _require(assignments == expected, "split strategy replay mismatch")


def compute_disposition_metrics(
    golden_annotations: Iterable[Mapping[str, Any]], predictions: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    golden_items = list(golden_annotations)
    prediction_items = list(predictions)
    golden_ids = [item.get("observation_id") for item in golden_items]
    prediction_ids = [item.get("observation_id") for item in prediction_items]
    _require(
        len(golden_ids) == len(set(golden_ids)),
        "duplicate golden observation_id",
    )
    _require(
        len(prediction_ids) == len(set(prediction_ids)),
        "duplicate prediction observation_id",
    )
    for item in golden_items:
        if item.get("annotation_schema_version") is not None:
            _validate_annotation(item)
            _require(item.get("dataset_state") == "golden", "metrics requires golden annotations")
    for item in prediction_items:
        if item.get("prediction_schema_version") is not None:
            _require(
                item.get("prediction_schema_version") == "dataclean.prediction-record.v1",
                "invalid prediction schema",
            )
            _require(
                item.get("prediction_id") == _content_id(item, "prediction_id"),
                "prediction content hash mismatch",
            )
    gold = {item.get("observation_id"): item.get("disposition") for item in golden_items}
    predicted = {item.get("observation_id"): item.get("predicted_disposition") for item in prediction_items}
    _require(None not in gold and all(value in DISPOSITIONS for value in gold.values()), "invalid golden disposition")
    _require(None not in predicted and all(value in DISPOSITIONS for value in predicted.values()), "invalid predicted disposition")
    _require(set(gold) == set(predicted), "metrics prediction/golden identity mismatch")
    matrix = {actual: {pred: 0 for pred in DISPOSITIONS} for actual in DISPOSITIONS}
    for observation_id, actual in gold.items():
        matrix[actual][predicted[observation_id]] += 1
    per_class: dict[str, dict[str, float]] = {}
    for label in DISPOSITIONS:
        true_positive = matrix[label][label]
        false_positive = sum(matrix[other][label] for other in DISPOSITIONS if other != label)
        false_negative = sum(matrix[label][other] for other in DISPOSITIONS if other != label)
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1}
    total = len(gold)
    false_reject = matrix["KEEP"]["EXCLUDE"]
    return {
        "confusion_matrix": matrix,
        "per_class": per_class,
        "macro_f1": sum(item["f1"] for item in per_class.values()) / len(DISPOSITIONS),
        "keep_recall": per_class["KEEP"]["recall"],
        "false_reject_count": false_reject,
        "false_reject_rate": false_reject / sum(matrix["KEEP"].values()) if sum(matrix["KEEP"].values()) else 0.0,
        "exclude_precision": per_class["EXCLUDE"]["precision"],
        "review_coverage": sum(matrix[actual]["REVIEW"] for actual in DISPOSITIONS) / total if total else 0.0,
    }


def candidate_registry() -> dict[str, dict[str, Any]]:
    """Return the sole frozen candidate registry, in its declared order."""

    return {
        "E0": {
            "model_id": "sklearn.tfidf-char-logreg",
            "model_revision": "sklearn.tfidf-char-logreg.v1",
            "implementation_status": "MANDATORY",
            "interface_contract": "tfidf-character-ngram + logistic-regression",
            "dependency_boundary": "scikit-learn local runtime",
        },
        "E1": {
            "model_id": "BAAI/bge-small-zh-v1.5",
            "model_revision": "frozen-unresolved",
            "implementation_status": "DECLARATION_ONLY",
            "interface_contract": "frozen-embedding + linear-classifier",
            "dependency_boundary": "embedding runtime, no ROUND-002 execution",
        },
        "E2": {
            "model_id": "BAAI/bge-small-zh-v1.5",
            "model_revision": "frozen-unresolved",
            "implementation_status": "DECLARATION_ONLY",
            "interface_contract": "frozen-embedding + setfit-style classifier",
            "dependency_boundary": "embedding/setfit runtime, no ROUND-002 execution",
        },
        "E3": {
            "model_id": "hfl/chinese-macbert-base",
            "model_revision": "frozen-unresolved",
            "implementation_status": "DECLARATION_ONLY",
            "interface_contract": "supervised-sequence-classification",
            "dependency_boundary": "transformers runtime, no ROUND-002 execution",
        },
    }


def create_experiment_manifest(
    *,
    candidate_model_id: str,
    candidate_model_revision: str,
    dataset: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
    seed: int,
    hyperparameters: Mapping[str, Any],
    code_revision: str,
    package_revision: str,
    preprocessing_version: str,
    runtime: Mapping[str, Any],
) -> dict[str, Any]:
    registry = candidate_registry()
    _require(candidate_model_id in registry, "unknown candidate model")
    _require(_nonempty(candidate_model_revision), "missing candidate_model_revision")
    manifest, _, _ = _dataset_maps(dataset, []) if dataset.get("annotations") == [] else (dataset.get("manifest"), {}, {})
    # Dataset creation already validates all annotations. For nonempty datasets,
    # use its immutable manifest without needing sample records at this boundary.
    _require(isinstance(manifest, Mapping), "invalid dataset manifest")
    _require(manifest.get("dataset_version") == _content_id(manifest, "dataset_version"), "dataset version content hash mismatch")
    _require(split_manifest.get("split_manifest_id") == _content_id(split_manifest, "split_manifest_id"), "split manifest content hash mismatch")
    _require(split_manifest.get("dataset_version") == manifest.get("dataset_version"), "experiment split dataset mismatch")
    _require(isinstance(seed, int) and not isinstance(seed, bool), "seed must be an integer")
    _require(isinstance(hyperparameters, Mapping) and isinstance(runtime, Mapping), "hyperparameters and runtime must be objects")
    for field, value in (("code_revision", code_revision), ("package_revision", package_revision), ("preprocessing_version", preprocessing_version)):
        _require(_nonempty(value), f"missing {field}")
    experiment: dict[str, Any] = {
        "experiment_schema_version": "dataclean.experiment-manifest.v1",
        "candidate_model_id": candidate_model_id,
        "candidate_model_revision": candidate_model_revision,
        "dataset_version": manifest["dataset_version"],
        "dataset_content_sha256": manifest["dataset_content_sha256"],
        "split_manifest_id": split_manifest["split_manifest_id"],
        "split_manifest_sha256": _content_id(split_manifest, "split_manifest_id"),
        "seed": seed,
        "hyperparameters": deepcopy(dict(hyperparameters)),
        "code_revision": code_revision,
        "package_revision": package_revision,
        "preprocessing_version": preprocessing_version,
        "candidate_registry": candidate_registry(),
        "runtime": deepcopy(dict(runtime)),
    }
    identity = {key: value for key, value in experiment.items() if key not in {"runtime", "candidate_registry"}}
    experiment["experiment_id"] = hashlib.sha256(_canonical_bytes(identity)).hexdigest()
    return experiment


def _validate_experiment(experiment: Mapping[str, Any]) -> None:
    _require(experiment.get("experiment_schema_version") == "dataclean.experiment-manifest.v1", "invalid experiment schema")
    expected = hashlib.sha256(_canonical_bytes({key: value for key, value in experiment.items() if key not in {"runtime", "candidate_registry", "experiment_id"}})).hexdigest()
    _require(experiment.get("experiment_id") == expected, "experiment identity hash mismatch")


def _validate_experiment_links(
    experiment: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
) -> None:
    _require(
        experiment.get("dataset_version") == dataset_manifest.get("dataset_version"),
        "provenance experiment dataset version mismatch",
    )
    _require(
        experiment.get("dataset_content_sha256")
        == dataset_manifest.get("dataset_content_sha256"),
        "provenance experiment dataset hash mismatch",
    )
    _require(
        experiment.get("split_manifest_id") == split_manifest.get("split_manifest_id"),
        "provenance experiment split ID mismatch",
    )
    _require(
        experiment.get("split_manifest_sha256")
        == _content_id(split_manifest, "split_manifest_id"),
        "provenance experiment split hash mismatch",
    )


def create_prediction_records(
    experiment_manifest: Mapping[str, Any],
    dataset: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
    predictions: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    _validate_experiment(experiment_manifest)
    _require(
        split_manifest.get("split_manifest_id")
        == _content_id(split_manifest, "split_manifest_id"),
        "split manifest content hash mismatch",
    )
    manifest = dataset.get("manifest")
    _require(isinstance(manifest, Mapping), "invalid dataset")
    _validate_experiment_links(experiment_manifest, manifest, split_manifest)
    annotations = {item["observation_id"]: item for item in dataset.get("annotations", [])}
    assignments = {item["observation_id"]: item for item in split_manifest.get("assignments", [])}
    supplied = list(predictions)
    _require({item.get("observation_id") for item in supplied} == set(assignments), "prediction observations must match split")
    records: list[dict[str, Any]] = []
    for supplied_item in supplied:
        observation_id = supplied_item["observation_id"]
        _require(observation_id in annotations, "prediction annotation missing")
        _require_disposition(supplied_item.get("predicted_disposition"), "predicted_disposition")
        assignment = assignments[observation_id]
        annotation = annotations[observation_id]
        record: dict[str, Any] = {
            "prediction_schema_version": "dataclean.prediction-record.v1",
            "experiment_id": experiment_manifest["experiment_id"],
            "dataset_version": manifest["dataset_version"],
            "split_manifest_id": split_manifest["split_manifest_id"],
            "observation_id": observation_id,
            "annotation_id": annotation["annotation_id"],
            "sample_record_id": annotation["sample_record_id"],
            "exact_content_key": annotation["exact_content_key"],
            "split": assignment["split"],
            "predicted_disposition": supplied_item["predicted_disposition"],
        }
        if "model_output" in supplied_item:
            _require(isinstance(supplied_item["model_output"], Mapping), "model_output must be an object")
            record["model_output"] = deepcopy(dict(supplied_item["model_output"]))
        record["prediction_id"] = _content_id(record, "prediction_id")
        records.append(record)
    return sorted(records, key=lambda item: (item["experiment_id"], item["observation_id"]))


def resolve_prediction_provenance(
    prediction: Mapping[str, Any],
    experiment_manifest: Mapping[str, Any],
    dataset: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
    sample_records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    _validate_experiment(experiment_manifest)
    _require(
        split_manifest.get("split_manifest_id")
        == _content_id(split_manifest, "split_manifest_id"),
        "split manifest content hash mismatch",
    )
    _require(prediction.get("prediction_schema_version") == "dataclean.prediction-record.v1", "provenance invalid prediction schema")
    _require(prediction.get("prediction_id") == _content_id(prediction, "prediction_id"), "provenance prediction hash mismatch")
    _require(prediction.get("experiment_id") == experiment_manifest.get("experiment_id"), "provenance experiment mismatch")
    manifest, annotations, samples = _dataset_maps(dataset, sample_records)
    validate_split_manifest(split_manifest, dataset, samples.values())
    _validate_experiment_links(experiment_manifest, manifest, split_manifest)
    _require(prediction.get("dataset_version") == manifest.get("dataset_version"), "provenance dataset mismatch")
    _require(prediction.get("split_manifest_id") == split_manifest.get("split_manifest_id"), "provenance split mismatch")
    observation_id = prediction.get("observation_id")
    _require(observation_id in annotations and observation_id in samples, "provenance observation missing")
    annotation = annotations[observation_id]
    sample = samples[observation_id]
    assignment = next((item for item in split_manifest.get("assignments", []) if item.get("observation_id") == observation_id), None)
    _require(isinstance(assignment, Mapping), "provenance assignment missing")
    for field, expected in (("annotation_id", annotation["annotation_id"]), ("sample_record_id", sample["sample_record_id"]), ("exact_content_key", annotation["exact_content_key"]), ("split", assignment["split"])):
        _require(prediction.get(field) == expected, f"provenance {field} mismatch")
    clean = sample["clean_record"]
    return {"clean_id": clean["clean_id"], "observation_id": clean["observation_id"], "lineage": deepcopy(dict(clean["lineage"]))}


def run_e0(
    dataset: Mapping[str, Any] | None,
    sample_records: Iterable[Mapping[str, Any]],
    split_manifest: Mapping[str, Any] | None,
    *,
    seed: int,
    execution_context: str,
) -> dict[str, Any]:
    """Execute the fixed local E0 baseline or return the exact real-data blocker."""

    _require(
        execution_context in {"SYNTHETIC_TEST_ONLY", "REAL_EXECUTION"},
        "invalid execution_context",
    )
    sample_list = list(sample_records)
    if dataset is None or split_manifest is None or not sample_list:
        if execution_context == "REAL_EXECUTION":
            return _blocked_e0()
        raise ValueError("synthetic E0 needs golden dataset and split")
    manifest, annotations, samples = _dataset_maps(dataset, sample_list)
    if not annotations or not all(item["dataset_state"] == "golden" for item in annotations.values()):
        if execution_context == "REAL_EXECUTION":
            return _blocked_e0()
        raise ValueError("synthetic E0 needs golden dataset")
    validate_split_manifest(split_manifest, dataset, sample_list)
    train = [item for item in split_manifest["assignments"] if item["split"] == "train"]
    test = [item for item in split_manifest["assignments"] if item["split"] == "test"]
    _require(train and test, "E0 requires non-empty train and test splits")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    def text(entry: Mapping[str, Any]) -> str:
        return str(samples[entry["observation_id"]]["clean_record"].get("title") or "") + "\n" + samples[entry["observation_id"]]["clean_record"]["content"]

    train_text = [text(item) for item in train]
    train_labels = [annotations[item["observation_id"]]["disposition"] for item in train]
    _require(len(set(train_labels)) >= 2, "E0 requires at least two train dispositions")
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5))
    classifier = LogisticRegression(random_state=seed, max_iter=1000)
    classifier.fit(vectorizer.fit_transform(train_text), train_labels)
    test_labels = classifier.predict(vectorizer.transform([text(item) for item in test])).tolist()
    prediction_items = [{"observation_id": item["observation_id"], "predicted_disposition": label} for item, label in zip(test, test_labels, strict=True)]
    metric_gold = [annotations[item["observation_id"]] for item in test]
    return {
        "status": execution_context if execution_context == "SYNTHETIC_TEST_ONLY" else "COMPLETED",
        "candidate_model_id": "E0",
        "feature_contract": "tfidf-character-ngram",
        "classifier_contract": "logistic-regression",
        "promotable_execution_evidence": execution_context == "REAL_EXECUTION",
        "dataset_version": manifest["dataset_version"],
        "split_manifest_id": split_manifest["split_manifest_id"],
        "predictions": prediction_items,
        "metrics": compute_disposition_metrics(metric_gold, prediction_items),
    }


def _blocked_e0() -> dict[str, Any]:
    return {
        "status": "BLOCKED_NO_GOLDEN_LABELS",
        "candidate_model_id": "E0",
        "predictions": [],
        "metrics": None,
    }
