# ROUND-003 Core QA Report

> Status：**QA_PASS / PILOT_READY_FOR_RESEARCH_OWNER** ｜ Date：2026-08-12

QA performed only structural, provenance, determinism and preservation checks. It did not
assign or infer any quality, disposition, sentiment, or annotation label.

## Results

- `pilot-300.jsonl` contains 300 rows and 300 unique `observation_id` values.
- All 300 IDs resolve to the read-only Collector source rows.
- All 300 `title` and `content` values exactly equal the source row values.
- All rows retain source item, observation version, source metadata, raw evidence and scopes.
- Repeated content remains represented by independent observations: 43 pilot rows across 34
  repeated-content groups; no content-based deletion occurred.
- Seed replay with `20260812` produced identical SHA-256 for all three artifacts.
- No synthetic observations and no disposition, sentiment, quality, human, teacher, or LLM
  labels are present.

## Source facts

The selected database is the completed 35-day backfill at
`MyResearcher-DataCollector/data/collector.db`: SQLite user_version 2, 8251 observations,
one source (`eastmoney_guba`), and observed content source `list_title`. The source database
fingerprint is `b7c3189b19cf4d65197f363dc6102535ca248ac580831af3db2c11ada3a03006`.

The pilot is ready for Research Owner manual inspection. QA stops here; no annotation or model
execution is authorized by this Round.

The JSONL/CSV payloads contain real source text and author-linked lineage, so they are excluded
from Git by the repository `.gitignore`. The profile summary, sampler code, QA evidence and source
fingerprint remain suitable for Git history; the payloads must be retained/transferred through a
controlled artifact channel.
