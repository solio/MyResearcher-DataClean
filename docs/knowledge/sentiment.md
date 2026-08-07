# Sentiment Knowledge

## Purpose

积累情绪与立场识别相关的领域知识：sentiment、stance、emotion、action intent 的区分；标签设计、标注规范、Golden Set、错误分类体系与升级路线。
维护者：Sentiment and Stance Expert。

## Evidence Rules

- 每条知识必须标注 Evidence Level（CONFIRMED / PROVISIONAL / HYPOTHESIS / REJECTED）。
- 标签定义变更必须带样本证据（Golden Set 或人工复核）。
- 反例与边界样本必须保留。
- 初始条目全部为 PROVISIONAL。

## Known Initial Assumptions（全部 PROVISIONAL）

- sentiment（情绪）、stance（立场）、emotion（情感）、action intent（行为意图）是四个不同的概念，必须分开建模与评估。
- 模型 confidence（置信度）不等于情绪强度；语言正负不等于交易立场（BUY/HOLD/SELL）。
- 反讽、否定、转折、短文本会系统性破坏朴素词典/规则方法。
- 引用他人内容与作者自己的评论必须分离处理。
- 无法确定的样本应输出 UNCERTAIN 而非强行分类。
- 存在「疑似机器人/水军」内容，其语言模式与真实散户不同。

## Open Questions

- 立场标签集（看多/看空/观望 + UNCERTAIN？）如何定义才能支撑研究目标？
- 反讽检测采用什么路线（规则、模型、人工标注补充）？
- Golden Set 的规模、来源与标注一致性流程如何设计？
- 错误分类体系（Error Taxonomy）的层级如何划分？

## 维护记录

| 日期 | 变更 | 级别 |
| --- | --- | --- |
| 2026-08-07 | 初始化：仅登记初始假设与开放问题 | PROVISIONAL |
