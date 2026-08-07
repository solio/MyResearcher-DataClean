# Finance Knowledge

## Purpose

积累 A 股社区财经语义与散户行为相关的领域知识：看多/看空/观望表达、买卖动作、仓位表达、市场环境、群体情绪、拥挤度、传播结构，以及这些表达对聚合信号的意义。
维护者：Financial Domain Expert。

## Evidence Rules

- 每条知识必须标注 Evidence Level（CONFIRMED / PROVISIONAL / HYPOTHESIS / REJECTED，见 `docs/agent-system/protocol.md`）。
- 只有经过真实数据或专家验收的内容可升级为 CONFIRMED。
- 反例与失败假设必须保留，不得删除。
- 初始条目全部为 PROVISIONAL，未经项目内数据验证。

## Known Initial Assumptions（全部 PROVISIONAL）

- 股吧、雪球、微博等社区文本存在可识别的看多/看空/观望表达。
- 「看多措辞」不等于「买入行为」，两者必须区分。
- 散户语言与专业投资者/机构语言存在可观察差异。
- 社区中存在广告、营销、引流、喊单、疑似水军与重复传播等噪声。
- 群体情绪与拥挤度可能可以从社区文本中聚合估计，但有效性未验证。
- 存在未来数据泄漏风险：用 t 日之后的信息解释 t 日行为属于泄漏。

## Open Questions

- 哪些表达在 A 股语境中稳定指示看多/看空/观望？
- 仓位表达（如「满仓」「轻仓」「空仓」）能否作为行为意图证据？
- 反讽与黑话如何影响财经语义判断（与 Sentiment Expert 协作）？
- 如何系统性检测未来数据泄漏？
- 聚合情绪/立场指标是否有真实研究价值？

## 维护记录

| 日期 | 变更 | 级别 |
| --- | --- | --- |
| 2026-08-07 | 初始化：仅登记初始假设与开放问题 | PROVISIONAL |
