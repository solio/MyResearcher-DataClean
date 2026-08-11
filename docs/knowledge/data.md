# Data Knowledge

## Boundary

本项目只维护 Collector RAW -> DataClean CLEAN 的数据知识。ENRICHED、label、sentiment、eligible-for-analysis、aggregation 与训练切分属于下游，不在此设计。

## Confirmed facts

- `CONFIRMED — Collector schema/code inspection`：Collector SQLite v1/v2 的 `source_item_observations` 与 `raw_evidence` metadata 不可 UPDATE/DELETE；observation 通过 evidence links 保持 lineage。
- `CONFIRMED — Collector schema/code inspection`：SQLite v2 增加 `raw_body_state`，raw body 可处于 `PRESENT` 或 `PURGED`；DataClean 必须保留该状态，不能假装 body 一直存在。
- `CONFIRMED — user boundary`：CLEAN transformation 必须 deterministic、replayable、traceable，不能按财经语义改变或删除文本。
- `CONFIRMED — Collector schema/code inspection`：`observation_id` 是 immutable primary key，`(source, source_item_id, observation_version)` 唯一；这是 record identity 的根，normalized content digest 不是。
- `CONFIRMED — ROUND-001 corrected contract`：不同 observation 的 normalized title/content 相同时全部保留为 CLEAN；`exact_content_key` / `duplicate_content_of` 仅表示 deterministic relationship/group。
- `CONFIRMED — ROUND-001 corrected contract`：HTML 采用 preserve-by-default；layout-only/safe allowlisted markup 可做最小清理，`del/s/strike` 必须保留可恢复的 meaning-bearing structure，不引入 rich-text AST。
- `CONFIRMED — ROUND-001 corrected contract`：post-validation non-CLEAN outcome 保留 full available Collector lineage；只有 `INVALID_RECORD` 允许 best-effort lineage。
- `CONFIRMED — ROUND-001 AC-8 attempt`：真实 Eastmoney Collector SQLite 可以被 DataClean 只读执行且 DB hash 不变，但本次上游运行因 `SPEC_MISMATCH` 含 0 observations，不能用于真实内容抽样。

## Open questions

- 真实 Collector records 中各 normalization rule 的分布与误改风险（ROUND-001 AC-8）。
- 后续 source 是否需要 source-specific 的结构保真规则。
- exact-content relationship 之后是否有足够证据开启基础 near-duplicate Round；当前不假设算法。

## Maintenance

| 日期 | 变更 | Evidence Level |
| --- | --- | --- |
| 2026-08-07 | Bootstrap assumptions | PROVISIONAL |
| 2026-08-11 | 收窄为 RAW/CLEAN，记录 Collector SQLite v1/v2 与 retention 事实 | CONFIRMED |
| 2026-08-11 | 纠正 record/content identity、meaning-bearing HTML preservation 与 rejection lineage 契约 | CONFIRMED（CODE_INSPECTION + EXTERNAL_REVIEW） |
| 2026-08-11 | 记录真实 Collector DB 的 0-observation AC-8 探针与准确 blocker | CONFIRMED（REAL EXECUTION + READ-ONLY PROBE） |
