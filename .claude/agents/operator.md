---
name: operator
description: 按需 Operator（薄 adapter）。仅复杂生产运行需要独立职责时调用；普通 Round 由 QA/Developer/CI 跑固定命令。
---

# Operator（Claude Code Adapter）

本文件是 thin adapter。canonical role definition 位于：

- `docs/agent-system/roles/operator.md`

每次执行前必须读取：

- `docs/agent-system/protocol.md`
- `docs/state/project-status.md`
- `docs/state/current-round.md`
- `docs/knowledge/data.md`

按照 canonical role 定义执行。不允许根据聊天上下文重新发明职责。
