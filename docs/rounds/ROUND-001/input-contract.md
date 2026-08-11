# ROUND-001 Input and CLEAN Contract

状态：**CORRECTED — QA + TECHNICAL REVIEW PASS**
Evidence：`CONFIRMED — CODE_INSPECTION + TEST + REPRODUCIBLE CLI PROBE` of sibling `MyResearcher-DataCollector` SQLite v1/v2 and current DataClean implementation（2026-08-11）。本版 supersede 了把 exact-content equality 当作 record identity 的旧契约；当前验证证据为 `qa-correction-report.md` 与 `technical-review-correction.md`。

## Input transport

Round 001 不发明 JSON envelope；它只读 Collector SQLite database，支持 `PRAGMA user_version in {1, 2}` 的共同 observation/evidence 子集，并消费：

- `source_item_observations`：原始结构化 observation 与 Collector/parser/schema versions；
- `observation_evidence -> raw_evidence`：list/detail raw snapshot lineage；
- `observation_scopes`：requested scope/bar association。

数据库必须以 SQLite read-only URI 打开。v2 新增的 `raw_body_state` 属于 Collector retention，不改变 CLEAN 文本契约；DataClean 不写它。缺表、缺必需列、非法 JSON、未知 user_version 或 observation 无 raw evidence lineage 都是输入契约失败，禁止静默猜字段。

Collector 中 `observation_id` 是 `source_item_observations` 的 immutable primary key，`(source, source_item_id, observation_version)` 另有 unique constraint。Round 001 每个有序输入位置必须对应一个不重复的 `observation_id`；同一 identity 重复出现说明 adapter/input contract 被违反，必须明确失败，不得用内容 key 猜测或选择代表记录。

## Required observation fields

`observation_id`, `source`, `source_item_id`, `observation_version`, `observed_at_utc`, `published_at_utc`, `content`, `url`, `source_times_raw_json`, `source_metadata_json`, `fact_fingerprint`, `schema_version`, `collector_version`, `parser_version`，以及至少一条 raw evidence link。

Nullable 字段保持 nullable，不用空字符串、0、作者名或当前时间补造事实。

## CLEAN record

CLEAN record 包含：

- deterministic `clean_id` 与 `clean_schema_version`；
- 清理后的 `title` / `content`；
- source/item/observation identity、author、timestamps、URL、source metadata；
- `lineage`：Collector storage/schema/parser versions、fact fingerprint、drift link、scopes、raw evidence IDs/roles/hash/path/run；
- `cleaning`：`minimal.v1`、applied rules、input/output digests、deterministic `exact_content_key`，以及可空 `duplicate_content_of`。

CLEAN 不内嵌或覆盖 RAW body；它通过 immutable observation + raw evidence reference 保留证据链。

## HTML and text preservation

- NFC、leading BOM 和 whitespace normalization 只能做确定性 surface transformation。
- layout-only elements（例如 `br`、paragraph/list/table/block boundaries）可转为 whitespace/newline；子文本必须保留。
- 只有 Round 001 实现显式 allowlist 且 regression 证明安全的 presentation-only wrapper 才可移除 tag syntax；子文本不得移除或重排。带有未证明安全属性的 wrapper 不能自动当作 presentation-only。
- `del`、`s`、`strike` 是 meaning-bearing markup；CLEAN text 必须保留成对、可见、可恢复的 start/end markers 与其子文本（例如保留 canonical literal tags）。`<del>明天涨停</del> 明天跌停` 不得退化为 `明天涨停 明天跌停`。
- 未在 layout-only 或 tested-safe allowlist 中的 markup 默认原样/等价可恢复地 preserve，而不是 drop。Round 001 不引入 rich-text AST。

## Reject record

本轮 record-level 原因枚举：`INVALID_RECORD`、`EMPTY_CONTENT`。exact-content equality 不是 rejection reason。

- `INVALID_RECORD` 发生在记录无法通过 input validation 时；其 `lineage` 对输入对象中已存在的字段做 best-effort 保留，包括可用的 Collector storage/schema/collector/parser versions、fact fingerprint、drift reference、raw evidence 和 scopes，不补造缺失事实。
- 任何已通过 input validation、随后因 cleaning 产生的 non-CLEAN outcome（Round 001 中为 `EMPTY_CONTENT`）必须保留与 CLEAN 记录同等的 full available Collector lineage：`collector_storage_version`、`collector_schema_version`、`collector_version`、`parser_version`、`fact_fingerprint`、`drift_from_observation_id`、所有 raw evidence references 及其可用 retention metadata、所有 scopes。不得退化为只有 observation/source/item 的子集。
- 每条 rejection 保留 cleaning version、rule list、input/output digest（能计算时）和机器可读 detail。

## Record identity and exact-content relationship

- Record identity 是 Collector immutable `observation_id`；`source_item_id`、observation occurrence/version 及 evidence/scope lineage 都是该独立 observation 的事实，不能由文本内容替代。
- `minimal.v1` 对 normalization 后 `(title, content)` 的 canonical JSON 计算 SHA-256 `exact_content_key`。该 key 仅表示当前有序 batch 内的 exact-content group，不是 record ID。
- group 首条 CLEAN record 的 `duplicate_content_of` 为 null/省略；后续不同 observation 可指向同 group 的稳定首条 `clean_id`。不论是否写 predecessor reference，每个不同 `observation_id` 都必须输出 CLEAN。
- 该 relationship 不扩展到 near-duplicate 或 semantic duplicate，也不进行任何语义判断。

## Deterministic report semantics

- `input_count`：进入 record-level validation/cleaning 的有序 candidate 数；transport/schema-level fatal failure 中止运行，不伪造成功 report。
- `cleaned_count`：输出 CLEAN record 数，包括 exact-content group 中的每个独立 observation。
- `unchanged_count`：CLEAN record 中 normalization 前后 `(title, content)` byte-identical 且没有 text-changing rule 的数量。
- `modified_count`：CLEAN record 中 normalization 改变了 `(title, content)` 的数量。被拒绝记录不计入 unchanged/modified。
- `exact_content_duplicate_count`：CLEAN 中 `duplicate_content_of` 非空的数量，即每个 exact-content group 除稳定首条外的独立 observation 数量；它是 `cleaned_count` 的子集，不是 rejection 数。
- `rejected_count`：产生 record-level rejection 的 candidate 数。
- `reason_distribution`：按 reason 稳定排序的 rejection 计数映射，不含 exact-content group metadata。

成功 report 必须满足：

```text
input_count = cleaned_count + rejected_count
cleaned_count = unchanged_count + modified_count
exact_content_duplicate_count <= cleaned_count
sum(reason_distribution.values()) = rejected_count
```
