# Rounds

- `ROUND-001/` — Collector Input Contract & Minimal Cleaning Baseline（历史：QA_PASS / REAL_DATA_BLOCKED）
- `ROUND-002/` — Dataset & Experiment Infrastructure（CLOSED；E0_BLOCKED_NO_GOLDEN_LABELS）
- `ROUND-003/` — Real-Data Pilot Sampling（PILOT_READY_FOR_RESEARCH_OWNER）

Round 档案存放目录。

当前状态以 `docs/state/current-round.md` 为准；ROUND-003 已完成 pilot handoff。

每个 Round 在这里建立 `ROUND-<NNN>/` 子目录，最少包含：

- Round Contract（`contract.md`，复制自 `docs/agent-system/templates/round-template.md`）
- lightweight acceptance 与验证记录
- 仅当发生责任切换时需要的 handoff
- 仅当触发 specialist 时需要的对应报告
