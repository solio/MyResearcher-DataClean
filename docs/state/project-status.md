# Project Status

状态：**ROUND_003_PILOT_READY_FOR_RESEARCH_OWNER**

- ROUND-003 已从真实 35 天 Collector backfill 生成 300 条 unique pilot observations 并通过 QA。
- ROUND-003 只交付 pilot 给 Research Owner；不做 annotation、model、training 或 experiment。
- ROUND-002 的 dataset 与 experiment infrastructure 已满足 AC-1--AC-8 并关闭。
- ROUND-001 deterministic cleaner 保持 CAP-001 `TESTED`；其真实内容 AC-8 仍因 0 observations 未完成。
- ROUND-002 新增 CAP-002 `TESTED`：deterministic sampling、versioned annotation、
  group-aware split、metrics、artifact provenance 与 E0 runner。
- Core QA 为 `QA_PASS`；risk-based Technical Review 修复复验为
  `REVIEW_PASS_REVALIDATION`。首次 `REVIEW_BLOCKED` 永久保留为修复历史。
- 研究决策保持冻结：`KEEP/EXCLUDE/REVIEW` + multi-label reasons，registry 仅 E0--E3，
  E1--E3 declaration-only，E4 未实现。
- 当前无真实 human golden labels且可见 Collector DB 为 0 observations；E0 精确
  `BLOCKED_NO_GOLDEN_LABELS`，未生成 predictions/metrics，不声称 `DATA_VALIDATED`。
- ROUND-003 completion boundary 已到达；未创建 ROUND-004。

维护者：Program Orchestrator
最近更新：2026-08-12
