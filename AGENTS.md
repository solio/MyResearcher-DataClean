# AGENTS.md

本文件是整个 Git 仓库对所有 AI 执行器（Claude Code、Codex 等）的最高级项目约束。

## 项目边界

`MyResearcher-DataClean` 位于以下链路中：

```text
MyResearcher-DataCollector -> RAW DATA -> MyResearcher-DataClean
-> CLEAN DATA -> DataLabel / Sentiment / Analyze -> MyResearcher
```

本项目只负责把 Collector 的 RAW record 可靠转换为结构明确、可供下游使用且不破坏原始语义的 CLEAN record。输入验证、确定性噪声清理、基础无效内容检测、exact duplicate、metadata consistency、lineage、rule version、reject reason、replay 与 audit 属于本项目。

本项目禁止实现或设计 sentiment、stance、bullish/bearish、action intent、emotion、财经观点/价值判断、投资信号、LLM/FinBERT 标签，以及基于财经语义删除内容。DataClean 必须保持 **semantic ignorance**。

## Lean Round

普通 Round 的常驻核心角色只有：

- Program Orchestrator
- Developer
- QA

默认路径是：契约/验收定义 -> QA -> Developer <-> QA -> 真实数据验证 -> Orchestrator 验收 -> Close。Data Architect、Solution Architect、Finance Expert、Sentiment Expert、Technical Reviewer、Operator、Expert Acceptance Coordinator、Code Reviewer 都保留为 specialist toolbox，仅按 `docs/agent-system/workflow.md` 的触发条件调用；未调用 specialist 不得阻止普通 Round 完成。

## 来源与状态

- `docs/agent-system/` 是 workflow、protocol、role、state、contract 的 Source of Truth。
- 当前项目状态以 `docs/state/` 为准。
- 开始工作前必须读取当前 Round 及其契约。
- 关键事实必须落在 Git，而不是只存在于聊天中。

## 硬性规则

1. QA 在实现前冻结 lightweight acceptance criteria、invariants、fixtures、expected behavior 与 negative cases。
2. 相同 RAW input + 相同 cleaning rule version 必须得到相同输出。
3. RAW 不得被覆盖或不可逆丢失；CLEAN 必须保留到 Collector record/raw evidence 的 lineage，能够回放。
4. 任何 changed、normalized、rejected、dropped、deduplicated 结果必须有可解释的 rule/reason。
5. 禁止根据财经含义、情绪或立场删除、修改、标记文本。
6. 失败必须按 `protocol.md` 路由；同一根因两轮局部修复失败时执行 Two Repair Rule。
7. Code Review 默认不阻塞；仅数据破坏、严重逻辑错误、安全问题升级为阻塞。
8. 能力成熟度与关键结论必须有仓库证据并按 `protocol.md` 标注，测试通过不得冒充真实数据验证通过。

## 链接

- [Agent System README](docs/agent-system/README.md)
- [Protocol](docs/agent-system/protocol.md)
- [Workflow](docs/agent-system/workflow.md)
- [Project Status](docs/state/project-status.md)
- [Current Round](docs/state/current-round.md)
- [Capability Ledger](docs/state/capability-ledger.md)
