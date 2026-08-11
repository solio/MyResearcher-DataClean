# Data Knowledge

## Boundary

本项目只维护 Collector RAW -> DataClean CLEAN 的数据知识。ENRICHED、label、sentiment、eligible-for-analysis、aggregation 与训练切分属于下游，不在此设计。

## Confirmed facts

- `CONFIRMED — Collector schema/code inspection`：Collector SQLite v1/v2 的 `source_item_observations` 与 `raw_evidence` metadata 不可 UPDATE/DELETE；observation 通过 evidence links 保持 lineage。
- `CONFIRMED — Collector schema/code inspection`：SQLite v2 增加 `raw_body_state`，raw body 可处于 `PRESENT` 或 `PURGED`；DataClean 必须保留该状态，不能假装 body 一直存在。
- `CONFIRMED — user boundary`：CLEAN transformation 必须 deterministic、replayable、traceable，不能按财经语义改变或删除文本。
- `CONFIRMED — ROUND-001 contract`：exact duplicate 使用 cleaning versioned identity；被 deduplicated 的 observation 仍保留 reason、metadata 与 RAW lineage。

## Open questions

- 真实 Collector records 中各 normalization rule 的分布与误改风险（ROUND-001 AC-8）。
- 后续 source 是否需要 source-specific 的结构保真规则。
- exact duplicate 之后是否有足够证据开启基础 near-duplicate Round；当前不假设算法。

## Maintenance

| 日期 | 变更 | Evidence Level |
| --- | --- | --- |
| 2026-08-07 | Bootstrap assumptions | PROVISIONAL |
| 2026-08-11 | 收窄为 RAW/CLEAN，记录 Collector SQLite v1/v2 与 retention 事实 | CONFIRMED |
