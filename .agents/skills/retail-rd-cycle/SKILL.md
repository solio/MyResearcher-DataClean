---
name: retail-rd-cycle
description: 研发 Round 编排 Skill（Codex 版本，业务含义与 Claude 版本一致）。Orchestrator 使用：读取状态 → 找到当前 Round → 按状态机选择 Agent → 不允许跳阶段 → QA fail 正确路由 → expert reject 正确路由 → Round close 更新 Knowledge/Capability/Backlog。当需要启动或推进一个研发 Round 时使用。
---

# Retail R&D Cycle（Codex Adapter Skill）

本 Skill 只定义 Orchestrator 如何运行一个研发 Round，**不执行研发本身**。业务含义与 `.claude/skills/retail-rd-cycle/SKILL.md` 完全一致。

## 运行步骤

1. 读取状态：`docs/state/project-status.md`、`docs/state/current-round.md`。
2. 找到当前 Round：`docs/rounds/`；无活跃 Round 时不得自行创建。
3. 按状态机选择 Agent（`docs/agent-system/state-machine.md`）。
4. 不允许跳阶段：检查前置 artifact 与不可跳过状态。
5. QA fail 正确路由（`docs/agent-system/protocol.md` Failure Routing）。
6. expert reject 正确路由（Expert Acceptance 分类）。
7. Round close 更新 Knowledge / Capability Ledger / Decision Log / Backlog，并归档 Round。

## Canonical References

- 工作流（canonical）：`docs/agent-system/workflow.md`
- 状态机：`docs/agent-system/state-machine.md`
- 共同协议：`docs/agent-system/protocol.md`

本 Skill 是薄 adapter，不复制上述文件内容。
