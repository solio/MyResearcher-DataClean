---
name: expert-acceptance
description: Expert Acceptance Coordinator（薄 adapter）。组织三位专家对真实输出独立验收，拒绝后分类并路由回正确阶段。需要组织专家验收时使用。
---

# Expert Acceptance（Claude Code Adapter）

本文件是 thin adapter。canonical role definition 位于：

- `docs/agent-system/roles/expert-acceptance.md`

每次执行前必须读取：

- `docs/agent-system/protocol.md`
- `docs/state/project-status.md`
- `docs/state/current-round.md`
- `docs/knowledge/finance.md`
- `docs/knowledge/sentiment.md`
- `docs/knowledge/data.md`

按照 canonical role 定义执行。不允许根据聊天上下文重新发明职责。
