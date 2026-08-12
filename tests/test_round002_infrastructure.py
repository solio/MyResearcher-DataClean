"""Synthetic contract tests for ROUND-002 infrastructure.

These fixtures are deliberately synthetic.  They prove deterministic schema and
algorithm boundaries only; they are never real Collector sampling or real
human-golden / E0 evidence.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import tomllib

import pytest


def _api():
    """Load the frozen ROUND-002 public API at test time (Expected RED pre-dev)."""

    return importlib.import_module("myresearcher_dataclean.research")


def _content_id(value: dict, own_id: str) -> str:
    """Fixture-side canonical content ID for teacher-exchange tampering tests."""

    payload = {key: item for key, item in value.items() if key != own_id}
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def _clean(
    observation_id: str,
    *,
    source: str = "source-a",
    observed_at_utc: str = "2026-08-01T00:00:00.000000Z",
    exact_content_key: str | None = None,
    content: str | None = None,
) -> dict:
    """A complete synthetic ROUND-001 CLEAN snapshot for contract testing."""

    key = exact_content_key or f"content-{observation_id}"
    return {
        "clean_schema_version": "dataclean.clean.v1",
        "clean_id": f"clean-{observation_id}",
        "observation_id": observation_id,
        "observation_version": 1,
        "source": source,
        "source_item_id": f"item-{observation_id}",
        "observed_at_utc": observed_at_utc,
        "published_at_utc": observed_at_utc,
        "title": f"title {observation_id}",
        "content": content or f"正文 {observation_id}",
        "source_metadata": {"fixture": "ROUND-002 synthetic"},
        "cleaning": {
            "version": "minimal.v1",
            "input_text_sha256": "1" * 64,
            "output_text_sha256": "2" * 64,
            "exact_content_key": key,
            "duplicate_content_of": None,
        },
        "lineage": {
            "observation_id": observation_id,
            "source": source,
            "source_item_id": f"item-{observation_id}",
            "observation_version": 1,
            "collector_storage_version": 2,
            "collector_schema_version": "collector.raw.v2",
            "collector_version": "collector.v2",
            "parser_version": "parser.v2",
            "fact_fingerprint": f"fingerprint-{observation_id}",
            "drift_from_observation_id": None,
            "raw_evidence": [{"evidence_id": f"raw-{observation_id}"}],
            "scopes": [{"scope_key": "fixture:round002"}],
        },
    }


@pytest.fixture
def clean_records() -> list[dict]:
    return [
        _clean("obs-1", exact_content_key="group-a", content="甲" * 10),
        _clean(
            "obs-2",
            source="source-b",
            observed_at_utc="2026-08-03T00:00:00.000000Z",
            exact_content_key="group-a",
            content="甲" * 10,
        ),
        _clean(
            "obs-3",
            source="source-b",
            observed_at_utc="2026-08-03T00:00:00.000000Z",
            exact_content_key="group-b",
            content="乙" * 12,
        ),
        _clean(
            "obs-4",
            source="source-c",
            observed_at_utc="2026-08-05T00:00:00.000000Z",
            exact_content_key="group-c",
            content="丙" * 14,
        ),
    ]


def _sample(clean_records: list[dict]) -> dict:
    return _api().sample_clean_records(
        clean_records,
        input_clean_artifact_id="synthetic-clean-artifact-v1",
        seed=17,
        requested_count=4,
        grouping_mode="record",
    )


def _candidate(sample_record: dict, disposition: str = "KEEP") -> dict:
    return _api().create_annotation_record(
        sample_record,
        dataset_state="candidate",
        disposition=disposition,
        reason_tags=[],
        annotator_type="HUMAN",
        annotator_id="fixture-annotator",
        annotation_version="fixture-guideline.v1",
        annotated_at_utc="2026-08-10T00:00:00.000000Z",
    )


def _golden(sample_record: dict, disposition: str) -> tuple[dict, dict]:
    """Return the immutable candidate predecessor and its golden successor."""

    candidate = _candidate(sample_record, disposition)
    golden = _api().create_annotation_record(
        sample_record,
        dataset_state="golden",
        disposition=disposition,
        reason_tags=[],
        annotator_type="HUMAN",
        annotator_id="fixture-reviewer",
        annotation_version="fixture-guideline.v1",
        annotated_at_utc="2026-08-11T00:00:00.000000Z",
        supersedes_annotation_id=candidate["annotation_id"],
        golden_review={
            "reviewer_type": "HUMAN",
            "reviewer_id": "fixture-reviewer",
            "reviewed_at_utc": "2026-08-11T00:00:00.000000Z",
            "review_rule_version": "fixture-human-rule.v1",
        },
    )
    return candidate, golden


def _golden_records(
    sample_records: list[dict], dispositions: list[str]
) -> tuple[list[dict], list[dict]]:
    pairs = [
        _golden(record, disposition)
        for record, disposition in zip(sample_records, dispositions, strict=True)
    ]
    return [candidate for candidate, _ in pairs], [golden for _, golden in pairs]


def _golden_dataset(sample: dict) -> dict:
    labels = ["KEEP", "KEEP", "REVIEW", "EXCLUDE"]
    priors, annotations = _golden_records(sample["records"], labels)
    return _api().build_annotation_dataset(
        sample["manifest"], annotations, prior_annotations=priors
    )


def _rehashed(value: dict, own_id: str) -> dict:
    """Return a self-consistent forged artifact for semantic validator tests."""

    forged = deepcopy(value)
    forged[own_id] = _content_id(forged, own_id)
    return forged


def _rehashed_experiment(value: dict) -> dict:
    """Recompute an experiment identity under the contract's identity payload."""

    forged = deepcopy(value)
    identity = {
        key: item
        for key, item in forged.items()
        if key not in {"runtime", "candidate_registry", "experiment_id"}
    }
    forged["experiment_id"] = hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return forged


