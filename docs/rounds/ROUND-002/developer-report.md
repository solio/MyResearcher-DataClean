# ROUND-002 Developer Report

> Role: Developer  
> Status: **SLICE_IMPLEMENTED / TESTS_RUN**  
> Date: 2026-08-12

## Implemented scope

Added `myresearcher_dataclean.research`, implementing the frozen ROUND-002
public API only:

- canonical UTF-8 JSON content addressing for sample, annotation, dataset,
  teacher exchange, split, experiment, and prediction artifacts;
- sample-manifest input CLEAN schema/cleaning versions and a canonical complete
  input snapshot digest, with mismatched versions rejected before sampling;
- deterministic CLEAN sampler with source/time/length filters and complete
  exact-content group selection;
- immutable annotation records, candidate/reviewed/golden validation, human
  golden attestation boundary, and model-neutral teacher import/export;
- teacher import content-address validation and immutable export-ID linkage;
- group-aware random/time/source split construction and leakage validation;
- unified disposition metrics and independent prediction provenance resolver;
- fixed E0 local TF-IDF character n-gram + Logistic Regression execution for
  `SYNTHETIC_TEST_ONLY`, plus the exact real-execution
  `BLOCKED_NO_GOLDEN_LABELS` result only when a real execution lacks a
  qualifying golden dataset/split. A supplied qualifying real golden dataset
  executes E0 and reports `COMPLETED`.
- ordered fixed E0--E3 registry. E1--E3 remain declaration-only and perform
  no model execution.

`pyproject.toml` declares the bounded local E0 runtime dependency
`scikit-learn>=1.8,<2`.

No external network call, LLM call, prompt, real label generation, financial
semantic rule, or new candidate model was added. Synthetic E0 results carry
`promotable_execution_evidence: false`; a `REAL_EXECUTION` result is not
hard-coded to block, but this repository has not produced one from real data.

## Validation evidence

Executed in the repository root on 2026-08-12:

```text
$ python -m pytest -q tests/test_round002_infrastructure.py
9 passed

$ python -m pytest -q
25 passed

$ ruff check src tests
All checks passed!

$ python -m compileall -q src tests
$ git diff --check
```

The ROUND-002 fixture suite exercises deterministic sampling/splits/E0 replay,
per-disposition group stratification, all three split boundaries, group-label
conflict, leakage assertion, metric regression, teacher/golden separation,
mixed-state rejection, confidence/note validation, split-manifest tampering,
and provenance tampering. These are synthetic contract tests only. Real E0 was
not run because this repository has no qualifying real human golden dataset;
the real-execution branch returns `BLOCKED_NO_GOLDEN_LABELS` only for that
absence, and executes a valid supplied golden dataset as `COMPLETED`.

## Handoff

Hand off to QA for independent regression, leakage, provenance, and E0
non-promotability checks. This report is implementation/test evidence only; it
does not change Round state or claim real-data validation.

## Technical Review repair pass

Following the risk-based review's `TR-B1`--`TR-B4` findings, the same module
was minimally hardened without adding a model, workflow, or external service:

- persisted split manifests now validate exact strategy config shape and replay
  the deterministic group-assignment algorithm before accepting assignments;
- sample manifests bind every sample record to immutable observation, CLEAN ID,
  exact-content key, and canonical source-lineage digest; annotation datasets
  carry and revalidate these bindings, canonical annotation ordering/count/state
  and content digest;
- `build_annotation_dataset(..., prior_annotations=())` is backward-compatible
  for candidate datasets and requires immutable, same-observation/sample
  candidate/reviewed predecessors for reviewed/golden records;
- metrics reject duplicate golden or prediction observation identities before
  joining; full schema-bearing inputs are content-address validated;
- prediction creation and provenance resolution close experiment dataset/split
  ID/hash links and invoke full split validation.

Repair validation on 2026-08-12:

```text
$ python -m pytest -q tests/test_round002_infrastructure.py
11 passed

$ python -m pytest -q
27 passed

$ ruff check src tests
All checks passed!

$ python -m compileall -q src tests
$ git diff --check
```

These results remain synthetic infrastructure evidence only. Technical Review
must independently revalidate the repair; this report does not change Round
state or claim real data/label validation.
