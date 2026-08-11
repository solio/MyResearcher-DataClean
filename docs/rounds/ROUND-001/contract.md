# Round Contract — ROUND-001

> 名称：Collector Input Contract & Minimal Cleaning Baseline
>
> 状态：QA_PASS / REAL_DATA_BLOCKED（correction QA + Technical Review PASS）
>
> 确认：Program Orchestrator ｜ 2026-08-11

## Trigger and problem

- Trigger：USER_TRIGGER；用户明确要求 Lean Reset 后立即创建并启动 ROUND-001。
- Problem：DataClean 尚无业务代码，需要把 Collector 已持久化的 immutable RAW observation 转为 deterministic、replayable、traceable CLEAN record。
- Why now：Collector 已实现 SQLite schema v2（兼容 v1 observation/evidence 共同边界）与一次 80-record live smoke；继续停留在治理阶段没有业务价值。

## Evidence and unknowns

- `CONFIRMED — EXTERNAL_REVIEW`：旧 exact-content rejection、meaning-bearing HTML 丢失与 post-validation rejection lineage 不完整是 data-correctness blockers；旧 Technical Review PASS 已 supersede。

- `CONFIRMED — CODE_INSPECTION`：Collector SQLite v1/v2 共同定义 `source_item_observations`、`observation_evidence`、`raw_evidence`、`observation_scopes`；2026-08-11 上游当前版本为 v2。
- `CONFIRMED — REAL_DATA execution report`：Collector `runs/phase-02-live-smoke-01/execution-evidence.md` 记录 80 observations、160 evidence links，但报告引用的运行目录当前不存在。
- `CONFIRMED — repository fixture metadata`：Collector committed HTML fixtures 是 synthetic/cropped，不是真实 record fixture。
- `CONFIRMED — AC-8 real-data attempt`：新的 Eastmoney 真实网络 Collector SQLite 已以只读方式成功执行 DataClean，但上游在身份核实页上以 `SPEC_MISMATCH` 停止，数据库含 0 observations。
- Unknown：至少含一条有效 observation 的实际 live SQLite 尚不可用，真实内容变更/误改分布与 before/after 抽样尚不能验证。

## Scope

1. 以 Collector SQLite schema v1/v2 共同子集为输入，使用只读连接读取 observation、scope 与 raw evidence lineage。
2. 验证最小 record contract。
3. 对 title/content 做保守、确定性的 NFC、BOM、HTML/entity 和 whitespace normalization；layout-only markup 可转换为边界 whitespace/newline，显式 allowlist 的 safe presentation wrapper 可去掉 tag syntax 但必须保留子文本。`del` / `s` / `strike` 必须在 CLEAN text 中保留可恢复的删除/划除关系；其他未能证明可安全丢弃的 markup 默认 preserve。
4. 检测清理后空文本；输出机器可读 reject reason。
5. record identity 只使用 Collector immutable `observation_id`（其 source/item/version 一致性由 Collector schema 约束）。清理后 title+content 的 deterministic exact-content key 只用于表达 content relationship/group；不同 `observation_id` 即使 key 相同也都输出为独立 CLEAN record，可在后续成员上记录 `duplicate_content_of`，但不得因 content equality reject/drop。
6. 输出 CLEAN JSONL、rejections JSONL 和 deterministic run report。
7. 每条输出包含 Collector observation/raw evidence lineage、cleaning version、规则列表和 input/output digest。已通过 input validation 后才产生的 non-CLEAN outcome 必须保留 full available Collector lineage；`INVALID_RECORD` 使用 best-effort lineage。
8. report 固定输出 `input_count`、`cleaned_count`、`unchanged_count`、`modified_count`、`exact_content_duplicate_count`、`rejected_count` 和 `reason_distribution`，并满足契约中的计数等式。

## Out of scope

Near-duplicate、embedding/ML/LLM、spam 语义模型、sentiment、stance、bullish/bearish、action intent、emotion、recommendation、crowd signal、advanced NLP、production scale optimization，以及任何 Collector crawling/retry/persistence 实现。

## Invariants

- INV-1：不得依据财经语义做删除或修改；`垃圾股，明天继续加仓` 等内容保留。
- INV-2：RAW database 只读；CLEAN/rejection 能追溯 observation 与 raw evidence。
- INV-3：每个 rejection 都有 reason，修改有 rules applied，exact-content relationship 有 deterministic key/可选 predecessor reference。
- INV-4：相同有序输入 + `minimal.v1` 产生 byte-identical serialization。
- INV-5：URL、mention、stock code、重复标点和原文可见文本不得被语义规则改写。
- INV-6：CLEAN record 保留 source、source item、author、timestamps、URL、metadata、Collector/cleaning versions。
- INV-7：content equality != record identity equality；不同 Collector observation occurrence 不得只因 CLEAN text 相同而丢失。
- INV-8：HTML normalization 不得消除否定、删除、划除或类似的 meaning-bearing structure；对非显式 safe allowlist 使用 preserve-by-default。
- INV-9：已通过 input validation 的 record 如被拒绝，lineage 不得退化为 best-effort 子集。

## Acceptance Criteria

详见 `acceptance.md`。AC-1 至 AC-8 全部为 mandatory；真实 Collector records 的 AC-8 不得由 synthetic fixture 替代。

## Owners and specialists

- Core：Orchestrator / Developer / QA。
- Data Architect：已触发；原因是 RAW/CLEAN schema、record/content identity、HTML structure preservation、lineage 与 reporting semantics。输出是 `input-contract.md` 与 `data-contract-correction.md`，为 gate。
- Technical Reviewer：在实现后触发；原因是 core pipeline、dedup 与 lineage/replayability change。只审当前 contract，为 gate。
- Finance/Sentiment Expert：未触发；本轮规则不依据财经语义，semantic regression fixture 由 QA 覆盖。若发现 destructive rule 反例再调用。
- Operator / Expert Acceptance Coordinator / Solution Architect：未触发；运行可由固定 CLI + QA 完成，且没有多模块/cross-cutting architecture。
- Code Reviewer：optional/non-blocking。

## Capability and next questions

- CAP-001：旧 TESTED evidence 已被 correction blockers supersede；修正后 AC-1–AC-7 的 QA 与 risk-based Technical Review 现已 PASS，以新 evidence 恢复 `TESTED`。仅当 AC-8 使用真实 Collector records 通过后才可到 `DATA_VALIDATED`。
- Rejected：near-duplicate、semantic filtering、引入 workflow engine。
- Next question：真实数据画像后，判断是否需要单独 Round 改进 source-specific HTML/structure handling。