def _balanced_golden_fixture() -> tuple[dict, dict, dict]:
    """Six independent groups: each disposition can populate both splits."""

    api = _api()
    records = [
        _clean(f"obs-{label.lower()}-{number}", exact_content_key=f"{label}-{number}")
        for label in ("KEEP", "EXCLUDE", "REVIEW")
        for number in ("1", "2")
    ]
    sample = api.sample_clean_records(
        records,
        input_clean_artifact_id="synthetic-balanced-clean.v1",
        seed=3,
        requested_count=6,
    )
    priors, annotations = _golden_records(
        sample["records"],
        [record["clean_record"]["observation_id"].split("-")[1].upper() for record in sample["records"]],
    )
    return (
        sample,
        api.build_annotation_dataset(
            sample["manifest"], annotations, prior_annotations=priors
        ),
        records,
    )


def test_sampler_is_deterministic_filters_and_preserves_full_clean_snapshot(
    clean_records: list[dict],
) -> None:
    api = _api()
    first = api.sample_clean_records(
        clean_records,
        input_clean_artifact_id="synthetic-clean-artifact-v1",
        seed=17,
        requested_count=2,
        sources=["source-a", "source-b"],
        observed_at_start="2026-08-01T00:00:00.000000Z",
        observed_at_end="2026-08-04T00:00:00.000000Z",
        minimum_text_length=10,
        grouping_mode="exact_content_group",
    )
    second = api.sample_clean_records(
        clean_records,
        input_clean_artifact_id="synthetic-clean-artifact-v1",
        seed=17,
        requested_count=2,
        sources=["source-a", "source-b"],
        observed_at_start="2026-08-01T00:00:00.000000Z",
        observed_at_end="2026-08-04T00:00:00.000000Z",
        minimum_text_length=10,
        grouping_mode="exact_content_group",
    )

    assert first == second
    assert first["manifest"]["sample_manifest_schema_version"] == (
        "dataclean.sample-manifest.v1"
    )
    assert first["manifest"]["sample_manifest_id"]
    assert first["manifest"]["sample_record_ids"] == [
        record["sample_record_id"] for record in first["records"]
    ]
    assert first["manifest"]["input_clean_schema_version"] == "dataclean.clean.v1"
    assert first["manifest"]["input_cleaning_version"] == "minimal.v1"
    # Group mode selects the complete relationship group, never one representative.
    assert [record["clean_record"]["observation_id"] for record in first["records"]] == [
        "obs-1",
        "obs-2",
        "obs-3",
    ]
    for sample_record in first["records"]:
        clean = sample_record["clean_record"]
        assert sample_record["sample_record_schema_version"] == "dataclean.sample-record.v1"
        assert clean["lineage"]["raw_evidence"]
        assert clean["lineage"]["scopes"]
        assert clean["lineage"]["fact_fingerprint"]
        assert clean["cleaning"]["exact_content_key"]

    inconsistent_version = deepcopy(clean_records)
    inconsistent_version[-1]["cleaning"]["version"] = "minimal.v2"
    with pytest.raises(ValueError, match="CLEANing version"):
        api.sample_clean_records(
            inconsistent_version,
            input_clean_artifact_id="synthetic-clean-artifact-v1",
            seed=17,
            requested_count=2,
        )


