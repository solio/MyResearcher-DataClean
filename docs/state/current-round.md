# Current Round

- 当前 Round：**ROUND-003 — Real-Data Pilot Sampling**。
- 状态：**PILOT_READY_FOR_RESEARCH_OWNER**。
- Input：35 天 backfill 的真实 Collector SQLite，8251 observations，`list_title`。
- Output：300 unique real observations；JSONL、CSV、profile 已生成并通过 QA。
- Boundary：本 Round 到 `Collector DB -> deterministic sampler -> pilot-300 -> QA` 即停止。
- 不得在本 Round 自动进入 annotation、golden、teacher、E0/E1/E2/E3、模型或 ROUND-004。
- ROUND-002：保留 `CLOSED — INFRASTRUCTURE_ACCEPTED / E0_BLOCKED_NO_GOLDEN_LABELS` 历史状态。
- ROUND-001：保留 `QA_PASS / REAL_DATA_BLOCKED` 历史状态和未完成 AC-8。

最近更新：2026-08-12
