# Round Contract — ROUND-003 Real-Data Pilot Sampling

> 状态：**PILOT_READY_FOR_RESEARCH_OWNER**
>
> Trigger：USER_TRIGGER ｜ Owner：Data Executor / Developer ｜ 2026-08-12

## Objective

从完成 35 天 backfill 的真实 DataCollector SQLite
`source_item_observations` 中生成恰好 300 条 unique real observations，供 Research
Owner 人工研究并制定后续 Quality Cleaning Contract。Pilot 完成后停止。

## Frozen input and boundary

- 真实输入：`/Users/mac/Documents/trae_projects/MyResearcher/MyResearcher-DataCollector/data/collector.db`
- 仅读取 `source_item_observations` 及其 Collector lineage；不要求 detail page。
- 当前内容来源事实为 `content_source=list_title`；短文本不因长度被删除或判定为垃圾。
- 原始 `title`、`content`、observation identity 与 lineage 不被清洗、改写、截断或去重。

## Sampling contract

固定 seed `20260812`、sampler version `round-003.pilot.v1`，使用 deterministic hash
ordering 而非 `ORDER BY RANDOM()`。目标 bucket 为：GENERAL_RANDOM 120、VERY_SHORT 50、
MEDIUM_LENGTH 40、LONGER_TEXT 30、EXACT_CONTENT_REPEAT 20、METADATA_EXTREME 20、
STRUCTURAL_PATTERN 20。Bucket 可重叠；最终 membership 按 immutable `observation_id`
去重，不足时由 general deterministic pool 补足。

结构 bucket 只能使用长度、标点、数字、URL、ticker/tag、Unicode、重复字符、whitespace
等形式特征。Metadata bucket 只使用 Collector 已存在的 count 字段；字段或值不存在时
记录事实，不伪造。Exact-content bucket 保留所有命中的 observations，不把正文相同当作
record identity。

## Out of scope

不定义 taxonomy，不判断 KEEP/EXCLUDE/low information，不判断 sentiment，不研究或选择
模型，不调用 LLM，不自动标注，不训练 classifier，不建立 annotation/golden/experiment
artifact，不扩建 experiment infrastructure，不要求 detail page，不创建 ROUND-004。

## Required output

`artifacts/round-003/pilot-300.jsonl`、`pilot-300.csv`、`pilot-profile.json`。每条记录至少
包含 observation/source/source item/time/author/title/content/text length/count metadata、
exact-content key/count、sampling reasons、Collector lineage/source reference。

## Invariants and acceptance

1. 输出恰好 300 条且 observation_id 唯一。
2. 每条 observation 可回溯真实 Collector row；title/content 字节级语义保持一致。
3. 相同 DB fingerprint + sampler version + seed 产生相同 artifacts。
4. sampling reasons 是可解释的结构 bucket 属性，不是互斥分类或质量标签。
5. 不产生 synthetic observation、人工/LLM label、model metric 或 quality conclusion。
