# Workflow — Lean DataClean Round

## Core workflow

普通 DataClean Round 只要求以下闭环：

```text
PLANNED
  -> Orchestrator 定义 Scope / Out of Scope / Acceptance
READY
  -> QA 在实现前定义 fixtures、expected behavior、negative cases
IMPLEMENTING
  -> Developer <-> QA
VALIDATING
  -> 固定命令执行真实 Collector 数据、统计并抽样
ACCEPTED
  -> Orchestrator 按 Round Contract 汇总必要证据
CLOSED
```

- acceptance 必须 lightweight、可执行，不要求大型测试计划。
- QA 与 Developer 可以循环；同一根因两轮局部修复失败执行 Two Repair Rule。
- 真实数据执行可由 QA、Developer 或 CI/script 完成，不要求独立 Operator。
- Orchestrator 可以直接做 Round acceptance；代码测试通过不替代 Round 明确要求的真实数据验证。

## Specialists on demand

Specialist 的定义保留，但只有触发条件成立时才参与：

| Specialist | 触发条件 |
| --- | --- |
| Data Architect | RAW/CLEAN schema、storage contract、lineage、record/dedup identity、persistence、breaking schema change |
| Solution Architect | 多模块结构、pipeline architecture、基础 infrastructure、cross-cutting 或影响多个 Round 的设计 |
| Finance Expert | cleaning rule 可能破坏财经原意，需要提供反例；禁止做分类或普通验收 |
| Sentiment Expert | cleaning operation 可能破坏未来情绪/立场分析所需信息；禁止实际标签 |
| Technical Reviewer | destructive/irreversible cleaning、breaking schema、major refactor、core pipeline、高风险 dedup、lineage/replay 变更 |
| Operator | 复杂生产执行或需要独立运行职责；普通真实数据验证不触发 |
| Expert Acceptance Coordinator | 多个已触发专家确需独立汇总时；普通 Round 不触发 |
| Code Reviewer | 可选、non-blocking；数据破坏、严重逻辑错误、安全问题除外 |

调用 specialist 时，Round Contract 必须记录触发原因、需要的输出以及它是否构成当前 Round gate。未触发的 specialist 不产生缺失 artifact，也不影响状态流转。

## Round close

只有当前 Round 的 Acceptance Criteria 全部满足时才能 `ACCEPTED`。`CLOSED` 时更新 Round 档案、Capability Ledger、Decision Log、Backlog 和项目状态。普通 improvement/technical debt 留在 backlog，不冒充 blocker。
