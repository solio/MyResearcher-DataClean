# ROUND-002 Core QA — Expected RED Evidence

> Role：Core QA  
> 状态：**EXPECTED_RED / BUG_ROUTED**  
> 日期：2026-08-12

## Test design scope

QA read `AGENTS.md`, the QA role, project/current state, ROUND-002 contract and
Data Contract before production implementation. No Finance/Sentiment Expert is in this
Round. The acceptance matrix is frozen in `acceptance.md`; production code, state,
capability and contracts were not modified by QA.

`tests/test_round002_infrastructure.py` adds seven synthetic contract regressions. Its
fixtures contain complete but explicitly `SYNTHETIC_TEST_ONLY` ROUND-001 CLEAN lineage
snapshots. They do not claim an actual Collector observation or human review.

## Baseline

```text
$ python -m pytest
16 passed
```

The baseline covers ROUND-001 only and does not implement any ROUND-002 public API.

## Frozen expected failures

| AC | Test | Expected pre-implementation failure | Routing |
| --- | --- | --- | --- |
| AC-1 | sampler/filter/full-lineage regression | `ModuleNotFoundError: myresearcher_dataclean.research` | Developer — missing infrastructure |
| AC-2 | annotation/state/teacher/prediction separation regression | same | Developer — missing infrastructure |
| AC-3 | random/time/source split and leakage regression | same | Developer — missing infrastructure |
| AC-4 | hand-calculated unified metrics regression | same | Developer — missing infrastructure |
| AC-5 | manifest/prediction/provenance resolver regression | same | Developer — missing infrastructure |
| AC-6 | deterministic synthetic-only E0 plus real-data blocker regression | same | Developer — missing infrastructure |
| AC-7 | E0–E3 registry/no-E4 regression | same | Developer — missing infrastructure |

The RED run must not be bypassed with skips, `importorskip`, placeholder outputs, or
synthetic labels reclassified as real golden evidence.

## Handoff

Developer implements the frozen public API and no additional candidate/model route. After
implementation, QA will run full pytest, static checks, replay/leakage/metrics/provenance
regressions and inspect that E0's synthetic test branch remains non-promotable while the
real-golden absence is exactly `BLOCKED_NO_GOLDEN_LABELS`.
