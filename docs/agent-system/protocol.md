# Protocol — 共同协议

## Evidence Levels

| Level | 含义 |
| --- | --- |
| CONFIRMED | 已被真实数据、人工检查或可复现实验确认。 |
| PROVISIONAL | 有部分支持，可作工作假设但仍可被推翻。 |
| HYPOTHESIS | 没有项目内证据的假设。 |
| REJECTED | 已被证据否定；保留原因避免重复。 |

关键结论必须注明证据类型与来源（见 `contracts/evidence-contract.md`）；未标注的一律视为 HYPOTHESIS。

## Capability Maturity

| Maturity | 含义 |
| --- | --- |
| PROPOSED | 有契约，无实现。 |
| PROTOTYPE | 有原型，未完成系统测试。 |
| TESTED | 通过单元/集成验收。 |
| DATA_VALIDATED | 用真实 Collector record 执行并完成人工抽样。 |
| EXPERT_ACCEPTED | 当前能力确实需要且已经完成领域专家验收。 |

- 代码与 synthetic fixture 最多支持 `TESTED`。
- `DATA_VALIDATED` 必须有可复现命令、版本、统计和真实样本抽查。
- `EXPERT_ACCEPTED` 不是普通 DataClean Round 的默认目标或关闭前提。

## Failure Routing

| 失败类型 | 路由到 |
| --- | --- |
| Collector/CLEAN schema、lineage、identity | Data Architect（按需） |
| cleaning rule/acceptance 问题 | Orchestrator（contract owner）；cross-cutting 时 Solution Architect |
| 实现 Bug | Developer |
| 测试设计/fixture Bug | QA |
| 可能破坏财经原意 | Finance Expert（仅反例检查） |
| 可能破坏未来 sentiment/stance 信息 | Sentiment Expert（仅信息保真检查） |
| 真实数据未知模式 | 回到 contract/QA，必要时研究或实验 |

不得让 Developer 用 patch 掩盖错误 contract。

## Two Repair Rule

同一根因经过两轮局部 Developer 修复仍失败：停止 patch，记录 Root Cause，返回 contract、rule 或 architecture owner。结构性问题不得继续堆叠局部修复。

## Data safety and semantic ignorance

- RAW 只读；任何派生输出都能通过 lineage + cleaning version 重建。
- 每个 normalize/reject/drop/deduplicate 都有机器可读 rule/reason。
- DataClean 只能依据结构、编码、空值、确定性文本噪声和 exact identity 作决定，禁止依据看多/看空、情绪、行动意图或股票价值作决定。

## User Decision Gate

只有改变项目边界、永久丢弃一类原始证据、破坏历史 schema 兼容、或存在无法通过实验解决的重大成本/效果取舍时才请求用户。普通实现选择不触发。

## Round Start

只有 Orchestrator 创建 Round。用户明确要求开始一个具体 Round、已接受 Round 的 approved next question、或 Decision Log 中 `APPROVED_FOR_NEXT_ROUND` 的具体问题，构成合法 trigger。无 trigger 时保持 `NO_ACTIVE_ROUND`；有 trigger 时必须初始化 `PLANNED` Round。
