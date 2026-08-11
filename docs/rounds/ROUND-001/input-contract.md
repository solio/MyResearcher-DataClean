# ROUND-001 Input and CLEAN Contract

状态：**FROZEN FOR ROUND-001**
Evidence：`CONFIRMED — CODE_INSPECTION` of sibling `MyResearcher-DataCollector` SQLite v1/v2（2026-08-11）。

## Input transport

Round 001 不发明 JSON envelope；它只读 Collector SQLite database，支持 `PRAGMA user_version in {1, 2}` 的共同 observation/evidence 子集，并消费：

- `source_item_observations`：原始结构化 observation 与 Collector/parser/schema versions；
- `observation_evidence -> raw_evidence`：list/detail raw snapshot lineage；
- `observation_scopes`：requested scope/bar association。

数据库必须以 SQLite read-only URI 打开。v2 新增的 `raw_body_state` 属于 Collector retention，不改变 CLEAN 文本契约；DataClean 不写它。缺表、缺必需列、非法 JSON、未知 user_version 或 observation 无 raw evidence lineage 都是输入契约失败，禁止静默猜字段。

## Required observation fields

`observation_id`, `source`, `source_item_id`, `observation_version`, `observed_at_utc`, `published_at_utc`, `content`, `url`, `source_times_raw_json`, `source_metadata_json`, `fact_fingerprint`, `schema_version`, `collector_version`, `parser_version`，以及至少一条 raw evidence link。

Nullable 字段保持 nullable，不用空字符串、0、作者名或当前时间补造事实。

## CLEAN record

CLEAN record 包含：

- deterministic `clean_id` 与 `clean_schema_version`；
- 清理后的 `title` / `content`；
- source/item/observation identity、author、timestamps、URL、source metadata；
- `lineage`：Collector storage/schema/parser versions、fact fingerprint、drift link、scopes、raw evidence IDs/roles/hash/path/run；
- `cleaning`：`minimal.v1`、applied rules、input/output digests、exact duplicate key。

CLEAN 不内嵌或覆盖 RAW body；它通过 immutable observation + raw evidence reference 保留证据链。

## Reject record

原因枚举：`INVALID_RECORD`、`EMPTY_CONTENT`、`EXACT_DUPLICATE`。每条 rejection 保留可用 identity/lineage、cleaning version、rule list 和细节；duplicate 额外记录首条 `clean_id`。

## Exact duplicate identity

`minimal.v1` 对 NFC/HTML/entity/whitespace 处理后的 `(title, content)` 做 canonical JSON SHA-256。只在一次确定性 batch 内去重；按稳定 observation 顺序保留第一条。它不是 near-duplicate，也不判断文本意义。
