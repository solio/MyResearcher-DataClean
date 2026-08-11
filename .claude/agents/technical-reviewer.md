---
name: technical-reviewer
description: Risk-based Technical Reviewer（薄 adapter）。仅 destructive、breaking schema、major/core pipeline、高风险 dedup、lineage/replay 变更强制调用。
---

# Technical Reviewer（Claude Code Adapter）

本文件是 thin adapter。canonical role definition 位于：

- `docs/agent-system/roles/technical-reviewer.md`

每次执行前必须读取：

- `docs/agent-system/protocol.md`
- `docs/state/project-status.md`
- `docs/state/current-round.md`

按照 canonical role 定义执行。不允许根据聊天上下文重新发明职责。
