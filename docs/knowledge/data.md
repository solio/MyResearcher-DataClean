# Data Knowledge

## Purpose

积累数据分层与数据契约相关的知识：RAW / NORMALIZED / ENRICHED / ELIGIBLE / AGGREGATED 分层、schema、provenance、processing/rule version、重复簇、可回放性与不可逆数据保护。
维护者：Data Architecture Expert。

## Evidence Rules

- 每条知识必须标注 Evidence Level（CONFIRMED / PROVISIONAL / HYPOTHESIS / REJECTED）。
- 数据问题报告必须带样本证据。
- 分层与 schema 决策需记录理由，涉及取舍的写入 `docs/decisions/decision-log.md`。
- 初始条目全部为 PROVISIONAL。

## Known Initial Assumptions（全部 PROVISIONAL）

- RAW 层必须只读、不可变；任何派生数据必须可从 RAW 重建（可回放）。
- 每条记录需要 provenance：source、author、timestamp、processing version、rule version。
- 重复内容需要以 duplicate cluster 方式管理，而非直接删除。
- 数据源结构差异大（股吧、雪球、微博、新闻/公告/研报转载），需要统一的 RAW schema。
- 原始数据的不可逆丢失是不可接受的事故。

## Open Questions

- 五层分层的具体字段契约如何定义？
- 重复簇的判定窗口与近似去重标准？
- 时间字段口径（发布时间 vs 抓取时间）如何统一？
- 训练/验证/测试的时间切分规则（防泄漏边界）如何设计？
- 数据量级与存储方案（未评估，不假设）。

## 维护记录

| 日期 | 变更 | 级别 |
| --- | --- | --- |
| 2026-08-07 | 初始化：仅登记初始假设与开放问题 | PROVISIONAL |
