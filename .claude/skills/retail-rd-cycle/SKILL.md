---
name: retail-rd-cycle
description: 研发 Round 编排 Skill。Program Orchestrator 使用：读取状态 → 找到当前 Round → 按状态机选择 Agent → 不允许跳阶段 → QA fail 正确路由 → expert reject 正确路由 → Round close 更新 Knowledge/Capability/Backlog。当需要启动或推进一个研发 Round 时使用。
---

# Retail R&D Cycle（Orchestrator Skill）

本 Skill 只定义 Orchestrator 如何运行一个研发 Round，**不执行研发本身**。

## 运行步骤

1. **读取状态**：读取 `docs/state/project-status.md` 与 `docs/state/current-round.md`。
2. **找到当前 Round**：读取 `docs/rounds/` 中当前 Round 契约。无活跃 Round 时，遵循 `docs/agent-system/state-machine.md` 中定义的 canonical Round Start Transition；本 Skill 不定义 Round 创建规则。
3. **按状态机选择 Agent**：依据 `docs/agent-system/state-machine.md` 确定当前状态应工作的角色，选择对应 adapter（`.claude/agents/`）。
4. **不允许跳阶段**：检查前置 artifact 与「不能跳过的状态」列表；不满足则路由回上游，不得推进。
5. **QA fail 正确路由**：按 `docs/agent-system/protocol.md` Failure Routing 分类（标签/规范/实现/测试本身），Two Repair Rule 计数，不一律回 Developer。
6. **expert reject 正确路由**：按 Expert Acceptance 分类（需求/领域/标签/架构/实现/数据/研究假设失败）路由回正确阶段。
7. **Round close 更新资产**：更新 Knowledge（`docs/knowledge/`）、Capability Ledger（`docs/state/capability-ledger.md`）、Decision Log（`docs/decisions/decision-log.md`）、Backlog（`backlog/`），并归档 Round。

## Canonical References

- 工作流：`docs/agent-system/workflow.md`
- 状态机：`docs/agent-system/state-machine.md`
- Round Start Transition（canonical，含 ROUND_START_TRIGGER）：`docs/agent-system/state-machine.md`
- 共同协议：`docs/agent-system/protocol.md`
- Round 模板：`docs/agent-system/templates/round-template.md`

本 Skill 不复制上述文件的内容；它们才是 canonical 定义。Round 创建策略由 state-machine.md 的 ROUND_START_TRIGGER 定义，本 Skill 不自行定义。
