# AGENTS.md

本文件是整个 Git 仓库对**所有 AI 执行器**（Claude Code、Codex 等）的最高级项目约束。

## 项目是什么

中文 A 股社区（东方财富股吧、雪球、微博等）数据清洗与散户情绪研究项目。
长期目标是建立数据清洗、立场/情绪/行为意图识别与聚合分析能力，并持续用真实数据、实验、QA 和专家验收检验其研究价值。

## 这是多轮演进项目

- 项目以 Round 为单位演进：需求研究 → 架构 → QA 测试设计 → Developer ↔ QA → 技术审查 → 真实数据执行 → 专家验收 → 下一 Round。
- 不允许假设一次设计即可完成整个项目。
- 不允许把「代码能跑 + 测试通过」当作「专家验收通过」。

## 来源与状态

- `docs/agent-system/` 是 Agent System 的 Source of Truth（角色、工作流、协议、状态机、契约、模板）。
- 当前项目状态以 `docs/state/` 为准。
- Agent 开始任何工作前必须读取当前 Round 及其契约。

## 硬性规则

1. 需求、实现、QA、真实运行、专家验收必须区分，互不替代。
2. 代码测试通过不等于专家验收通过。
3. Agent 不得根据聊天历史重新发明项目架构；架构以 `docs/agent-system/` 与 `docs/decisions/` 为准。
4. 原始数据不可逆丢失是严重事故；任何清洗步骤必须可回放（replayable）、可追溯。
5. 失败必须沉淀为知识、测试（regression）或决策资产，不允许静默消失。
6. Code Review 的普通技术债不阻塞研究主流程（见 `backlog/code-review-backlog.md`）；只有数据破坏、严重逻辑错误、安全问题才可升级为阻塞。
7. Agent 必须优先读取仓库事实（`docs/state/`、`docs/rounds/`、`docs/knowledge/`、`docs/decisions/`、当前 Round 契约），而不是依赖长会话记忆。
8. 所有关键结论必须标注证据级别（见 `docs/agent-system/protocol.md` Evidence Levels）。

## 链接

- [Agent System README](docs/agent-system/README.md)
- [Protocol](docs/agent-system/protocol.md)
- [Workflow](docs/agent-system/workflow.md)
- [Project Status](docs/state/project-status.md)
- [Current Round](docs/state/current-round.md)
- [Capability Ledger](docs/state/capability-ledger.md)
