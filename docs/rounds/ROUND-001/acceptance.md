# ROUND-001 Lightweight Acceptance Definition

状态：**FROZEN BEFORE IMPLEMENTATION** ｜ Owner：QA ｜ 2026-08-11

| AC | Expected behavior / negative case | Evidence | Status |
| --- | --- | --- | --- |
| AC-1 | 合法 Collector SQLite v1/v2 共同子集以只读方式读取；缺表/列、未知 user_version、坏 JSON、缺 lineage 明确失败 | integration tests | PASS |
| AC-2 | HTML/entity/BOM/NFC/whitespace 最小清理确定且记录 rule；不执行词义替换 | unit tests | PASS |
| AC-3 | URL、`@mention`、`$600519$`、重复感叹号及 `垃圾股，明天继续加仓` 可见语义信息保留 | semantic-preservation regression | PASS |
| AC-4 | title+content 清理后均为空时拒绝为 `EMPTY_CONTENT`；非法结构为 `INVALID_RECORD`，均有 lineage/reason | unit tests | PASS |
| AC-5 | 相同清理后 title+content 的后续条目为 `EXACT_DUPLICATE`，记录 `duplicate_of`，不做 near/semantic dedup | unit tests | PASS |
| AC-6 | 每条 CLEAN 含 versions、applied rules、digests、source/author/time/url/metadata、observation/raw evidence lineage | schema assertions | PASS |
| AC-7 | 相同 SQLite input + `minimal.v1` 两次执行的三个输出文件 byte-identical；报告含规定计数与 reason distribution | CLI replay test | PASS |
| AC-8 | 使用实际 Collector output 运行；统计 input/cleaned/unchanged/modified/rejected/duplicate/reasons，并抽样 before/after/reason 检查误删误改 | REAL_DATA report | BLOCKED_DATA_UNAVAILABLE |

## Fixtures

- Synthetic contract fixtures：正常、HTML/entity/whitespace、空文本、非法类型、exact duplicate、缺 raw evidence、Collector SQLite v1；另用上游当前 persistence 代码生成 v2 临时数据库。
- Semantic-preservation regression 只验证 cleaning operation 不破坏文本，不标注 bullish/bearish 或 sentiment。
- Real fixture：不得伪造。Collector committed fixtures 明确为 synthetic；live smoke 报告中的数据库路径当前不存在。

## Required real-data report

固定命令使用 `python -m myresearcher_dataclean <collector.db> <output-dir>`。报告必须记录 cleaning version、数据库 SHA-256、全部计数、reason distribution，并抽样比对 before/after/rules。取得实际 DB 前，AC-8 保持阻塞且 CAP-001 不高于 TESTED。
