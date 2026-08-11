# ROUND-001 Data Contract Correction Handoff

> Role：Data Architecture Expert
>
> 状态：**DATA_CONTRACT_DONE**
>
> 日期：2026-08-11

## Trigger and evidence

本记录是 ROUND-001 内的 contract correction，不是新 Round。触发项为 record/dedup identity、HTML semantic preservation 与 rejection lineage，符合 Data Architect 的按需 invocation 条件。

- `CONFIRMED — Collector schema/code inspection`：`source_item_observations.observation_id` 是 primary key，`(source, source_item_id, observation_version)` 有 unique constraint；observation 通过 `observation_evidence` 与 `observation_scopes` 关联 lineage。
- `CONFIRMED — DataClean code inspection`：修正前 `clean_records` 用 normalized `(title, content)` digest 驱逐后续 observation 并产生 `EXACT_DUPLICATE` rejection。
- `CONFIRMED — DataClean code inspection`：修正前 HTML extractor 把 `del/s/strike` 归入可直接移除的 inline tags，因而只保留子文本。
- `CONFIRMED — DataClean code inspection`：修正前所有 rejection 都调用 `_available_lineage`，使已通过 validation 的 `EMPTY_CONTENT` 也丢失 Collector/storage/parser/fingerprint/drift 字段。
- `CONFIRMED — EXTERNAL_REVIEW`：上述三项中前两项是 data-preservation blockers，第三项是 traceability blocker；原 Technical Review PASS 已 superseded。

## Corrected normative contract

1. **Identity is observation identity.** Record identity 仅取 Collector immutable `observation_id`。正常 SQLite 输入因 primary key 不会产生重复 identity；如 adapter/batch 重复交付同一 ID，必须作为 input-contract violation 明确失败，不用 content digest 猜测代表记录。
2. **Content equality is a relationship.** Normalized `(title, content)` 的 canonical SHA-256 是 `exact_content_key`。它可组成 batch-local exact-content group，后续成员可用 `duplicate_content_of` 指向稳定首条 CLEAN `clean_id`；所有不同 observations 都保留为 CLEAN。
3. **Meaning-bearing HTML survives.** Layout-only boundaries 可转 whitespace/newline，已显式 allowlist 且有 regression 证明的 presentation wrapper 可移除 tag syntax，但 child text 保留。`del/s/strike` 必须保留成对可见/可恢复 markers；未证明安全的 markup 默认 preserve。本轮不建 rich-text AST。
4. **Lineage depends on validation stage.** `INVALID_RECORD` 保留所有可用 lineage 但不补造缺字段。任何 post-validation non-CLEAN outcome 必须保留 full available storage/schema/collector/parser versions、fact fingerprint、drift reference、raw evidence 与 scopes，与 CLEAN lineage 对齐。
5. **Report counts observations, not unique text.** `input_count = cleaned_count + rejected_count`；`cleaned_count = unchanged_count + modified_count`；`exact_content_duplicate_count` 是 CLEAN 内后续 content-group 成员数，且 `<= cleaned_count`；`reason_distribution` 仅统计 rejection，其 value 之和等于 `rejected_count`。

## Contract/implementation mismatches handed off

Developer 必须修正：

- 移除基于 exact-content key 的 rejection/drop，改为每个 observation 输出 CLEAN 并记录 content-group metadata；
- 保留 `del/s/strike` 的可恢复结构，将非 safe allowlist markup 改为 preserve-by-default；
- post-validation rejection 使用 full lineage，`INVALID_RECORD` 的 best-effort helper 也要覆盖所有可用 lineage keys；
- 将 report 的 `duplicate_count` 替换为上述 `exact_content_duplicate_count` 语义，并强制计数等式。

QA 必须在实现前冻结 regression/acceptance，至少覆盖：两个不同 `observation_id` 但 normalized content 相同时产生两条 CLEAN；`del/s/strike` 删除关系可恢复；`EMPTY_CONTENT` full lineage 与 `INVALID_RECORD` best-effort lineage；report 等式与 deterministic replay。

## Non-goals

本 correction 不引入 near/semantic duplicate、rich-text AST、source-specific parser、新 workflow/agent/phase/governance layer，也不调用 Finance/Sentiment Expert。真实 Collector database 验证仍属 AC-8，但必须在 correction QA 与 risk-based Technical Review 重新 PASS 后才能恢复为唯一 blocker。
