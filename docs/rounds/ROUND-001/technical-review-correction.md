# ROUND-001 Risk-based Technical Review — Correction Pass

> Role：Technical Completion Reviewer
>
> 状态：**REVIEW_PASS_CORRECTION**
>
> 日期：2026-08-11

## Trigger and review boundary

本报告属于现有 `ROUND-001 — Collector Input Contract & Minimal Cleaning Baseline` 的
contract correction，不是新 Round。触发风险为 dedup/record identity、core pipeline、
lineage/replayability 与 semantic preservation change。

审查以 `contract.md`、`input-contract.md`、`data-contract-correction.md`、
`acceptance.md`、`qa-correction-red.md`、`developer-correction.md` 与
`qa-correction-report.md` 为当前证据，并独立检查 production source、全部 tests 和核心 CLI。
Finance / Sentiment Expert 未调用。

旧 `technical-review.md` 的 PASS 已被 external correction evidence 推翻；该文件只保留为
负面历史证据。本报告明确 supersede 旧结论，旧结论不得继续支持 acceptance、state 或
capability maturity。

Evidence level：`CONFIRMED — CODE_INSPECTION + TEST + REPRODUCIBLE CLI PROBE`。

## Risk findings

### 1. Record identity and exact-content relationship — PASS

- `pipeline.py::_require_unique_observation_ids` 在任何 record-level processing 前检查非空
  `observation_id`；同一 immutable identity 在有序 batch 重复交付时明确抛出 input-contract
  failure，不按文本内容选择代表记录。
- `pipeline.py::clean_records` 只把 normalized `(title, content)` digest 用作
  `exact_content_key`。不同 observations 的相同 key 不触发 reject/drop；每个 observation
  都产生独立 CLEAN，稳定后续成员以 `duplicate_content_of` 指向组内首条 `clean_id`。
- `clean_id` 包含 `observation_id` 与 `fact_fingerprint`，因此 content equality 不会合并
  record identity。production rejection reason 只剩 `INVALID_RECORD` / `EMPTY_CONTENT`，
  不存在 `EXACT_DUPLICATE` path。

定向 regression 确认两个不同 `observation_id` / source items 的同内容 occurrence 均为
CLEAN，key 相同且 predecessor reference 稳定；重复同一 `observation_id` 明确失败。

### 2. Meaning-bearing HTML preservation — PASS

- `normalization.py::_ConservativeHTMLTextExtractor` 只对无属性 layout-only tags 转换边界
  whitespace/newline，只对无属性 `_SAFE_PRESENTATION_TAGS` 移除 wrapper syntax，并始终保留
  child text。
- `del` / `s` / `strike`、unknown tags，以及带未证明属性的 presentation/layout tags 进入
  preserve path；start/end markers 与 child text 保留。独立 probe 复核了三类删除/划除 tag、
  attributed `b` / `div` 与 unknown `signal`，结果均保留可恢复 marker。
- semantic fixture 中 URL、mention、stock code、重复标点与财经文本未被词义规则改写；代码
  中没有 Finance/Sentiment classifier、near duplicate 或 semantic drop rule。

定向 regressions 覆盖 `del/s/strike`、unknown markup、attributed markup、layout-only 与 safe
wrapper 的最小处理。未发现当前 contract 内的 destructive text transformation。

### 3. Rejection lineage and v2 retention state — PASS

- post-validation `EMPTY_CONTENT` 显式使用 `_full_lineage`，实际保存
  `collector_storage_version`、`collector_schema_version`、`collector_version`、
  `parser_version`、`fact_fingerprint`、`drift_from_observation_id`、observation/source/item
  identity、原样 deep-copy 的 `raw_evidence` 与 `scopes`。
- `INVALID_RECORD` 使用 `_available_lineage`，对输入中存在的同类字段做 best-effort copy，
  不补造缺失事实。rejection 同时保存 reason、detail、rules 与可计算的 input/output digest。
