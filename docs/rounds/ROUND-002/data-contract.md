# ROUND-002 Dataset and Experiment Data Contract

> Role: Data Architecture Expert  
> Status: **DATA_CONTRACT_DONE**  
> Date: 2026-08-12  
> Evidence: **CONFIRMED — ROUND-001 contract/code inspection + USER_FROZEN_DECISIONS**

## Boundary and canonical form

This contract defines reproducible dataset, split, experiment, and prediction
artifacts above the immutable ROUND-001 CLEAN boundary.  It does not define an
annotation guideline, a teacher prompt, a confidence threshold, or the meaning
of any disposition/reason beyond the frozen enumerations below.

All persisted artifacts are UTF-8 JSON or JSONL.  Their canonical form uses
sorted object keys, no insignificant whitespace, UTF-8, and the ordered arrays
specified below.  A content-addressed ID is the lowercase SHA-256 hex digest of
the canonical JSON object after omitting that object's own ID field.  IDs are
never overwritten: a changed field creates a new artifact/version.

Every schema-version field is an exact string.  Version values below are the
only ROUND-002 v1 values; an incompatible field or meaning change requires a
new schema version rather than a silent optional-field reinterpretation.

## Frozen values and identities

```text
disposition = KEEP | EXCLUDE | REVIEW

reason_tag = ADVERTISEMENT | BOT_TEMPLATE | LOW_INFORMATION | OFF_TOPIC
           | MARKET_QUOTE_ONLY | REPOST | BROKEN_CONTENT | OTHER

annotator_type = HUMAN | TEACHER_MODEL
dataset_state = candidate | reviewed | golden
split_name = train | test
split_strategy = random_stratified | time_holdout | source_holdout
```

`observation_id` remains the only record identity.  `source_item_id`, source,
observation occurrence/version, and raw evidence/scopes remain facts attached
to that identity.  `exact_content_key` is the deterministic ROUND-001
normalized `(title, content)` relationship key, never an observation ID and
never grounds deletion or label propagation.  Dataset and split grouping use it
only to prevent content leakage.

## Sample record and sample manifest

A sample record is an immutable projection of one CLEAN record, with schema
`dataclean.sample-record.v1`.  It must contain:

```json
{
  "sample_record_schema_version": "dataclean.sample-record.v1",
  "sample_record_id": "<sha256 of this object without sample_record_id>",
  "clean_record": {
    "clean_id": "<ROUND-001 clean_id>",
    "clean_schema_version": "dataclean.clean.v1",
    "cleaning_version": "minimal.v1",
    "observation_id": "<immutable Collector ID>",
    "observation_version": 1,
    "source": "<source>",
    "source_item_id": "<source item ID>",
    "observed_at_utc": "<canonical UTC>",
    "published_at_utc": "<canonical UTC>",
    "title": "<nullable CLEAN title>",
    "content": "<CLEAN content>",
    "source_metadata": {"...": "preserved ROUND-001 metadata"},
    "cleaning": {
      "input_text_sha256": "<sha256>",
      "output_text_sha256": "<sha256>",
      "exact_content_key": "<sha256>",
      "duplicate_content_of": null
    },
    "lineage": {"...": "complete ROUND-001 Collector/raw-evidence/scopes lineage"}
  }
}
```

The ellipses above are not permission to discard fields: `clean_record` is the
full CLEAN record snapshot, not a pointer or a newly invented RAW envelope.
The shown fields are the minimum fields a validator must address directly.  A
sampler must reject a CLEAN record without a non-empty `observation_id`,
`clean_id`, `fact_fingerprint` in lineage, `exact_content_key`, or complete
ROUND-001 raw-evidence/scopes lineage.

`dataclean.sample-manifest.v1` contains `sample_manifest_id`, the input CLEAN
artifact ID/digest and its cleaning/schema versions, canonical sampler config
(filters, grouping mode, seed, and requested count), and `sample_record_ids`.
The IDs are ordered deterministically; filtering precedes seeded selection.
Sampling may select record units or exact-content group units, but when group
mode is selected, all eligible members of a selected group must be selected.
No sampling decision may inspect disposition, reason tags, sentiment, or
financial meaning.

## Annotation dataset

