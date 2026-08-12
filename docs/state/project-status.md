# Project Status

状态：**NO_ACTIVE_ROUND / ROUND_002_CLOSED / E0_BLOCKED_NO_GOLDEN_LABELS**

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
- 未创建 ROUND-003 或其他新 Round。

维护者：Program Orchestrator
最近更新：2026-08-12
