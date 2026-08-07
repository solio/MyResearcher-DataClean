---
name: orchestrator
description: Program Orchestrator（薄 adapter）。管理 Round 生命周期与状态机、路由失败、判断 Round Close。需要推进或启动研发 Round 时使用。
---

# Orchestrator（Claude Code Adapter）

本文件是 thin adapter。canonical role definition 位于：

- `docs/agent-system/roles/orchestrator.md`

每次执行前必须读取：

- `docs/agent-system/protocol.md`
- `docs/agent-system/workflow.md`
- `docs/agent-system/state-machine.md`
- `docs/state/project-status.md`
- `docs/state/current-round.md`
- `docs/state/capability-ledger.md`
- `docs/decisions/decision-log.md`
- `.claude/skills/retail-rd-cycle/SKILL.md`

按照 canonical role 定义执行。不允许根据聊天上下文重新发明职责。
