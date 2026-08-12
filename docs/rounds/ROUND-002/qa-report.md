# ROUND-002 Core QA Report

> Role: Core QA  
> Status: **QA_PASS / REVIEW_PASS_REVALIDATION / E0_BLOCKED_NO_GOLDEN_LABELS**  
> Date: 2026-08-12

## Scope and evidence boundary

## Repair QA revalidation

The prior `QA_FAIL / REVIEW_BLOCKED_REPAIR_PENDING` is historical evidence, not
the current QA result. Developer repaired the four Technical Review findings
with canonical sample bindings, an optional immutable prior-annotation registry,
strategy/config replay, duplicate identity rejection, and complete
experiment/dataset/split provenance closure. Core QA independently reran the
expanded matrix.

| Repair validation | Result |
| --- | --- |
| ROUND-002 suite | 11 passed |
| Full repository pytest | 27 passed |
| Ruff / compileall / `git diff --check` | passed / passed / passed |
| Rehashed split strategy/config/assignment tamper | rejected |
| sample membership and rehashed annotation lineage tamper | rejected |
| missing and cross-observation golden predecessor | rejected |
| duplicate gold/prediction metric identities | rejected |
| rehashed experiment dataset-hash provenance tamper | rejected |

This was `QA_REPAIR_PASS` at the QA handoff. The risk-based reviewer subsequently
revalidated leakage, reproducibility, metrics, and provenance and recorded
`REVIEW_PASS_REVALIDATION`; the prior pending status is superseded.

## Superseded Technical Review repair gate

The prior QA_PASS conclusion below is superseded. Technical Review identified
contract-bypass paths that the earlier matrix did not exercise. QA added the
minimal regression cases and reproduced four implementation failures:

| Review finding | Current QA result | Route |
| --- | --- | --- |
| self-consistent forged strategy/config/assignments accepted by split validator | RED | Developer |
| annotation not proven a member of the referenced sample manifest | RED | Developer / API-compatible provenance repair |
| duplicate observation IDs silently collapse in metrics | RED | Developer |
| self-consistent forged experiment dataset hash accepted by provenance resolver | RED | Developer |

Golden `supersedes_annotation_id` history validation is also required. Its
dedicated regression is staged behind the earlier sample-manifest failure in the
same test and will be reported separately after that repair. Full comparison of
annotation `source_record_lineage` against its sample's CLEAN snapshot cannot be
implemented from the frozen two-argument `build_annotation_dataset(manifest,
annotations)` alone: a manifest contains IDs, not sample snapshots. This is a
contract/API compatibility issue requiring a minimal optional or additional
validation input, not an excuse to omit the check.

No source, contract, state, or capability file was modified by QA. The earlier
validation evidence remains historical only. Do not use it to claim QA_PASS or
Technical Review PASS.

QA read the protocol, QA role, project/Round state, ROUND-002 contract and data
contract, acceptance, expected-RED evidence, developer report, production source,
and all tests. QA did not modify production code, the Round contract, state, or
the capability ledger.

All fixtures in `tests/test_round002_infrastructure.py` remain
`SYNTHETIC_TEST_ONLY`: they prove schemas, canonicalization, leakage, metrics and
replay properties only. They are not real Collector samples, human golden labels,
or promotable model evidence.

## Regression additions and repair loop

Independent QA added minimum regressions for: fatal mixed annotation state;
confidence/note validation; feasible disposition stratification; split manifest
tamper rejection in prediction/provenance paths; a qualified real-execution E0
path; input CLEAN schema/version/snapshot provenance; teacher-import content ID
and export binding; and the bounded E0 dependency.

The first audit correctly produced implementation RED for these requirements.
Developer repair was independently retested. The final ROUND-002 suite is 10
passed; this is the first repair loop for those implementation gaps.

## Superseded initial validation

| Test group | Result | Evidence type |
| --- | --- | --- |
| ROUND-002 contract/regression suite | 10 passed | SYNTHETIC / UNIT_TEST |
| Full repository pytest | 26 passed | UNIT_TEST / integration |
| Ruff (`ruff check src tests`) | passed | STATIC_CHECK |
| Compile (`python -m compileall -q src tests`) | passed | STATIC_CHECK |
| `git diff --check` | passed | STATIC_CHECK |
| Deterministic E0 replay | equal result; `SYNTHETIC_TEST_ONLY`, 3 predictions, metrics present | SYNTHETIC / REPLAY |
| Registry/static scope scan | registry exactly E0–E3; no E4, HTTP client/network, or teacher execution import found | STATIC_INSPECTION |

The replay result is explicitly non-promotable; it only verifies deterministic
runner behavior.

## Refreshed real Collector sampling and E0 blocker

QA used the only visible Collector database read-only:

```text
/Users/mac/Documents/trae_projects/MyResearcher/MyResearcher-DataCollector/
data/live-backfill-eastmoney-601012/collector.db
```

Input SHA-256 before and after execution was identical:

```text
6c4d3c7acff34acc731698ea260442a376dfdd6eb6c0472e9f26cb04996f4825
```

The database is Collector storage v2 and contained `0 source_item_observations`
(with one recorded collection failure). QA ran the ROUND-001 CLI into an isolated
temporary output directory, then sampled its CLEAN JSONL using seed `20260812`,
requested count `100`, and `exact_content_group` mode.

| Evidence | Result |
| --- | --- |
| ROUND-001 input/CLEAN/rejection counts | 0 / 0 / 0 |
| Real CLEAN artifact SHA-256 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Real sample manifest ID | `4a88913f3aed779bc23eb2c9f16933b0126f5c3eb7ea037b9c20b66eecab0822` |
| Real sample record count | 0 |
| `run_e0(..., execution_context="REAL_EXECUTION")` | `BLOCKED_NO_GOLDEN_LABELS` |
| Predictions / metrics | `[]` / `null` |

This is real infrastructure/blocker evidence, not a model result. It establishes
that the available empty sample is handled conservatively; it does not establish
model quality, validation on non-empty observations, or golden-label sufficiency.

## Superseded initial acceptance conclusion

The initial QA conclusion is superseded by the repair result above. The real
E0 status remains **BLOCKED_NO_GOLDEN_LABELS**. No Finance/Sentiment Expert was
invoked.
