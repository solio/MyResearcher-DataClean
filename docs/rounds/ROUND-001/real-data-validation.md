# ROUND-001 AC-8 Real Collector Data Attempt

> Role：Program Orchestrator
>
> 状态：**AC-8 BLOCKED_NO_REAL_OBSERVATIONS**
>
> 日期：2026-08-11

## Dataset provenance

在 correction QA 与 risk-based Technical Review 均 PASS 后，工作区出现了新的真实
Collector SQLite：

```text
/Users/mac/Documents/trae_projects/MyResearcher/MyResearcher-DataCollector/data/live-backfill-eastmoney-601012/collector.db
```

Collector `runs/backfill-live-01/{execution,inspection,handoff}.md` 证明该库来自一次
`eastmoney_guba` / `601012` 真实网络运行，run ID 为
`3a714f1bbb364565839384eae6c76596`。运行未绕过身份核实页；首页因
`SPEC_MISMATCH / schema_mismatch` 按 Collector contract 停止。

DataClean 执行前的只读检查：

```text
SQLite user_version: 2
PRAGMA quick_check: ok
open file handles: none
database SHA-256: 6c4d3c7acff34acc731698ea260442a376dfdd6eb6c0472e9f26cb04996f4825

source_item_observations: 0
observation_evidence: 0
raw_evidence: 1
observation_scopes: 0
```

这是真实 Collector execution evidence，但不是包含可清理 observation records 的
dataset。唯一 raw evidence 是触发 schema mismatch 的 list response；DataClean 不把
Collector failure/evidence-only row 伪装成 observation。

## DataClean execution

对已静止数据库使用只读 adapter，并把输出写到 isolated temporary directory：

```text
PYTHONPATH=src python -m myresearcher_dataclean \
  /Users/mac/Documents/trae_projects/MyResearcher/MyResearcher-DataCollector/data/live-backfill-eastmoney-601012/collector.db \
  <isolated-output-dir>

exit: 0
artifacts: clean-records.jsonl, rejections.jsonl, run-report.json
clean-records.jsonl bytes: 0
rejections.jsonl bytes: 0
second isolated replay exit: 0
byte comparison: all three artifacts identical
```

`run-report.json` 的 corrected report fields：

```json
{
  "input_count": 0,
  "cleaned_count": 0,
  "unchanged_count": 0,
  "modified_count": 0,
  "exact_content_duplicate_count": 0,
  "rejected_count": 0,
  "reason_distribution": {}
}
```

四个 report invariants 对空 input 全部成立；两次独立输出的三个 artifacts 逐字节相同。
数据库两次执行后 SHA-256 仍为
`6c4d3c7acff34acc731698ea260442a376dfdd6eb6c0472e9f26cb04996f4825`，确认
RAW 未被修改。

## Acceptance decision

AC-8 仍为 **BLOCKED_NO_REAL_OBSERVATIONS**，不能评为 PASS：

- 没有 observation 可计算非零 unchanged/modified/content-relationship/rejection 分布；
- 没有 CLEAN 或 rejection 可进行 before/after/rules/lineage 人工抽样；
- 空数据集不能证明真实内容的误删、误改风险。

因此 ROUND-001 保持 `QA_PASS / REAL_DATA_BLOCKED`，CAP-001 保持 `TESTED`，不升级为
`DATA_VALIDATED`。恢复 AC-8 所需的不再是“找到任意 Collector DB”，而是一个已静止、
契约有效且至少含一条 `source_item_observations` 的真实 Collector SQLite。获得后应
重跑同一 CLI，记录全部 report fields，并抽样 modified/rejected/exact-content groups（如有）
及 unchanged records。