def test_annotation_state_teacher_and_prediction_boundaries_are_fatal(
    clean_records: list[dict],
) -> None:
    api = _api()
    sample = _sample(clean_records)
    candidate = _candidate(sample["records"][0])
    dataset = api.build_annotation_dataset(sample["manifest"], [candidate])
    assert dataset["manifest"]["dataset_state"] == "candidate"
    assert dataset["manifest"]["dataset_version"]

    teacher = deepcopy(candidate)
    teacher.update({"annotator_type": "TEACHER_MODEL", "dataset_state": "golden"})
    with pytest.raises(ValueError, match="TEACHER_MODEL.*golden"):
        api.build_annotation_dataset(sample["manifest"], [teacher])

    missing_attestation = deepcopy(candidate)
    missing_attestation.update(
        {
            "dataset_state": "golden",
            "supersedes_annotation_id": candidate["annotation_id"],
            "golden_review": None,
        }
    )
    with pytest.raises(ValueError, match="golden_review"):
        api.build_annotation_dataset(sample["manifest"], [missing_attestation])

    bad_reason = deepcopy(candidate)
    bad_reason["reason_tags"] = ["OTHER", "NOT_A_FROZEN_REASON"]
    with pytest.raises(ValueError, match="reason"):
        api.build_annotation_dataset(sample["manifest"], [bad_reason])

    with pytest.raises(ValueError, match="prediction.*annotation"):
        api.build_annotation_dataset(
            sample["manifest"],
            [{**candidate, "prediction_id": "must-not-be-here"}],
        )

    exported = api.export_teacher_candidates(
        sample["manifest"], sample["records"], request_metadata={"fixture": True}
    )
    teacher_import = {
            "teacher_import_schema_version": "dataclean.teacher-import.v1",
            "teacher_export_id": exported["teacher_export_id"],
            "teacher_model_id": "fixture-teacher",
            "teacher_model_revision": None,
            "response_items": [
                {
                    "sample_record_id": sample["records"][0]["sample_record_id"],
                    "observation_id": "obs-1",
                    "disposition": "EXCLUDE",
                    "reason_tags": ["OTHER"],
                }
            ],
        }
    teacher_import["teacher_import_id"] = _content_id(teacher_import, "teacher_import_id")
    imported = api.import_teacher_candidates(
        exported,
        teacher_import,
        annotation_version="fixture-guideline.v1",
        annotated_at_utc="2026-08-11T00:00:00.000000Z",
    )
    assert imported[0]["annotator_type"] == "TEACHER_MODEL"
    assert imported[0]["dataset_state"] == "candidate"

    mismatched_import = deepcopy(teacher_import)
    mismatched_import["teacher_export_id"] = "other-export"
    mismatched_import["teacher_import_id"] = _content_id(
        mismatched_import, "teacher_import_id"
    )
    with pytest.raises(ValueError, match="teacher import source mismatch"):
        api.import_teacher_candidates(
            exported,
            mismatched_import,
            annotation_version="fixture-guideline.v1",
            annotated_at_utc="2026-08-11T00:00:00.000000Z",
        )

    mixed_prior, mixed_golden = _golden(sample["records"][1], "KEEP")
    with pytest.raises(ValueError, match="mixed dataset states"):
        api.build_annotation_dataset(
            sample["manifest"], [candidate, mixed_golden], prior_annotations=[mixed_prior]
        )

    annotated = api.create_annotation_record(
        sample["records"][2],
        dataset_state="candidate",
        disposition="REVIEW",
        reason_tags=[],
        annotator_type="HUMAN",
        annotator_id="fixture-annotator",
        annotation_version="fixture-guideline.v1",
        annotated_at_utc="2026-08-10T00:00:00.000000Z",
        confidence=0.75,
        note="opaque review context",
    )
    assert annotated["confidence"] == 0.75
    assert annotated["note"] == "opaque review context"
    with pytest.raises(ValueError, match="invalid confidence"):
        api.create_annotation_record(
            sample["records"][3],
            dataset_state="candidate",
            disposition="KEEP",
            reason_tags=[],
            annotator_type="HUMAN",
            annotator_id="fixture-annotator",
            annotation_version="fixture-guideline.v1",
            annotated_at_utc="2026-08-10T00:00:00.000000Z",
            confidence=1.1,
        )

    outside_sample = _candidate(sample["records"][3])
    unrelated_manifest = api.sample_clean_records(
        clean_records[:1],
        input_clean_artifact_id="other-sample-artifact.v1",
        seed=7,
        requested_count=1,
    )["manifest"]
    with pytest.raises(ValueError, match="sample manifest"):
        api.build_annotation_dataset(unrelated_manifest, [outside_sample])

    predecessor, unattested_parent = _golden(sample["records"][0], "KEEP")
    unattested_parent["supersedes_annotation_id"] = "unknown-prior-annotation"
    unattested_parent = _rehashed(unattested_parent, "annotation_id")
    with pytest.raises(ValueError, match="supersedes annotation is missing"):
        api.build_annotation_dataset(
            sample["manifest"], [unattested_parent], prior_annotations=[predecessor]
        )

    other_predecessor = _candidate(sample["records"][1], "KEEP")
    cross_observation = deepcopy(unattested_parent)
    cross_observation["supersedes_annotation_id"] = other_predecessor["annotation_id"]
    cross_observation = _rehashed(cross_observation, "annotation_id")
    with pytest.raises(ValueError, match="supersedes annotation identity mismatch"):
        api.build_annotation_dataset(
            sample["manifest"],
            [cross_observation],
            prior_annotations=[predecessor, other_predecessor],
        )

    lineage_tampered = _candidate(sample["records"][0])
    lineage_tampered["source_record_lineage"]["clean_id"] = "forged-clean-id"
    lineage_tampered = _rehashed(lineage_tampered, "annotation_id")
    with pytest.raises(ValueError, match="annotation source lineage mismatch"):
        api.build_annotation_dataset(sample["manifest"], [lineage_tampered])


