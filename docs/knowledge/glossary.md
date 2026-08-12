# Glossary — DataClean

| Term | Definition |
| --- | --- |
| RAW record | Collector 已获取并持久化的 source observation；DataClean 只读。 |
| CLEAN record | 对 RAW 做最小确定性结构/表面规范化后的派生记录，不包含语义标签。 |
| Lineage | CLEAN/rejection 到 Collector observation、scope、raw evidence/version 的证据链。 |
| Cleaning version | 决定本次确定性转换行为的规则版本。 |
| Rule applied | 实际改变 surface text 的机器可读规则名。 |
| Reject reason | `INVALID_RECORD`、`EMPTY_CONTENT` 等不进入 CLEAN 的可解释原因。 |
| Exact duplicate | cleaning version 下规范化 title+content byte-exact 相同；不是语义相似。 |
| Exact-content group | 由 ROUND-001 `exact_content_key` 表示的关系组；可用于防止 split leakage，但不改变 observation identity、保留或标签。 |
| Sample record | 完整 CLEAN snapshot 的 immutable dataset-entry projection，保留 observation、content relationship 与 Collector lineage。 |
| Annotation dataset | 由 immutable annotation records 组成的 versioned snapshot；其 `dataset_version` 是 canonical manifest 的 content-addressed ID。 |
| Candidate / reviewed / golden | annotation dataset states。Teacher 只可为 candidate；reviewed/golden 必须由 HUMAN 产生；golden 还须显式记录当前 human-review rule 的 attestation。 |
| Split manifest | 针对单一 golden dataset 的可重放 group-aware train/test assignment；同 observation 或 exact-content group 不得跨 split。 |
| Prediction artifact | 与 annotation dataset 分离的模型输出；通过 experiment/dataset/split/sample references 回溯，却不能作为 golden truth 写回。 |
| Replay | 使用相同 RAW snapshot 与 cleaning version 重建相同输出。 |
| Regression case | 已发现的清洗 Bug 或 semantic-destruction 风险的固定测试。 |
| Semantic ignorance | DataClean 不判断 sentiment、stance、行为意图、财经价值或投资方向。 |

Bootstrap 中的 BUY/HOLD/SELL、Golden Set、拥挤度等术语已移交下游，不是 DataClean contract。