- Collector v2 adapter 从 `raw_body_state` 暴露并强制验证 `body_state in
  {PRESENT, PURGED}`，同时携带 `body_purged_at_utc`；pipeline 对 evidence dictionary 原样
  deep-copy。QA regression 对 `PRESENT` 与 `PURGED` 均有 lineage assertion；当前 sibling
  Collector persistence integration 也确认 CLEAN lineage 保留 v2 `PRESENT` state。

以上结论只声称代码实际保存的字段；没有声称 DataClean 内嵌 RAW body 或重新校验 evidence
filesystem body。

### 4. Reporting semantics — PASS

成功 report 固定包含 `input_count`、`cleaned_count`、`unchanged_count`、
`modified_count`、`exact_content_duplicate_count`、`rejected_count` 与
`reason_distribution`。实现与 mixed regression 均确认：

```text
input_count = cleaned_count + rejected_count
cleaned_count = unchanged_count + modified_count
exact_content_duplicate_count <= cleaned_count
sum(reason_distribution.values()) = rejected_count
```

`exact_content_duplicate_count` 只计 CLEAN content group 稳定首条之后的成员，是
`cleaned_count` 子集；content relationship 不进入 rejection 或 reason distribution。

### 5. Determinism, core entry point and RAW safety — PASS

- Python replay 对相同有序 input 两次产生相等 result；CLI replay 对相同 SQLite input 的
  `clean-records.jsonl`、`rejections.jsonl` 与 `run-report.json` 产生 byte-identical output。
- SQLite adapter 使用 `mode=ro` URI、稳定 SQL order 与 read transaction；DataClean source
  没有对 Collector database 的 DML。独立 v1 CLI probe 返回 `rc=0`，生成三个规定 artifact，
  且输入 database SHA-256 在执行前后相同。
- canonical JSON、SHA-256 identity/digest、固定 `minimal.v1` 与无 wall-clock/random output
  支持 replayability。v1 fixture 与当前 sibling Collector v2 persistence integration 均通过；
  这些仍是 synthetic contract evidence，不冒充 AC-8 real-data evidence。

## Independent verification

```text
$ python -m pytest
................                                                         [100%]
16 passed in 0.08s

$ python -m pytest -q <11 correction / replay / v1-v2 integration nodes>
...........                                                              [100%]

$ python -m ruff check src tests
All checks passed!

$ python -m compileall -q src tests
PASS

$ git diff --check
PASS

$ <independent v1 CLI read-only probe>
{'rc': 0, 'db_unchanged': True,
 'artifacts': ['clean-records.jsonl', 'rejections.jsonl', 'run-report.json']}
```

定向 nodes 覆盖 distinct-observation retention、duplicate identity failure、
`del/s/strike`、unknown/attributed markup、full/best-effort lineage、mixed report equations、
Python replay、CLI byte replay、Collector v1 read 与当前 Collector v2 persistence integration。

## Review decision and handoff

结论：**REVIEW_PASS_CORRECTION**。

修正后的 dedup semantics、core pipeline、lineage、semantic preservation、reporting、
deterministic replay 与 RAW read-only 风险均按当前 Round contract 受控；未发现当前需求内的
data-destruction、安全或明显逻辑 blocker。本报告满足恢复
`QA_PASS / REAL_DATA_BLOCKED` 的 Technical Review 前置 gate，但不自行更新
`docs/state/` 或 capability evidence；由 Program Orchestrator 统一收尾。

Technical Review 交接时 AC-8 仍为 **BLOCKED_DATA_UNAVAILABLE**。后续 Orchestrator
在 `real-data-validation.md` 中对新出现的真实、静止 Collector SQLite 完成只读探针；
该库上游运行因 `SPEC_MISMATCH` 含 0 observations，因此 AC-8 精确更新为
**BLOCKED_NO_REAL_OBSERVATIONS**。该探针不改变本报告对 AC-1–AC-7 的 correction PASS，
也不能替代真实内容统计与 before/after 抽样、不能把 CAP-001 提升为
`DATA_VALIDATED`。
