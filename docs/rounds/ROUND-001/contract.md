# Round Contract — ROUND-001

> 名称：Collector Input Contract & Minimal Cleaning Baseline
>
> 状态：BLOCKED（AC-8 real records unavailable）
>
> 确认：Program Orchestrator ｜ 2026-08-11

## Trigger and problem

- Trigger：USER_TRIGGER；用户明确要求 Lean Reset 后立即创建并启动 ROUND-001。
- Problem：DataClean 尚无业务代码，需要把 Collector 已持久化的 immutable RAW observation 转为 deterministic、replayable、traceable CLEAN record。
- Why now：Collector 已实现 SQLite schema v2（兼容 v1 observation/evidence 共同边界）与一次 80-record live smoke；继续停留在治理阶段没有业务价值。

## Evidence and unknowns

- `CONFIRMED — CODE_INSPECTION`：Collector SQLite v1/v2 共同定义 `source_item_observations`、`observation_evidence`、`raw_evidence`、`observation_scopes`；2026-08-11 上游当前版本为 v2。
- `CONFIRMED — REAL_DATA execution report`：Collector `runs/phase-02-live-smoke-01/execution-evidence.md` 记录 80 observations、160 evidence links，但报告引用的运行目录当前不存在。
- `CONFIRMED — repository fixture metadata`：Collector committed HTML fixtures 是 synthetic/cropped，不是真实 record fixture。
- Unknown：实际 live SQLite record 当前不可访问，真实内容变更/误改分布尚不能验证。

## Scope

1. 以 Collector SQLite schema v1/v2 共同子集为输入，使用只读连接读取 observation、scope 与 raw evidence lineage。
2. 验证最小 record contract。
3. 对 title/content 做保守、确定性的 NFC、BOM、HTML/entity 和 whitespace normalization。
4. 检测清理后空文本；输出机器可读 reject reason。
5. 对清理后 title+content 做 batch 内 exact duplicate identity；保留首条，后续条目记录 `EXACT_DUPLICATE` 与 `duplicate_of`。
6. 输出 CLEAN JSONL、rejections JSONL 和 deterministic run report。
7. 每条输出包含 Collector observation/raw evidence lineage、cleaning version、规则列表和 input/output digest。

## Out of scope

Near-duplicate、embedding/ML/LLM、spam 语义模型、sentiment、stance、bullish/bearish、action intent、emotion、recommendation、crowd signal、advanced NLP、production scale optimization，以及任何 Collector crawling/retry/persistence 实现。

## Invariants

- INV-1：不得依据财经语义做删除或修改；`垃圾股，明天继续加仓` 等内容保留。
- INV-2：RAW database 只读；CLEAN/rejection 能追溯 observation 与 raw evidence。
- INV-3：每个 reject/deduplicate 都有 reason，修改有 rules applied。
- INV-4：相同有序输入 + `minimal.v1` 产生 byte-identical serialization。
- INV-5：URL、mention、stock code、重复标点和原文可见文本不得被语义规则改写。
- INV-6：CLEAN record 保留 source、source item、author、timestamps、URL、metadata、Collector/cleaning versions。

## Acceptance Criteria

详见 `acceptance.md`。AC-1 至 AC-8 全部为 mandatory；真实 Collector records 的 AC-8 不得由 synthetic fixture 替代。

## Owners and specialists

- Core：Orchestrator / Developer / QA。
- Data Architect：已触发；原因是 RAW/CLEAN schema、record identity 与 lineage。输出是 `input-contract.md`，为 gate。
- Technical Reviewer：在实现后触发；原因是 core pipeline、dedup 与 lineage/replayability change。只审当前 contract，为 gate。
- Finance/Sentiment Expert：未触发；本轮规则不依据财经语义，semantic regression fixture 由 QA 覆盖。若发现 destructive rule 反例再调用。
- Operator / Expert Acceptance Coordinator / Solution Architect：未触发；运行可由固定 CLI + QA 完成，且没有多模块/cross-cutting architecture。
- Code Reviewer：optional/non-blocking。

## Capability and next questions

- CAP-001：AC-1–AC-7 已通过，成熟度为 TESTED；通过 AC-8 才可到 DATA_VALIDATED。
- Rejected：near-duplicate、semantic filtering、引入 workflow engine。
- Next question：真实数据画像后，判断是否需要单独 Round 改进 source-specific HTML/structure handling。
