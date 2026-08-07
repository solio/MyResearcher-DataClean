# State Machine — 研发状态机

状态机是 Orchestrator 推进 Round 的唯一依据。

## 状态总览

| 状态 | 可以由谁进入 | 必须存在的 Artifact | 可以流向哪里 |
| --- | --- | --- | --- |
| DISCOVERY | Orchestrator（新 Round 启动 / 问题空间探索） | Round 契约草案、研究笔记 | REQUIREMENTS_ANALYSIS、RESEARCH_NEEDED、EXPERIMENT_NEEDED |
| REQUIREMENTS_ANALYSIS | 来自 DISCOVERY，或 RESEARCH/EXPERIMENT 结论返回 | 三专家研究报告、需求草案 | RESEARCH_NEEDED、EXPERIMENT_NEEDED、REQUIREMENTS_DESIGN |
| RESEARCH_NEEDED | 任何阶段按 Failure Routing 进入 | 研究问题、证据要求 | EXPERIMENT_NEEDED、REQUIREMENTS_ANALYSIS |
| EXPERIMENT_NEEDED | 来自 RESEARCH_NEEDED，或专家冲突 | 实验计划（假设、方法、成功标准） | REQUIREMENTS_ANALYSIS、REQUIREMENTS_DESIGN |
| REQUIREMENTS_DESIGN | 来自 REQUIREMENTS_ANALYSIS | Round Contract（Scope / Out of Scope / Acceptance Criteria） | ARCHITECTURE |
| ARCHITECTURE | 来自 REQUIREMENTS_DESIGN | 架构决策、Data Contract、Slice 列表 | TEST_DESIGN |
| TEST_DESIGN | 来自 ARCHITECTURE | QA 计划（Acceptance Matrix、Golden Fixtures、Expected RED tests、人工抽查与真实数据验收方式） | IMPLEMENTATION |
| IMPLEMENTATION | 来自 TEST_DESIGN | 每个 Slice 的实现与真实测试结果 | QA_LOOP |
| QA_LOOP | 来自 IMPLEMENTATION | QA 报告、regression 案例、Bug 记录 | IMPLEMENTATION（修复后回环）；通过 → TECHNICAL_REVIEW；两轮失败 → 返回上层 |
| TECHNICAL_REVIEW | 来自 QA_LOOP | 技术完成审查报告 | REAL_DATA_EXECUTION；不通过 → 回 IMPLEMENTATION / QA_LOOP |
| REAL_DATA_EXECUTION | 来自 TECHNICAL_REVIEW | 执行报告（运行报告、数据分布、异常/无法处理样本、与上一版本差异） | EXPERT_ACCEPTANCE |
| EXPERT_ACCEPTANCE | 来自 REAL_DATA_EXECUTION | 三专家独立验收报告与汇总结论 | ROUND_ACCEPTED；拒绝 → 路由回正确阶段 |
| ROUND_ACCEPTED | 来自 EXPERT_ACCEPTANCE | 关闭记录（Knowledge / Capability / Decision / Backlog 更新、Round 归档） | 未来 Round → DISCOVERY |
| BLOCKED | 任何状态（升级进入） | BLOCKED 记录（原因、选项、恢复条件） | 解决后回到正确状态 |

## 状态细则

- **DISCOVERY**：Round 的起点。探索问题空间，不产出代码。
- **REQUIREMENTS_ANALYSIS**：三专家独立研究与架构整合发生于此；产出需求草案。
- **RESEARCH_NEEDED / EXPERIMENT_NEEDED**：研究/实验循环的子状态，反复进出直到收敛；不允许带未知问题直接进入设计。
- **REQUIREMENTS_DESIGN**：需求冻结。Round Contract 在此定稿，Acceptance Criteria 冻结。
- **ARCHITECTURE**：架构与数据契约、Slice 拆分在此完成。
- **TEST_DESIGN**：QA 在代码之前参与的关键状态。
- **IMPLEMENTATION / QA_LOOP**：开发与测试循环；Two Repair Rule 在此生效。
- **TECHNICAL_REVIEW**：只审当前 Round 完成度，不得以未来优化 BLOCK。
- **REAL_DATA_EXECUTION**：Operator 真正运行真实数据；产物必须可复现（command/config/version）。
- **EXPERT_ACCEPTANCE**：三专家独立验收真实输出；与「测试通过」严格分离。
- **ROUND_ACCEPTED**：Round 关闭，更新四类资产。
- **BLOCKED**：任何状态可升级进入；必须记录原因、选项与恢复条件。

## 哪些状态不能跳过

- 不允许从 DISCOVERY 直接跳到 IMPLEMENTATION。
- 不允许没有 REQUIREMENTS_DESIGN（冻结的 Round Contract）就进入 ARCHITECTURE。
- 不允许跳过 TEST_DESIGN：QA 必须在开发之前参与。
- 不允许跳过 QA_LOOP 直接进入 TECHNICAL_REVIEW。
- 不允许跳过 REAL_DATA_EXECUTION 直接进入 EXPERT_ACCEPTANCE。
- 不允许跳过 EXPERT_ACCEPTANCE 直接关闭 Round。
- 任何「测试通过」都不能替代 EXPERT_ACCEPTANCE。

## 状态文件

当前状态以 `docs/state/current-round.md` 为准；Orchestrator 每次流转后必须更新该文件。
