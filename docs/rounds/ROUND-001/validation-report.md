# ROUND-001 Validation Report

状态：**SUPERSEDED — HISTORICAL PRE-CORRECTION EVIDENCE** ｜ 2026-08-11

> 本报告的 12-test PASS 依赖了错误的 exact-content rejection 语义，且未覆盖
> meaning-bearing HTML 与完整 rejection lineage，不再构成当前 QA、Technical
> Review 或 capability evidence。本文件不删除，用于保留历史与失败模式；替代证据为
> `qa-correction-report.md` 与 `technical-review-correction.md`。

原阶段性结论：~~QA_PASS / REAL_DATA_BLOCKED~~（已 supersede）。

## Executed evidence

```text
python -m pytest
12 passed in 0.09s

ruff check src tests
All checks passed

python -m compileall -q src tests
exit 0

git diff --check
exit 0

PYTHONPATH=src python -m myresearcher_dataclean --help
exit 0
```

Evidence Level：`CONFIRMED — UNIT_TEST / INTEGRATION_TEST / CODE_INSPECTION`。

## Coverage

- Collector SQLite v1 contract fixture：只读读取、坏 schema/JSON、缺 evidence/scope lineage。
- 当前 sibling Collector SQLite v2 persistence：由上游 `SQLitePersistence` 生成临时 DB，DataClean 成功读取 observation、两个 raw evidence links、`PRESENT` retention state 并生成 CLEAN。
- Normalization：NFC、leading BOM、known HTML/entity、horizontal/newline whitespace；unknown angle text 和 script literal 保留。
- Semantic preservation regression：财经短句、重复标点、URL、mention、stock code 均不被语义规则改写。
- Invalid/empty/exact duplicate：机器可读 reason、duplicate_of、record metadata 与 lineage。
- Replay：同一 DB 两次输出 `clean-records.jsonl`、`rejections.jsonl`、`run-report.json` byte-identical；报告记录 DB 与 consumed records SHA-256。

上述数据内容均为 synthetic。它们证明可执行的 Collector -> DataClean storage boundary 与技术行为，不构成 REAL_DATA evidence。

## Real-data status

Collector 的 `runs/phase-02-live-smoke-01/execution-evidence.md` 记录 80 条真实 observations 和 160 evidence links，但其引用路径：

```text
/Users/mac/Documents/trae_projects/MyResearcher/live-smoke-data/eastmoney/phase2-live-smoke-01/collector.db
```

当前不存在；在工作区搜索也未找到其他 `collector.db`。上游 `tests/fixtures/eastmoney_guba/README.md` 明确说明 committed fixtures 是 synthetic，不能冒充真实样本。因此尚无可执行的 actual record dataset，无法诚实填写 input/cleaned/unchanged/modified/rejected/duplicate/reasons 或 before/after 人工抽样。

## Resume command

拿到一个已关闭、静止的 Collector SQLite v1/v2 数据库后执行：

```text
PYTHONPATH=src python -m myresearcher_dataclean <collector.db> <output-dir>
```

然后记录 `run-report.json` 的全部计数，并从 modified/rejected/duplicate 各抽样 before/after/rules。完成且无 semantic destruction 后，AC-8 才可 PASS，CAP-001 才可升级为 DATA_VALIDATED。
