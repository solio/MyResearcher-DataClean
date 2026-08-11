# Current Round

- Round：**ROUND-001 — Collector Input Contract & Minimal Cleaning Baseline**
- 状态：**QA_PASS / REAL_DATA_BLOCKED**（current-Round correction 已完成；未创建新 Round）
- Correction chain：Orchestrator -> Data Architect -> QA -> Developer -> QA -> risk-based Technical Reviewer。
- Correction result：record identity/content relationship、`del/s/strike` 与 preserve-by-default、post-validation lineage、reporting semantics 已修正；full QA 与重新 risk-based Technical Review 均 PASS。
- Prior QA / Technical Review：**SUPERSEDED**，不得作为当前 PASS evidence；当前 evidence 为 `qa-correction-report.md` 与 `technical-review-correction.md`。
- Finance/Sentiment Expert：不调用。
- AC-8：**BLOCKED_NO_REAL_OBSERVATIONS**；修正 gates 均已 PASS。新发现的真实、静止 Collector SQLite 已安全执行，但因上游 `SPEC_MISMATCH` 只含 raw failure evidence 且 observations 为 0；当前唯一 blocker 是缺少可抽样的真实 observation records。
- Trigger：ROUND-001 内部 correction（2026-08-11 external review）；Round ID 不变。

最近更新：2026-08-11
