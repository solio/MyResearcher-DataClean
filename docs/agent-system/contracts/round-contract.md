# Round Contract

每个 Round 由 Orchestrator 从 `templates/round-template.md` 创建并确认，存放在 `docs/rounds/ROUND-<NNN>/contract.md`。

必须记录：Round ID、trigger、problem、why now、current evidence/unknowns、scope、out of scope、invariants、acceptance criteria、core owners、按需 specialist 及触发原因、测试与真实数据证据要求、关闭资产。

规则：

- Scope 与 Out of Scope 同时存在。
- Acceptance Criteria、invariants、fixtures/negative cases 必须在进入 `IMPLEMENTING` 前冻结。
- Specialist 为空是合法情况；未触发 specialist 不生成 gate。
- Scope 变化由 Orchestrator 记录原因并重新检查 QA acceptance。
- 关闭时补齐 evidence、capability changes、rejected ideas 和 next questions。
