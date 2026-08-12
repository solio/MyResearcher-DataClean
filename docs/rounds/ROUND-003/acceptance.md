# ROUND-003 Pilot Acceptance

状态：**QA_PASS / PILOT_READY_FOR_RESEARCH_OWNER** ｜ QA：Core QA ｜ 2026-08-12

| AC | 验收 | 结果 |
| --- | --- | --- |
| AC-1 | 真实 Collector `source_item_observations` 输入，恰好 300 条 unique observation_id | PASS：8251 source rows -> 300/300 unique |
| AC-2 | 每条记录可回溯真实 observation，保留 identity、lineage、title、content | PASS：300/300 provenance checks；300/300 title/content unchanged |
| AC-3 | 轻量 bucket sampling deterministic，overlap 只形成 sampling_reasons 属性，不删除 exact-content occurrences | PASS：bucket targets recorded；43 pilot observations belong to 34 repeated-content groups |
| AC-4 | 固定 DB fingerprint + sampler version + seed replay identical | PASS：JSONL/CSV/profile replay hashes identical |
| AC-5 | 输出字段完整，metadata 缺失如实记录；无 synthetic 或 quality labels | PASS：profile records list_title, metadata availability, synthetic=false, quality_labels=false |
| AC-6 | 不进入 annotation/model/experiment，不调用 Finance/Sentiment Expert | PASS：本 Round 仅 sampler -> artifacts -> QA |

## QA commands and evidence

```text
python -m ruff check src/myresearcher_dataclean/pilot.py       PASS
python -m compileall -q src/myresearcher_dataclean/pilot.py    PASS
python -m pytest                                            27 passed
seed replay: pilot-300.jsonl / pilot-300.csv / pilot-profile.json hashes identical
```

真实 DB fingerprint：`b7c3189b19cf4d65197f363dc6102535ca248ac580831af3db2c11ada3a03006`。
Input rows：8251；date range：2026-07-08 至 2026-08-12；content source：`list_title`。
