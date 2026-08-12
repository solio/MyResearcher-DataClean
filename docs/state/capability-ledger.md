# Capability Ledger

能力登记表（契约见 `docs/agent-system/contracts/capability-contract.md`，成熟度定义见 `docs/agent-system/protocol.md`）。

| Capability ID | Description | Owner | Implementation Location | Validation Location | Maturity | Known Limitations | Last Validated Round |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAP-000 | Agent R&D Governance：多 Agent 研发组织、状态机、协议、契约、角色定义 | Program Orchestrator | docs/agent-system/ | 人工检查 | PROPOSED | 尚未经历真实 Round 运行验证 | — |
| CAP-001 | Collector SQLite RAW -> deterministic minimal CLEAN baseline（validation、conservative HTML/entity/whitespace、empty reason、exact-content relationship、full/best-effort lineage） | Developer / QA | `src/myresearcher_dataclean/` | `tests/`、`docs/rounds/ROUND-001/qa-correction-report.md`、`docs/rounds/ROUND-001/technical-review-correction.md`、`docs/rounds/ROUND-001/real-data-validation.md` | TESTED | 支持 Collector SQLite v1/v2 共同子集；真实 DB 只读探针仅含 0 observations，无法完成 AC-8 抽样，因此不是 DATA_VALIDATED | ROUND-001 |
| CAP-002 | CLEAN -> deterministic sample -> versioned annotation dataset -> group-aware saved split -> experiment/prediction artifacts -> disposition metrics；含 E0 executable runner | Developer / QA | `src/myresearcher_dataclean/research.py` | `tests/test_round002_infrastructure.py`、`docs/rounds/ROUND-002/qa-report.md`、`docs/rounds/ROUND-002/technical-review-revalidation.md` | TESTED | 真实 Collector 样本为 0 observations 且无 human golden；E0 为 `BLOCKED_NO_GOLDEN_LABELS`；E1--E3 仅 declaration-only；无模型质量或 DATA_VALIDATED 结论 | ROUND-002 |

> `DATA_VALIDATED` 必须有真实 Collector records 的统计与抽样证据；synthetic fixture 只能支持 `TESTED`。
