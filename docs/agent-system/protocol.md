# Protocol — 共同协议

本文档是全项目共同协议（canonical）。所有角色、所有执行器都必须遵守。

## Evidence Levels

所有关键结论必须标记以下级别之一：

| Level | 含义 |
| --- | --- |
| CONFIRMED | 已被真实数据、人工检查或可复现实验确认。 |
| PROVISIONAL | 有部分支持，但尚未被严格验证；允许作为工作假设使用，必须可被推翻。 |
| HYPOTHESIS | 仅是基于经验或直觉的假设，没有任何项目内证据。 |
| REJECTED | 已被证据否定；必须记录原因，防止再次提出。 |

规则：

- 标记必须与 `docs/decisions/decision-log.md`、`docs/knowledge/`、Round 报告保持一致。
- 未标注证据级别的结论一律视为 HYPOTHESIS。
- 结论必须说明证据来源（见 `contracts/evidence-contract.md`）。

## Capability Maturity

所有项目能力必须标记以下成熟度之一：

| Maturity | 含义 |
| --- | --- |
| PROPOSED | 只是提案，无实现。 |
| PROTOTYPE | 有原型实现，未经系统测试。 |
| TESTED | 代码完成且通过单元/集成测试。 |
| DATA_VALIDATED | 在真实数据上运行并验证过。 |
| EXPERT_ACCEPTED | 经过领域专家验收。 |

规则：

- **代码完成最多进入 TESTED。**
- **真实数据运行之后才能进入 DATA_VALIDATED。**
- **专家验收之后才能进入 EXPERT_ACCEPTED。**
- 任何人不允许跳级声明能力。

## Failure Routing

所有失败按类型路由，**不得一律交给 Developer 打补丁**：

| 失败类型 | 路由到 |
| --- | --- |
| 需求语义问题 | Domain Experts（Finance / Sentiment / Data Architect）与 Requirements |
| 情感或立场定义问题 | Sentiment Expert |
| 财经解释问题 | Finance Expert |
| 数据建模问题 | Data Architect |
| 系统设计问题 | Solution Architect |
| 实现 Bug | Developer |
| 测试设计问题 | QA |
| 真实数据表现问题 | 进入研究循环（research → experiment → expert reconsideration） |

## Two Repair Rule

同一根因经过**两轮局部 Developer 修复**仍然失败：

1. 停止继续 patch。
2. 创建 Root Cause 记录（写入当前 Round 文档与 `docs/decisions/`）。
3. 返回需求层或架构层重新处理。

目的：防止用补丁掩盖结构性问题。

## User Decision Gate

只有以下问题才要求用户介入：

- 会改变研究目标。
- 会永久丢弃一类潜在信号。
- 两种方案对应不同投资研究口径。
- 成本/效果存在重大且无法通过实验解决的取舍。
- 会破坏历史数据兼容性。

普通技术实现问题不得频繁请求用户。

## 相关契约

- 证据契约：`contracts/evidence-contract.md`
- 能力契约：`contracts/capability-contract.md`
- 交接契约：`contracts/handoff-contract.md`
