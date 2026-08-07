# Round Contract

每个 Round 必须创建一份 Round Contract（复制 `templates/round-template.md` 填写）。
由 Solution Architect 起草，Orchestrator 确认后生效，存放在 `docs/rounds/ROUND-<NNN>/contract.md`。

## 必须记录字段

| 字段 | 说明 |
| --- | --- |
| Round ID | 如 ROUND-001 |
| Problem | 本轮要解决的问题 |
| Why Now | 为什么现在做（依据） |
| Current Knowledge | 引用的已有知识资产（docs/knowledge、决策日志） |
| Unknowns | 已知未知清单 |
| Hypotheses | 本轮假设（带 Evidence Level） |
| Scope | 本轮交付范围 |
| Out of Scope | 明确排除的内容 |
| Acceptance Criteria | 可验证的验收标准（开发前冻结） |
| Required Experts | 本轮需要的专家角色 |
| Execution Evidence | 执行证据要求 |
| Expert Acceptance | 专家验收记录 |
| New Knowledge | 本轮新增知识（关闭时填写） |
| Capability Changes | 能力成熟度变化（关闭时填写） |
| Rejected Ideas | 被否定的方案与原因 |
| Next Questions | 留给下一轮的问题 |

## 规则

- Scope 与 Out of Scope 必须同时存在。
- Acceptance Criteria 必须在进入开发前冻结。
- 没有 Round Contract 不允许进入 REQUIREMENTS_DESIGN 之后的状态。
- 变更 Scope 必须经 Orchestrator 确认并记录原因。
- 关闭 Round 时补齐 New Knowledge / Capability Changes / Rejected Ideas / Next Questions。
