# Agent System

本目录是整套长期多 Agent 研发组织的 **Source of Truth**。

## 为什么采用这种研发组织

本项目从零开始，需求本身不确定：

- 数据源多样（股吧、雪球、微博，以及新闻/公告/研报转载）。
- 目标信号复杂（立场、情绪、行为意图、多空分歧、热度、拥挤度、重复传播、异常宣传）。
- 标签定义、数据模型、研究价值都必须靠真实数据、实验、QA 和专家验收逐轮演化。

单个长会话无法承载这类项目：

- 模型参数不会因为项目运行而自动成长，长期知识必须显式持久化。
- 聊天历史不可靠、不可检索、不可复用。
- 项目需要多个专业视角长期分工。

因此本项目采用：

> **多个长期专业角色，围绕 Git 中持久的知识与能力，通过 Round 不断演进系统。**

而不是：

> ~~多个 Agent 一次性把项目做完。~~

## 核心概念

| 概念 | 含义 |
| --- | --- |
| Agent | 一次具体的执行实例（Claude Code / Codex 中的配置化 agent）。Agent 是 Role 的执行者。 |
| Role | 长期稳定的职责定义，canonical 版本位于 `roles/`。一个 Role 可由不同执行器的 Agent 承载。 |
| Round | 一个可验收的研发周期，有明确契约（见 `contracts/round-contract.md`）。 |
| Capability | 项目已具备的能力，登记在 `docs/state/capability-ledger.md`，带成熟度等级。 |
| Evidence | 结论所依据的证据（类型见 `protocol.md` 与 `contracts/evidence-contract.md`）。 |
| Knowledge | 领域知识，登记在 `docs/knowledge/`，带证据级别。 |
| Acceptance | 专家验收，与「测试通过」严格分离。 |
| Handoff | 角色间交接，必须完整、可执行（见 `contracts/handoff-contract.md`）。 |
| Backlog | 候选工作：研究方向与普通技术债。 |

## 工作流总览

```text
Requirements Research
(Finance Expert / Sentiment Expert / Data Architect 独立研究)
        ↓
Architecture
(Requirements & Solution Architect 整合)
        ↓
QA Test Design
(QA 在代码出现之前定义测试)
        ↓
Developer ↔ QA
        ↓
Technical Review
        ↓
Real Data Execution
        ↓
Expert Acceptance
        ↓
Next Round
```

独立旁路（默认不阻塞主流程）：

```text
Code Review（独立运行，Non-Blocking）
        ↓
Technical Debt Backlog（backlog/code-review-backlog.md）
```

## 目录结构

- `roles/` — 11 个角色定义（canonical）
- `contracts/` — Round / Handoff / Evidence / Capability 契约
- `templates/` — 可直接复制填写的模板
- `protocol.md` — 共同协议（证据级别、能力成熟度、失败路由、Two Repair Rule、用户决策门）
- `workflow.md` — 完整研发流程（循环而非瀑布）
- `state-machine.md` — 状态机定义

## 去重原则

角色职责、工作流、共同协议、状态机**只允许一个 canonical version** 存在于本目录。
Claude 与 Codex 的 adapter（`.claude/agents/`、`.codex/agents/`、两个 skill）禁止复制这些内容的大段文本，只允许引用路径。