def test_split_manifest_has_three_strategy_boundaries_and_no_identity_or_content_leakage(
    clean_records: list[dict],
) -> None:
    api = _api()
    sample = _sample(clean_records)
    dataset = _golden_dataset(sample)

    random_split = api.create_split_manifest(
        dataset, sample["records"], strategy="random_stratified", seed=7, test_fraction=0.5
    )
    assert api.validate_split_manifest(random_split, dataset, sample["records"]) is None
    assignments = random_split["assignments"]
    assert [
        (entry["exact_content_key"], entry["observation_id"]) for entry in assignments
    ] == sorted((entry["exact_content_key"], entry["observation_id"]) for entry in assignments)
    by_group: dict[str, set[str]] = {}
    for assignment in assignments:
        by_group.setdefault(assignment["exact_content_key"], set()).add(assignment["split"])
    assert all(len(splits) == 1 for splits in by_group.values())

    conflicting_priors, conflicting_annotations = _golden_records(
        sample["records"], ["KEEP", "EXCLUDE", "REVIEW", "EXCLUDE"]
    )
    conflicting_dataset = api.build_annotation_dataset(
        sample["manifest"], conflicting_annotations, prior_annotations=conflicting_priors
    )
    with pytest.raises(ValueError, match="SPLIT_GROUP_LABEL_CONFLICT"):
        api.create_split_manifest(
            conflicting_dataset,
            sample["records"],
            strategy="random_stratified",
            seed=7,
            test_fraction=0.5,
        )

    with pytest.raises(ValueError, match="SPLIT_GROUP_BOUNDARY_CONFLICT"):
        api.create_split_manifest(
            dataset,
            sample["records"],
            strategy="time_holdout",
            cutoff_utc="2026-08-02T00:00:00.000000Z",
        )
    with pytest.raises(ValueError, match="SPLIT_GROUP_BOUNDARY_CONFLICT"):
        api.create_split_manifest(
            dataset, sample["records"], strategy="source_holdout", held_out_sources=["source-a"]
        )

    non_golden = api.build_annotation_dataset(
        sample["manifest"], [_candidate(sample["records"][0])]
    )
    with pytest.raises(ValueError, match="golden"):
        api.create_split_manifest(
            non_golden,
            sample["records"][:1],
            strategy="random_stratified",
            seed=7,
            test_fraction=0.5,
        )

    leaked = deepcopy(random_split)
    leaked["assignments"][1]["split"] = "test" if leaked["assignments"][0]["split"] == "train" else "train"
    with pytest.raises(ValueError, match="leakage"):
        api.validate_split_manifest(leaked, dataset, sample["records"])


