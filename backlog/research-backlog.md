# DataClean Backlog

只登记属于 RAW -> CLEAN 边界的候选工作；不在此重新承担 source access/crawling，也不登记下游 sentiment/label/analyze 研发。

| ID | DataClean 方向 | 状态 | 备注 |
| --- | --- | --- | --- |
| RB-001 | 不同 Collector source 的 RAW record 特征如何影响清洗 | CANDIDATE | 研究输入差异，不研究访问或爬取 |
| RB-002 | Collector RAW -> CLEAN schema、record identity 与 lineage | IN_ROUND | ROUND-001 |
| RB-005 | 短文本的结构保真清理 | CANDIDATE | 不判断语义或价值 |
| RB-006 | 正文 / 引用 / 转发内容的结构保持 | CANDIDATE | 不做 stance/label |
| RB-007 | exact duplicate 后的基础 near-duplicate 可行性 | CANDIDATE | ROUND-001 只做 exact；禁止 embedding/ML 扩张 |
| RB-011 | HTML/entity/encoding/whitespace 最小确定性 baseline | IN_ROUND | ROUND-001 |
| RB-012 | reject/drop reason taxonomy 与审计报告 | IN_ROUND | ROUND-001 |

## 从 DataClean 移出的 Bootstrap 条目

| 原 ID | 原方向 | 归属/处理 | 状态 |
| --- | --- | --- | --- |
| RB-001（原） | 股吧/雪球/微博访问方式与采集画像 | MyResearcher-DataCollector | TRANSFERRED |
| RB-003 | 立场/情绪/行为意图标签 | DataLabel / Sentiment | TRANSFERRED |
| RB-004 | sentiment Golden Set | DataLabel / Sentiment | TRANSFERRED |
| RB-008 | Spam/水军/广告/喊单语义检测 | 下游 Analyze/专项质量项目；不在本轮 | TRANSFERRED |
| RB-009 | 散户立场 baseline | Sentiment / Analyze | TRANSFERRED |
| RB-010 | 热度/多空分歧/拥挤度 | Analyze | TRANSFERRED |

状态：`CANDIDATE` / `IN_QUEUE` / `IN_ROUND` / `DONE` / `REJECTED` / `TRANSFERRED`。

## ROUND-002 close note

ROUND-002 没有新增 RAW -> CLEAN backlog 路线。其剩余事实是上游可见 Collector DB 为
0 observations，以及缺少 human-owned annotation guideline/review authorization 与真实
human golden labels；这些不是本表的 DataClean 清洗候选，已作为 evidence-backed
`RESEARCH_QUESTION` 记录在 `docs/rounds/ROUND-002/completion-report.md`，不会被误写成
新模型或新 Round。
