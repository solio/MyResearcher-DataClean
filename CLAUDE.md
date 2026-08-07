@AGENTS.md

# Claude Code 项目规则

- 本项目在 Claude Code 下的项目 Agent 位于 `.claude/agents/`。
- `.claude/agents/` 中的 Agent 定义只是 **adapter**；canonical role definition 位于 `docs/agent-system/roles/`。
- Agent 每次执行都必须重新读取 canonical role definition，不得仅凭长会话历史继续任务。
- 新 Round 或重大阶段切换时，优先依赖仓库 handoff（`docs/rounds/` 与 Handoff Contract），而不是聊天上下文。
- 本文件不复制 AGENTS.md 与 `docs/agent-system/` 的内容；那里是唯一事实源。
