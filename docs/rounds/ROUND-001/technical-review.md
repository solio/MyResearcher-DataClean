# ROUND-001 Risk-based Technical Review

> 状态：**SUPERSEDED — 2026-08-11 Correction Pass**
>
> 原因：外部 review 证明本报告错误接受了“content equality 即 record duplicate”的 rejection 语义，也未覆盖 `del/s/strike` meaning-bearing markup 丢失以及 post-validation rejection full-lineage 缺口。本文件保留为历史证据，不再构成任何 PASS 或 capability evidence。替代结论必须写入新的 `technical-review-correction.md`。

Trigger：core pipeline、exact dedup、lineage/replayability change。

历史结论：~~REVIEW_PASS_FOR_IMPLEMENTATION~~（已 supersede）。

Evidence Level：`CONFIRMED — CODE_INSPECTION + TEST`（2026-08-11）。

## Risk checks

- RAW safety：Collector DB 使用 SQLite `mode=ro` 并在 read transaction 中取得一致 snapshot；代码没有针对 Collector 的 DML。输出只写用户指定的独立 artifact。
- Schema/lineage：只接受 v1/v2 的冻结共同字段；未知版本、缺表/列、坏 JSON、缺 scope/evidence 直接失败。v2 `PRESENT/PURGED` raw-body state 被保留，不假装 raw body 一直存在。
- Determinism：稳定 SQL order、canonical JSON、固定 `minimal.v1`，不写当前时间或随机 ID；DB hash 与 consumed-record digest 都进入报告。
- Text safety：只做 surface normalization；未知 angle/script literal、URL、mention、stock code、否定/重复标点保留；没有 sentiment/finance classifier 或词义 drop rule。
- Dedup：只比较 normalization 后 title+content 的 exact SHA-256；稳定保留首条，后续 rejection 保留 `duplicate_of`、record metadata 和 RAW lineage；不实现 near/semantic dedup。
- Traceability：CLEAN 和 rejection 都记录 cleaning version、rules/reason、digests、Collector versions、observation/scope/raw evidence lineage。

## Non-blocking limitation

Round 001 保留 raw evidence path/hash/body state，但不接收 Collector raw-root 参数，因此不逐文件重新校验 raw body。该项不影响对 immutable structured observation 的最小清洗；若未来需要独立证据完整性审计，应另开明确 Round，不扩张本轮。

没有发现数据破坏、breaking schema、严重逻辑错误或安全 blocker。真实 record 未执行属于 acceptance evidence 缺失，不是实现缺陷。
