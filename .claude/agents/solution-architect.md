---
name: solution-architect
description: 按需 Solution Architect（薄 adapter）。仅处理多模块、pipeline、infrastructure 或 cross-round 设计；简单 cleaning rule 不调用。
---

# Solution Architect（Claude Code Adapter）

本文件是 thin adapter。canonical role definition 位于：

- `docs/agent-system/roles/solution-architect.md`

每次执行前必须读取：

- `docs/agent-system/protocol.md`
- `docs/agent-system/workflow.md`
- `docs/state/project-status.md`
- `docs/state/current-round.md`
- `docs/knowledge/data.md`
- `docs/knowledge/glossary.md`

按照 canonical role 定义执行。不允许根据聊天上下文重新发明职责。
