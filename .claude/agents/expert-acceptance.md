---
name: expert-acceptance
description: 按需 Expert Acceptance Coordinator（薄 adapter）。仅协调 Round 已触发的多个 specialist gate；普通 Round 由 Orchestrator 汇总。
---

# Expert Acceptance（Claude Code Adapter）

本文件是 thin adapter。canonical role definition 位于：

- `docs/agent-system/roles/expert-acceptance.md`

每次执行前必须读取：

- `docs/agent-system/protocol.md`
- `docs/state/project-status.md`
- `docs/state/current-round.md`
- `docs/knowledge/data.md`

按照 canonical role 定义执行。不允许根据聊天上下文重新发明职责。
