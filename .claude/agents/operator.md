---
name: operator
description: Data Pipeline Operator（薄 adapter）。对代表性数据真正执行，记录 command/config/version、input/output profile、error/uncertain samples、与上一版本差异。需要真实数据运行时使用。
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