An annotation dataset manifest has schema `dataclean.annotation-dataset.v1` and
contains `dataset_version`, `sample_manifest_id`, the exact ordered
`annotation_ids`, record count, and this schema's canonical content hash.
`dataset_version` is the content-addressed ID of the manifest without its
`dataset_version` field.  Its annotation records are sorted by
`(observation_id, annotation_id)` in canonical JSONL order.

Each annotation record has schema `dataclean.annotation-record.v1`:

```json
{
  "annotation_schema_version": "dataclean.annotation-record.v1",
  "annotation_id": "<sha256 of this object without annotation_id>",
  "sample_record_id": "<immutable sample record ID>",
  "observation_id": "<same ID as sample record>",
  "exact_content_key": "<same value as sample record>",
  "dataset_state": "candidate",
  "disposition": "KEEP",
  "reason_tags": [],
  "annotator_type": "HUMAN",
  "annotator_id": "<non-empty actor ID>",
  "annotation_version": "<non-empty annotation guideline/version reference>",
  "annotated_at_utc": "<canonical UTC>",
  "confidence": null,
  "note": null,
  "supersedes_annotation_id": null,
  "source_record_lineage": {"...": "full immutable sample CLEAN snapshot lineage"},
  "golden_review": null
}
```

`reason_tags` is a deduplicated lexicographically sorted array of the frozen
values; it may be empty and never implies a disposition.  `confidence` is null
or a finite number in `[0, 1]`; it has no contract-level threshold or state
transition effect.  `note` is null or a string.  `source_record_lineage` must
be the full lineage snapshot from its sample record, including CLEAN ID/version,
Collector versions, fact fingerprint, raw evidence, and scopes.  The referenced
sample record, observation ID, exact-content key, and lineage fingerprint must
all agree; disagreement is a fatal provenance error.

There is at most one annotation record for an `observation_id` in a single
dataset manifest.  Review history is represented by a new immutable dataset
version and a non-null `supersedes_annotation_id`, never by mutating a prior
JSONL record.

### State and human-golden boundary

| State | Allowed annotator | Required rule | Forbidden transition/result |
| --- | --- | --- | --- |
| `candidate` | `HUMAN` or `TEACHER_MODEL` | Valid frozen disposition/reason syntax | Automatic promotion to any other state |
| `reviewed` | `HUMAN` only | Non-null `supersedes_annotation_id` to a candidate/reviewed annotation | `TEACHER_MODEL` review |
| `golden` | `HUMAN` only | Non-null `golden_review` with `reviewer_type: HUMAN`, non-empty `reviewer_id`, canonical `reviewed_at_utc`, non-empty `review_rule_version`, and non-empty `supersedes_annotation_id` | Teacher-originated or automatically promoted golden |

`golden_review` records that the current external human-review rule was applied;
this contract deliberately does not define that rule, require a particular
number of reviewers, or infer its satisfaction from confidence/note.  A human
may review a teacher candidate only by producing a new HUMAN annotation record.
The teacher record itself remains `candidate`; it cannot be relabeled in place.
`MODEL_PREDICTION` is not an annotator type and is invalid in every annotation
dataset state.

## Teacher exchange

Teacher exchange is model-neutral and is only permitted for candidate data.

- `dataclean.teacher-export.v1` contains `teacher_export_id`, source
  `sample_manifest_id`, ordered sample record snapshots/IDs, and an opaque
  `request_metadata` object.  It contains no invented prompt or review policy.
- `dataclean.teacher-import.v1` contains `teacher_import_id`, the source export
  ID, non-empty `teacher_model_id`, nullable `teacher_model_revision`, and
  ordered response items keyed by `sample_record_id`/`observation_id`.
- Importing a valid response produces new `TEACHER_MODEL`, `candidate`
  annotation records only.  Proposed disposition/reasons use exactly the frozen
  values; malformed, missing, unknown, duplicate, or source-mismatched items
  fail import rather than being guessed or partially promoted.
- Export/import IDs address the supplied exchange artifacts.  Importing the
  same canonical response produces the same candidate records; no execution of
  an LLM is implied by this contract.

## Group-aware split manifest

A split consumes a single `golden` annotation dataset only.  It must have
schema `dataclean.split-manifest.v1`, a content-addressed `split_manifest_id`,
the exact `dataset_version`, strategy/config/seed, and canonical assignments:

