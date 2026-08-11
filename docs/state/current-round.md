# Current Round

- Round：**ROUND-001 — Collector Input Contract & Minimal Cleaning Baseline**
- 状态：**BLOCKED**（从 VALIDATING 进入）
- Contract：`docs/rounds/ROUND-001/contract.md`
- Acceptance / QA：AC-1–AC-7 PASS；`python -m pytest` 12 passed。
- Technical Review：PASS（core pipeline / dedup / lineage risk review）。
- Real Data：AC-8 BLOCKED；live smoke 报告引用的 80-record SQLite 已不可访问，仓库只有 synthetic fixtures。
- 恢复条件：提供一个实际 Collector SQLite v1/v2 数据库路径，或在 Collector 项目中另行授权并产出新的 bounded run；随后执行固定 CLI、统计和 before/after 抽样。
- Trigger：USER_TRIGGER（2026-08-11）。

最近更新：2026-08-11
