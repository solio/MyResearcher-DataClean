# ROUND-001 Lightweight Acceptance Definition

状态：**QA_PASS / REAL_DATA_BLOCKED** ｜ Owner：QA / Program Orchestrator ｜ 2026-08-11

> 本文件是在同一 ROUND-001 内冻结的 correction acceptance。旧版 AC-5 将
> normalized content equality 当作 record identity，并把后续 observation 作为
> `EXACT_DUPLICATE` rejection；该结论及依赖它的旧 PASS 已被本版明确
> supersede。旧 AC-2/3 对 meaning-bearing HTML 的覆盖、旧 AC-4 对
> post-validation rejection lineage 的约束、旧 AC-7 的 report 字段也不充分。
> 本版 correction 已由 QA 独立复验，并由 risk-based Technical Reviewer
> 重新 PASS；证据见 `qa-correction-report.md` 与
> `technical-review-correction.md`。旧 PASS 仍仅作 superseded 历史证据。

| AC | Corrected expected behavior / negative case | Evidence required | Correction status |
| --- | --- | --- | --- |
| AC-1 | 合法 Collector SQLite v1/v2 共同子集以只读方式读取；缺表/列、未知 `user_version`、坏 JSON、缺 raw evidence/scope lineage 明确失败。一个有序 batch 内重复交付同一 `observation_id` 是 input-contract failure，必须明确中止，不能按 content key 选择代表记录 | SQLite integration tests；duplicate-identity regression | **PASS — QA correction validation** |
| AC-2 | NFC、leading BOM、entity、layout-only HTML 与 whitespace 的最小清理确定且记录 rule；只可剥离经显式 allowlist 证明安全的 presentation wrapper，不执行词义替换 | normalization unit tests | **PASS — QA correction validation** |
| AC-3 | `del` / `s` / `strike` 的 start/end relationship 和子文本以可见、成对、可恢复形式保留；未知/未证明安全的 markup 默认 preserve。URL、`@mention`、`$600519$`、重复标点及 `垃圾股，明天继续加仓` 等可见信息不被语义规则改写 | meaning-bearing HTML 与 semantic-preservation regressions | **PASS — QA correction validation** |
| AC-4 | title+content 清理后均为空时产生 `EMPTY_CONTENT`；非法结构产生 `INVALID_RECORD`；两者均有机器可读 reason/detail/rules/digests（可计算时）。`EMPTY_CONTENT` 等 post-validation non-CLEAN outcome 保留 full available Collector lineage；`INVALID_RECORD` best-effort 保留输入中所有可用同类 lineage 字段且不补造事实 | rejection + lineage schema assertions | **PASS — QA correction validation** |
| AC-5 | Record identity 仅由 immutable `observation_id` 决定。不同 observation/source item/occurrence 即使 CLEAN `(title, content)` 完全相同也各自产生 CLEAN record；deterministic `exact_content_key` 只表达 content group，后续成员可用 `duplicate_content_of` 指向稳定首条 CLEAN，绝不产生 content-equality rejection/drop。禁止 near/semantic dedup | duplicate-occurrence regression；negative identity case | **PASS — QA correction validation** |
| AC-6 | 每条 CLEAN 含 versions、applied rules、input/output digests、`exact_content_key`、source/author/time/url/metadata、observation/raw evidence/scopes lineage；所有修改、relationship 与 rejection 可解释 | CLEAN/rejection schema assertions | **PASS — QA correction validation** |
| AC-7 | 相同有序 input + `minimal.v1` 两次执行产生相等 Python result；同一 SQLite 输入的三个输出文件 byte-identical。report 固定包含 `input_count`、`cleaned_count`、`unchanged_count`、`modified_count`、`exact_content_duplicate_count`、`rejected_count`、`reason_distribution`，并满足本文件下列计数关系 | pipeline + CLI deterministic replay；report invariant assertions | **PASS — QA correction validation** |
| AC-8 | 在 AC-1–AC-7 QA PASS 且 risk-based Technical Review 重新 PASS 后，使用实际 Collector output 运行；统计全部 corrected report fields，并抽样 before/after/reason 检查误删误改 | REAL_DATA report | **BLOCKED_NO_REAL_OBSERVATIONS — 真实 DB 探针为 0 observations，无法抽样** |

## Mandatory report semantics

- `input_count`：进入 record-level validation/cleaning 的有序 candidates 数量。
- `cleaned_count`：输出 CLEAN observations 数量，包含 exact-content group 中的每个独立 observation。
- `unchanged_count` / `modified_count`：只划分 CLEAN records；按 normalization 是否改变 `(title, content)` 判定。
- `exact_content_duplicate_count`：CLEAN records 中 exact-content group 稳定首条之后的成员数，是 `cleaned_count` 子集，不是 rejection。
- `rejected_count`：record-level rejection 数量。
- `reason_distribution`：只统计 rejection reason，不包含 exact-content relationship。

每个成功 report 必须满足：

```text
input_count = cleaned_count + rejected_count
cleaned_count = unchanged_count + modified_count
exact_content_duplicate_count <= cleaned_count
sum(reason_distribution.values()) = rejected_count
```

## Frozen correction fixtures

- 两个不同 `observation_id`、不同 `source_item_id`、不同 occurrence，normalization 后 title/content 相同：两条都 CLEAN；稳定后者带 `duplicate_content_of`，`exact_content_duplicate_count = 1`、`rejected_count = 0`。
- 同一 `observation_id` 在一个 batch 重复交付且 content 不同：明确 input-contract failure；不得凭 content 选出任一代表。
- `<del>明天涨停</del> 明天跌停`、`<s>旧值</s>`、`<strike>旧结论</strike>`：三类关系都可恢复；unknown markup 的 start/end marker 和 child text 保留。
- `EMPTY_CONTENT`：断言 storage/schema/collector/parser versions、fact fingerprint、drift reference、raw evidence（含 retention metadata）与 scopes 完整保留。
- `INVALID_RECORD`：输入中可用的上述同类 lineage 字段均 best-effort 保留。
- 混合 unchanged、modified、exact-content relationship、`EMPTY_CONTENT`、`INVALID_RECORD` 的 batch：断言所有 report 字段、等式及 deterministic replay。

Fixtures 全部是 synthetic contract fixtures，只能证明 contract behavior，不能替代 AC-8 real-data evidence。Finance/Sentiment classification 不在测试或本 Round scope 内。

## Re-validation gate

Developer 完成后，QA 必须执行 full pytest、lint/static checks、deterministic replay、duplicate-occurrence、meaning-bearing HTML 和 lineage regressions。只有这些通过且 risk-based Technical Review 重新 PASS，状态才可恢复为 `QA_PASS / REAL_DATA_BLOCKED`；此前不得声称 real data unavailable 是唯一 blocker。

QA correction validation 与 risk-based Technical Review correction 均已完成并通过；
`qa-correction-report.md` 记录 full suite、定向 regressions、lint/static、compile 与
diff evidence，`technical-review-correction.md` 记录独立风险复核。当前已恢复
`QA_PASS / REAL_DATA_BLOCKED`。后续 `real-data-validation.md` 记录了真实 Collector DB
的安全探针；该库因上游 schema mismatch 含 0 observations，所以仍不构成 AC-8
PASS evidence。