```json
{
  "observation_id": "<ID>",
  "annotation_id": "<golden annotation ID>",
  "exact_content_key": "<sha256>",
  "split": "train"
}
```

Every dataset observation appears exactly once; each exact-content key maps to
exactly one split; assignments are ordered by `(exact_content_key,
observation_id)`.  Therefore neither an observation identity nor any
exact-content group may cross train/test.  Candidate/reviewed data, missing
group keys, duplicate assignments, and manifest/dataset version mismatches are
fatal errors.

- `random_stratified` requires a fixed seed and test fraction.  It stratifies
  group units only when every member of a group has one same disposition;
  conflicting group labels fail with `SPLIT_GROUP_LABEL_CONFLICT` rather than
  inventing an aggregation rule.
- `time_holdout` requires a canonical UTC cutoff.  `observed_at_utc < cutoff`
  is train and `>= cutoff` is test.  A group spanning that boundary fails with
  `SPLIT_GROUP_BOUNDARY_CONFLICT`; it is not silently split or reassigned.
- `source_holdout` requires a canonical sorted non-empty held-out source list.
  Held-out sources are test and all other sources are train.  A group spanning
  those source sides fails with `SPLIT_GROUP_BOUNDARY_CONFLICT`.

An implementation may reject a mathematically impossible strategy/input pair;
it may not resolve leakage by using raw text semantics, label heuristics, or
duplicating an observation.

## Experiment and prediction artifacts

An experiment manifest has schema `dataclean.experiment-manifest.v1`.
`experiment_id` is the SHA-256 of the canonical **identity payload**:

```text
experiment schema version + candidate model ID + model revision + dataset version
+ dataset content hash + split manifest ID/hash + seed + canonical hyperparameters
+ code/package revision identifiers + preprocessing/feature contract version
```

The manifest also records supported candidate declarations and runtime metadata.
Runtime observations such as elapsed time, host, Python/package versions, and
hardware are required for execution evidence but excluded from `experiment_id`;
they do not alter the logical experiment.  A result status may be
`COMPLETED`, `BLOCKED_NO_GOLDEN_LABELS`, or `FAILED`; no status fabricates
metrics or predictions.

Predictions are independent JSONL artifacts with schema
`dataclean.prediction-record.v1`, sorted by `(experiment_id, observation_id)`.
Each record contains a content-addressed `prediction_id`, `experiment_id`,
`dataset_version`, `split_manifest_id`, `observation_id`, `annotation_id`,
`sample_record_id`, `exact_content_key`, the assigned split, and exactly one
`predicted_disposition` from the frozen disposition values.  It may carry
model-native scores as an opaque `model_output` object, but must not contain a
gold disposition, golden reason tags, annotation state, or a field that makes a
prediction writable as an annotation.

Prediction provenance resolves without text matching:

```text
prediction_id -> experiment_id -> dataset_version + split_manifest_id
              -> annotation_id -> sample_record_id -> clean_id
              -> observation_id -> Collector raw evidence/scopes
```

The resolver must verify all repeated IDs/keys against the referenced immutable
artifacts.  A missing link, version/hash mismatch, or identity/key mismatch is a
fatal provenance failure.  Metrics consume only prediction records joined to
the golden annotation dataset through this chain; they do not add labels to the
prediction artifact.

## Required validator outcomes

The implementation and QA suite must make the following failures explicit:

1. invalid disposition/reason/annotator/state or unsorted/duplicate reason tags;
2. teacher annotation in `reviewed`/`golden`, prediction mixed into annotation,
   or absent human golden-review attestation;
3. missing/mismatched observation, clean, exact-content, lineage, sample,
   dataset, split, experiment, or prediction references;
4. mutable overwrite of a content-addressed artifact/version;
5. observation or exact-content-group split leakage, invalid strategy boundary,
   or non-golden data supplied to a split; and
6. non-deterministic canonical ordering/ID generation for identical inputs.

## Handoff

Developer implements only these schema, validation, serialization, and resolver
boundaries.  QA freezes acceptance/regressions from the required outcomes.
Research Owner retains label guidance, teacher choice/prompt, human review rule
content, confidence policy, and any future model-route decision.
