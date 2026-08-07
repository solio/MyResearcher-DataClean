# Research Backlog

候选研究方向登记处。**只登记，不执行，不排序。**
纳入哪个 Round、如何排序，由 Orchestrator 与 Solution Architect 决定；状态默认 CANDIDATE。

| ID | 研究方向 | 提出者 | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| RB-001 | 数据源画像：股吧/雪球/微博 各自结构、规模、时间范围、访问方式 | Bootstrap | CANDIDATE | 其他方向的前置 |
| RB-002 | RAW schema 设计 | Bootstrap | CANDIDATE | 依赖 RB-001 |
| RB-003 | 标签定义（立场 / 情绪 / 行为意图） | Bootstrap | CANDIDATE | 需 Sentiment Expert |
| RB-004 | Golden Set 建设 | Bootstrap | CANDIDATE | 需 Sentiment Expert + QA |
| RB-005 | 短文本处理 | Bootstrap | CANDIDATE | |
| RB-006 | 引用拆分（引用 vs 作者评论） | Bootstrap | CANDIDATE | |
| RB-007 | 重复传播检测 | Bootstrap | CANDIDATE | |
| RB-008 | Spam / 水军 / 广告 / 喊单检测 | Bootstrap | CANDIDATE | |
| RB-009 | 散户立场 baseline（规则或最小模型） | Bootstrap | CANDIDATE | |
| RB-010 | 聚合指标（热度 / 多空分歧 / 拥挤度） | Bootstrap | CANDIDATE | 需 Finance Expert 验证财经意义 |

## 状态词汇

- CANDIDATE（候选，未进入任何 Round）
- IN_QUEUE（已被排入未来 Round）
- IN_ROUND（正在某 Round 中执行）
- DONE（完成并验收）
- REJECTED（被否定，记录原因）
