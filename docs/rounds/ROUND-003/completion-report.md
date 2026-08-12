## A. Source Data

真实输入为已完成 35 天 backfill 的 Collector SQLite：
`/Users/mac/Documents/trae_projects/MyResearcher/MyResearcher-DataCollector/data/collector.db`。
读取 `source_item_observations` 得到 8251 条真实 observations，source 为 `eastmoney_guba`，
content source 为 `list_title`，时间覆盖 2026-07-08 至 2026-08-12。DB fingerprint 为
`b7c3189b19cf4d65197f363dc6102535ca248ac580831af3db2c11ada3a03006`。

## B. Sampling Result

使用 `round-003.pilot.v1` 与 seed `20260812`，按 deterministic hash ordering 完成轻量
分层抽样。最终得到 300 条 unique observation_id。bucket 可重叠；每条保留排序去重后的
`sampling_reasons`。不同 observation 的相同 title/content 仍独立保留。

## C. Pilot Profile

- Pilot size：300
- 全源 length distribution：VERY_SHORT 2333、MEDIUM 3610、LONGER 2308
- Bucket reason counts：GENERAL_RANDOM 120、VERY_SHORT 50、MEDIUM_LENGTH 40、
  LONGER_TEXT 30、EXACT_CONTENT_REPEAT 20、METADATA_EXTREME 20、STRUCTURAL_PATTERN 20，
  另有 6 条因 overlap 后由 general supplement 补足
- Pilot 中重复 exact-content observations：43 条，分属 34 个 exact-content groups
- 可用 metadata：author_id、author_name、read_count、reply_count、like_count、forward_count；
  当前 like_count 实际值均为空，未伪造
- 日期：2026-07-08 至 2026-08-12

## D. QA

300/300 unique；300/300 provenance 可回溯；300/300 title/content 未修改；seed replay 的
JSONL、CSV、profile 三个 artifact hash 完全一致；无 synthetic observations；无人工/LLM
quality labels。全仓 pytest 27 passed，ruff、compileall、diff check 通过。

## E. Artifact Paths

- `artifacts/round-003/pilot-300.jsonl`（本地/受控 artifact；按 `.gitignore` 不提交）
- `artifacts/round-003/pilot-300.csv`（本地/受控 artifact；按 `.gitignore` 不提交）
- [pilot-profile.json](/Users/mac/Documents/trae_projects/MyResearcher/MyResearcher-DataClean/artifacts/round-003/pilot-profile.json)
- [QA report](/Users/mac/Documents/trae_projects/MyResearcher/MyResearcher-DataClean/docs/rounds/ROUND-003/qa-report.md)

真实 pilot payload 不进入 Git，因为包含原始论坛文本、作者字段和 Collector lineage；
Git 保留 sampler、contract、QA、profile summary 与 source fingerprint，payload 应放在
受控 artifact storage 或由 Research Owner 安全传递。

## F. Data Issues Observed

- 2333/8251 source records（约 28.26%）属于 `text_length <= 8`；这是长度事实，不是质量判断。
- 当前内容来源是 `list_title`，不是 detail page；本 Round 未要求或调用 detail page。
- `like_count` 字段存在但当前 observations 的值为空；没有伪造高 engagement 值。
- Pilot 中有 43 条 observations 属于 34 个重复 exact-content groups；没有因重复内容删除
  observation。

Round 状态：**ROUND-003 PILOT_READY_FOR_RESEARCH_OWNER**。本 Round 到此停止。