def test_split_validator_replays_strategy_not_just_self_consistent_assignments() -> None:
    """A rehashed manifest cannot masquerade as a different valid holdout split."""

    api = _api()
    records = [
        _clean(
            f"boundary-{number}",
            source="source-a" if number < 3 else "source-b",
            observed_at_utc=(
                "2026-08-01T00:00:00.000000Z"
                if number < 3
                else "2026-08-03T00:00:00.000000Z"
            ),
            exact_content_key=f"boundary-group-{number}",
        )
        for number in range(4)
    ]
    sample = api.sample_clean_records(
        records,
        input_clean_artifact_id="boundary-clean.v1",
        seed=1,
        requested_count=4,
    )
    priors, annotations = _golden_records(sample["records"], ["KEEP"] * 4)
    dataset = api.build_annotation_dataset(
        sample["manifest"], annotations, prior_annotations=priors
    )
    random_split = api.create_split_manifest(
        dataset, sample["records"], strategy="random_stratified", seed=2, test_fraction=0.5
    )
    forged = deepcopy(random_split)
    forged["strategy"] = "time_holdout"
    forged["config"] = {"cutoff_utc": "2026-08-02T00:00:00.000000Z"}
    forged = _rehashed(forged, "split_manifest_id")
    with pytest.raises(ValueError, match="split strategy replay mismatch"):
        api.validate_split_manifest(forged, dataset, sample["records"])


def test_random_stratified_split_preserves_each_feasible_disposition_in_both_sides() -> None:
    """The strategy must stratify group units, not merely randomly select groups."""

    api = _api()
    sample, dataset, _ = _balanced_golden_fixture()
    split = api.create_split_manifest(
        dataset,
        sample["records"],
        strategy="random_stratified",
        seed=1,
        test_fraction=0.5,
    )
    by_observation = {
        record["observation_id"]: record["disposition"]
        for record in dataset["annotations"]
    }
    by_label: dict[str, set[str]] = {}
    for assignment in split["assignments"]:
        by_label.setdefault(by_observation[assignment["observation_id"]], set()).add(
            assignment["split"]
        )
    assert by_label == {label: {"train", "test"} for label in ("KEEP", "EXCLUDE", "REVIEW")}


