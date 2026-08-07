# State Machine — 研发状态机

状态机是 Orchestrator 推进 Round 的唯一依据。

## 状态总览

| 状态 | 可以由谁进入 | 必须存在的 Artifact | 可以流向哪里 |
| --- | --- | --- | --- |
| NO_ACTIVE_ROUND | 初始状态（Bootstrap 完成时）；ROUND_ACCEPTED 关闭后（无继续执行上下文时） | 无（等待合法 Round Start Trigger） | 有合法 ROUND_START_TRIGGER → CREATE_ROUND → DISCOVERY；无 Trigger → 保持 NO_ACTIVE_ROUND |
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
| ROUND_ACCEPTED | 来自 EXPERT_ACCEPTANCE | 关闭记录（Knowledge / Capability / Decision / Backlog 更新、Round 归档） | → NO_ACTIVE_ROUND；或已有已批准的下一轮问题且存在明确继续执行上下文时，经 APPROVED_NEXT_ROUND Trigger → 新 Round → DISCOVERY |
| BLOCKED | 任何状态（升级进入） | BLOCKED 记录（原因、选项、恢复条件） | 解决后回到正确状态 |

## 状态细则

- **NO_ACTIVE_ROUND**：非死锁状态。含义：当前没有正在执行的 Round，等待合法的 Round Start Trigger。无 Trigger 时保持原状并正常停止；有合法 Trigger 时 Orchestrator 必须创建新 Round（见下方 Round Start Transition）。
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

## Round Start Transition（NO_ACTIVE_ROUND → DISCOVERY）

NO_ACTIVE_ROUND 的正确含义：**当前没有正在执行的 Round，等待合法的 Round Start Trigger**。它绝不意味着 Orchestrator 永远无权创建新 Round。

### ROUND_START_TRIGGER

合法的 Round Start Trigger 只有以下三类（本文件是唯一 canonical 定义，其他文件不得复制完整规则）：

**1. USER_TRIGGER**
用户明确要求启动研发，例如：开始项目、开始 Round 001、开启下一轮、继续下一轮、开始研究某个 backlog 项、处理某个明确研究问题。
用户不需要自己创建 Round 文件；只要用户意图明确表示「开始一个新的研发轮次」，即构成合法 Trigger。

**2. APPROVED_NEXT_ROUND**
上一 Round 已处于 ROUND_ACCEPTED，且其 Round Artifact 已明确记录 Next Highest-Value Question（或其他已批准的下一轮研究问题），同时存在明确的继续执行上下文（如工作流明确要求继续推进下一轮）。
不得因为上一轮通过就无限自动连续创建 Round。

**3. DECISION_TRIGGER**
`docs/decisions/decision-log.md` 中存在明确状态 `APPROVED_FOR_NEXT_ROUND` 并指向一个具体研究问题或 Backlog 项。

### 转移判定

```text
NO_ACTIVE_ROUND
        |
        v
Is there a valid ROUND_START_TRIGGER?
        |
   +----+----+
   |         |
   NO        YES
   |         |
   v         v
 STOP    CREATE_ROUND
             |
             v
        DISCOVERY
             |
             v
   REQUIREMENTS_ANALYSIS
```

- **无 Trigger**：`NO_ACTIVE_ROUND + no valid trigger → remain NO_ACTIVE_ROUND → do not create a Round → stop normally`。这用于防止 Agent 自己无目标地启动研发。
- **有 Trigger**：`NO_ACTIVE_ROUND + valid trigger → Program Orchestrator MUST create the new Round`。这里使用 **MUST** 而不是 MAY：一旦用户已经明确要求启动研发，Orchestrator 不应再要求用户手工创建 Round。

### CREATE_ROUND 的实际职责

当合法 Trigger 存在时，Program Orchestrator 必须自行执行 Round 初始化：

1. 读取：`docs/agent-system/templates/round-template.md`、`docs/state/project-status.md`、`docs/state/capability-ledger.md`、`backlog/research-backlog.md`，以及 Trigger 对应的用户目标或已批准问题。
2. 生成新的 Round ID（如 ROUND-001、ROUND-002，按现有 Round 顺序递增，不得覆盖已有目录）。
3. 创建 `docs/rounds/ROUND-<NNN>/`，按 round template 初始化该 Round 的核心 Artifact。
4. 更新 `docs/state/current-round.md`，使其指向新的 Round。
5. 更新项目状态到 DISCOVERY（或本状态机规定的新 Round 第一个状态）。
6. 将用户 Trigger 写入 Round：Trigger Type、Trigger Source、Initial Problem、Created At / Round ID。
7. 按 canonical workflow 进入后续需求研究流程。

### Phase 0 的含义

「Phase 0 不允许偷偷创建 Round 001」的精确解释：**在没有合法 ROUND_START_TRIGGER 的情况下，Phase 0 Bootstrap 本身不得自动进入 Round 001**。Phase 0 结束后，Orchestrator 在存在合法 Trigger 时仍必须创建 Round。

本次 Bootstrap / 规则修复本身**不构成** Round Start Trigger。

## 哪些状态不能跳过

- 不允许从 DISCOVERY 直接跳到 IMPLEMENTATION。
- 不允许没有 REQUIREMENTS_DESIGN（冻结的 Round Contract）就进入 ARCHITECTURE。
- 不允许跳过 TEST_DESIGN：QA 必须在开发之前参与。
- 不允许跳过 QA_LOOP 直接进入 TECHNICAL_REVIEW。
- 不允许跳过 REAL_DATA_EXECUTION 直接进入 EXPERT_ACCEPTANCE。
- 不允许跳过 EXPERT_ACCEPTANCE 直接关闭 Round。
- 任何「测试通过」都不能替代 EXPERT_ACCEPTANCE。
- 不允许在无合法 ROUND_START_TRIGGER 的情况下从 NO_ACTIVE_ROUND 进入 DISCOVERY。

## 状态文件

当前状态以 `docs/state/current-round.md` 为准；Orchestrator 每次流转后必须更新该文件。
