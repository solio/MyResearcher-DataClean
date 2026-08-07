# Glossary — 项目术语表

## Purpose

统一全项目术语定义，保证不同角色、不同执行器使用同一含义。条目按证据级别标注；初始条目全部为 PROVISIONAL。

## Evidence Rules

- 术语定义修改需记录理由与日期。
- 术语与标签体系冲突时，以 Sentiment Expert 与 Solution Architect 的定稿为准。

## Known Initial Terms（全部 PROVISIONAL）

| 术语 | 定义（初始） | 说明/开放问题 |
| --- | --- | --- |
| 股吧 | 东方财富股票论坛的社区板块 | 数据源之一 |
| 帖子 / 评论 | 社区中的主帖与回复 | 层级结构待定义 |
| 引用 | 帖子中引用的他人内容 | 与作者自身评论的边界待定义 |
| 看多 / 看空 / 观望 | 对标的走势或基本面的立场表达 | 立场标签基座，定义待定稿 |
| BUY / HOLD / SELL | 行为意图标签 | 与立场标签的关系待定 |
| UNCERTAIN | 无法确定立场/情绪的样本类别 | 输出与评估口径待定 |
| 黑话 | A 股社区特有表达（如「接飞刀」「韭菜」） | 词典待建设 |
| 喊单 | 引导他人买入/卖出的营销表达 | 与正常观点区分待研究 |
| 水军 / 机器人 | 疑似非真实散户的批量内容 | 检测能力不存在（见 capability-ledger） |
| Golden Set | 金标集：人工标注的评测样本集 | 规模与流程待设计 |
| Regression Case | 回归案例：真实 Bug 沉淀的测试样本 | 由 QA 维护 |
| 重复传播 | 完全重复与近似重复的内容传播 | 检测能力不存在 |
| 拥挤度 | 群体持仓/观点一致性程度 | 财经含义待验证（Finance Expert） |
| 数据分层 | RAW / NORMALIZED / ENRICHED / ELIGIBLE / AGGREGATED | 字段契约待设计（Data Architect） |

## Open Questions

- 术语表的维护责任归属（建议：Solution Architect 牵头，专家补充）。
- 标签术语（立场 vs 行为意图）与研究报告口径的对齐方式。