def test_metrics_match_hand_calculation_including_empty_denominators() -> None:
    api = _api()
    golden = [
        {"observation_id": "1", "disposition": "KEEP"},
        {"observation_id": "2", "disposition": "EXCLUDE"},
        {"observation_id": "3", "disposition": "REVIEW"},
        {"observation_id": "4", "disposition": "KEEP"},
    ]
    predictions = [
        {"observation_id": "1", "predicted_disposition": "EXCLUDE"},
        {"observation_id": "2", "predicted_disposition": "EXCLUDE"},
        {"observation_id": "3", "predicted_disposition": "REVIEW"},
        {"observation_id": "4", "predicted_disposition": "KEEP"},
    ]
    metrics = api.compute_disposition_metrics(golden, predictions)
    assert metrics["confusion_matrix"] == {
        "KEEP": {"KEEP": 1, "EXCLUDE": 1, "REVIEW": 0},
        "EXCLUDE": {"KEEP": 0, "EXCLUDE": 1, "REVIEW": 0},
        "REVIEW": {"KEEP": 0, "EXCLUDE": 0, "REVIEW": 1},
    }
    assert metrics["per_class"]["KEEP"] == {"precision": 1.0, "recall": 0.5, "f1": 2 / 3}
    assert metrics["per_class"]["EXCLUDE"] == {"precision": 0.5, "recall": 1.0, "f1": 2 / 3}
    assert metrics["per_class"]["REVIEW"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    assert metrics["macro_f1"] == pytest.approx(7 / 9)
    assert metrics["keep_recall"] == 0.5
    assert metrics["false_reject_count"] == 1
    assert metrics["false_reject_rate"] == 0.5
    assert metrics["exclude_precision"] == 0.5
    assert metrics["review_coverage"] == 0.25

    empty = api.compute_disposition_metrics([], [])
    assert empty["macro_f1"] == 0.0
    assert empty["false_reject_count"] == 0
    assert empty["false_reject_rate"] == 0.0
    assert empty["review_coverage"] == 0.0

    with pytest.raises(ValueError, match="duplicate golden observation_id"):
        api.compute_disposition_metrics(
            [
                {"observation_id": "dup", "disposition": "KEEP"},
                {"observation_id": "dup", "disposition": "EXCLUDE"},
            ],
            [{"observation_id": "dup", "predicted_disposition": "KEEP"}],
        )
    with pytest.raises(ValueError, match="duplicate prediction observation_id"):
        api.compute_disposition_metrics(
            [{"observation_id": "dup", "disposition": "KEEP"}],
            [
                {"observation_id": "dup", "predicted_disposition": "KEEP"},
                {"observation_id": "dup", "predicted_disposition": "EXCLUDE"},
            ],
        )


def test_experiment_prediction_provenance_is_independent_and_resolvable(
    clean_records: list[dict],
) -> None:
    api = _api()
    sample = _sample(clean_records)
    dataset = _golden_dataset(sample)
    split = api.create_split_manifest(
        dataset, sample["records"], strategy="random_stratified", seed=11, test_fraction=0.5
    )
    manifest = api.create_experiment_manifest(
        candidate_model_id="E0",
        candidate_model_revision="sklearn.tfidf-char-logreg.v1",
        dataset=dataset,
        split_manifest=split,
        seed=11,
        hyperparameters={"ngram_range": [2, 5], "C": 1.0},
        code_revision="fixture-code-revision",
        package_revision="fixture-package-revision",
        preprocessing_version="round002.e0.features.v1",
        runtime={"python": "synthetic-fixture"},
    )
    assert manifest["experiment_schema_version"] == "dataclean.experiment-manifest.v1"
    assert manifest["experiment_id"]
    assert manifest["runtime"] == {"python": "synthetic-fixture"}
    different_runtime = api.create_experiment_manifest(
        candidate_model_id="E0",
        candidate_model_revision="sklearn.tfidf-char-logreg.v1",
        dataset=dataset,
        split_manifest=split,
        seed=11,
        hyperparameters={"ngram_range": [2, 5], "C": 1.0},
        code_revision="fixture-code-revision",
        package_revision="fixture-package-revision",
        preprocessing_version="round002.e0.features.v1",
        runtime={"python": "another-runtime", "host": "different-host"},
    )
    assert different_runtime["experiment_id"] == manifest["experiment_id"]

    predictions = api.create_prediction_records(
        manifest,
        dataset,
        split,
        [
            {"observation_id": entry["observation_id"], "predicted_disposition": "KEEP"}
            for entry in split["assignments"]
        ],
    )
    assert [
        (item["experiment_id"], item["observation_id"]) for item in predictions
    ] == sorted((item["experiment_id"], item["observation_id"]) for item in predictions)
    assert all("disposition" not in item for item in predictions)
    assert all("golden_review" not in item for item in predictions)
    resolved = api.resolve_prediction_provenance(
        predictions[0], manifest, dataset, split, sample["records"]
    )
    assert resolved["clean_id"] == sample["records"][0]["clean_record"]["clean_id"]
    assert resolved["lineage"]["raw_evidence"]

    tampered = deepcopy(predictions[0])
    tampered["exact_content_key"] = "wrong-group"
    with pytest.raises(ValueError, match="provenance"):
        api.resolve_prediction_provenance(tampered, manifest, dataset, split, sample["records"])

    tampered_split = deepcopy(split)
    tampered_split["config"]["seed"] = 999
    with pytest.raises(ValueError, match="split manifest content hash mismatch"):
        api.create_prediction_records(
            manifest,
            dataset,
            tampered_split,
            [
                {"observation_id": entry["observation_id"], "predicted_disposition": "KEEP"}
                for entry in split["assignments"]
            ],
        )
    with pytest.raises(ValueError, match="split manifest content hash mismatch"):
        api.resolve_prediction_provenance(
            predictions[0], manifest, dataset, tampered_split, sample["records"]
        )

    forged_experiment = deepcopy(manifest)
    forged_experiment["dataset_content_sha256"] = "forged-dataset-hash"
    forged_experiment = _rehashed_experiment(forged_experiment)
    forged_prediction = deepcopy(predictions[0])
    forged_prediction["experiment_id"] = forged_experiment["experiment_id"]
    forged_prediction = _rehashed(forged_prediction, "prediction_id")
    with pytest.raises(ValueError, match="provenance experiment dataset hash mismatch"):
        api.resolve_prediction_provenance(
            forged_prediction, forged_experiment, dataset, split, sample["records"]
        )


def test_e0_is_deterministic_for_synthetic_test_only_and_blocks_without_real_golden(
    clean_records: list[dict],
) -> None:
    api = _api()
    sample = _sample(clean_records)
    dataset = _golden_dataset(sample)
    split = api.create_split_manifest(
        dataset, sample["records"], strategy="random_stratified", seed=19, test_fraction=0.5
    )
    first = api.run_e0(
        dataset, sample["records"], split, seed=19, execution_context="SYNTHETIC_TEST_ONLY"
    )
    second = api.run_e0(
        dataset, sample["records"], split, seed=19, execution_context="SYNTHETIC_TEST_ONLY"
    )
    assert first == second
    assert first["status"] == "SYNTHETIC_TEST_ONLY"
    assert first["candidate_model_id"] == "E0"
    assert first["feature_contract"] == "tfidf-character-ngram"
    assert first["classifier_contract"] == "logistic-regression"
    assert first["promotable_execution_evidence"] is False

    blocked = api.run_e0(None, [], None, seed=19, execution_context="REAL_EXECUTION")
    assert blocked == {
        "status": "BLOCKED_NO_GOLDEN_LABELS",
        "candidate_model_id": "E0",
        "predictions": [],
        "metrics": None,
    }


def test_e0_executes_qualified_real_context_without_promoting_synthetic_fixture() -> None:
    """REAL_EXECUTION is executable when its caller supplies a valid golden dataset.

    This in-memory fixture remains synthetic test evidence; the context branch only
    proves the runner is not hard-coded to block and does not create a persisted
    capability claim.
    """

    api = _api()
    sample, dataset, _ = _balanced_golden_fixture()
    split = api.create_split_manifest(
        dataset,
        sample["records"],
        strategy="random_stratified",
        seed=1,
        test_fraction=0.5,
    )
    result = api.run_e0(
        dataset, sample["records"], split, seed=1, execution_context="REAL_EXECUTION"
    )
    assert result["status"] == "COMPLETED"
    assert result["candidate_model_id"] == "E0"
    assert len(result["predictions"]) == 3
    assert result["metrics"] is not None


def test_e1_to_e3_registry_is_fixed_and_e4_is_absent() -> None:
    registry = _api().candidate_registry()
    assert list(registry) == ["E0", "E1", "E2", "E3"]
    assert registry["E0"]["implementation_status"] == "MANDATORY"
    for candidate in ("E1", "E2", "E3"):
        assert registry[candidate]["implementation_status"] == "DECLARATION_ONLY"
        assert registry[candidate]["model_id"]
        assert "model_revision" in registry[candidate]
        assert registry[candidate]["interface_contract"]
        assert registry[candidate]["dependency_boundary"]
    assert "E4" not in registry


def test_e0_runtime_dependency_is_declared_for_replayable_installation() -> None:
    """E0 imports scikit-learn at runtime, so it must be a project dependency."""

    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert "scikit-learn>=1.8,<2" in project["project"]["dependencies"]
