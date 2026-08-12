# Round Contract — ROUND-002

> 名称：Dataset & Experiment Infrastructure
>
> 状态：CLOSED — INFRASTRUCTURE_ACCEPTED / E0_BLOCKED_NO_GOLDEN_LABELS
>
> Trigger：USER_TRIGGER
>
> Owner：Program Orchestrator ｜ 2026-08-12

## Objective

建立可回放的：

```text
real Collector observation
  -> deterministic CLEAN
  -> sampled candidate
  -> versioned annotation dataset
  -> saved group-aware split
  -> fixed experiment runner
  -> independent prediction artifact
  -> unified metrics
```

本轮以 infrastructure correctness 为目标，不以最高模型分数为目标。ROUND-001 的
deterministic cleaner 仍是唯一 RAW -> CLEAN 转换边界。

## Frozen research decisions

- Primary disposition：`KEEP | EXCLUDE | REVIEW`。
- Secondary multi-label reason tags：`ADVERTISEMENT`、`BOT_TEMPLATE`、
  `LOW_INFORMATION`、`OFF_TOPIC`、`MARKET_QUOTE_ONLY`、`REPOST`、
  `BROKEN_CONTENT`、`OTHER`。Reason tag 不自动推导 disposition。
- Fixed candidates：E0 TF-IDF character n-gram + Logistic Regression；E1
  `BAAI/bge-small-zh-v1.5` frozen embedding + linear classifier；E2 同一 embedding
  + SetFit-style fine-tuning + classifier；E3 `hfl/chinese-macbert-base` supervised
  sequence classification。
- `Qwen3-Embedding-0.6B` 只作 future ceiling；本轮不实现 E4。
- 不增加模型、label、threshold 或 active-learning 路线。如真实数据冲突，只记录
  `RESEARCH_QUESTION + evidence + why it matters`。

## Scope

1. 对 ROUND-001 CLEAN JSONL 建立 deterministic / seedable sampler，保留
   observation/source/item/time/title/content/relevant metadata/full raw lineage/
   exact-content relationship，支持 source、time、text length 过滤和 exact-content
   grouping。
2. 实现 versioned annotation dataset schema，明确 `candidate | reviewed | golden`；
   teacher annotation 默认且最多进入 candidate，golden 必须满足冻结的 human-review
   rule。
3. 实现 model-neutral teacher import/export contract；不设计 prompt，不调用 LLM。
4. 实现可保存/重放的 group-aware split manifest，禁止同 observation identity 或
   exact-content group 跨 train/test；支持 `random_stratified`、`time_holdout`、
   `source_holdout` 策略边界。
5. 实现统一 disposition metrics：confusion matrix、per-class precision/recall/F1、
   macro F1、KEEP recall、false reject count/rate、EXCLUDE precision、REVIEW coverage。
6. 实现 experiment/prediction artifact contract 与统一 runner boundary；E0 是本轮唯一
   mandatory implementation。E1–E3 只需固定候选 ID/interface/dependency boundary，不得伪造运行结果。
7. 在有足够真实 golden labels 时执行 E0；否则交付可执行 runner 并记录
   `BLOCKED_NO_GOLDEN_LABELS`。

## Out of scope

- 自行定义 annotation guideline、teacher prompt、review policy 或 confidence threshold。
- 自行批量标注、把 prediction/teacher output 当作 golden truth。
- 根据 sentiment、stance、bullish/bearish、财经观点或投资价值决定 disposition。
- E4、RoBERTa、ERNIE、FinBERT、7B/LoRA LLM 或任何新候选模型。
- 自行规划 ROUND-003。

## Invariants

- INV-1：Collector RAW 只读；所有 dataset/run/prediction 可追溯到 immutable
  `observation_id` 和 ROUND-001 source/raw lineage。
- INV-2：Golden annotation 与 model prediction 使用不同 schema/artifact，不能混写。
- INV-3：`TEACHER_MODEL` annotation 不得进入 golden；golden 必须通过当前
  human-review rule。
- INV-4：split 必须以 observation identity 与 exact-content group 的闭包 group 分配，
  任何跨 split overlap 都是 fatal leakage。
- INV-5：相同 ordered input + config + seed + versions 产生相同 sample、dataset
  version、split manifest、experiment ID 和 predictions。
- INV-6：false reject 仅定义为 `gold=KEEP && prediction=EXCLUDE`。
- INV-7：缺少真实 data/labels 时显式 BLOCK，不生成 synthetic 训练结果。

## Lightweight acceptance

- AC-1：Sampler 稳定、seedable，完整保留冻结 lineage/relationship 字段，并对
  source/time/length/group 行为有 deterministic tests。
- AC-2：Annotation schema/version/state validation 可执行；teacher -> golden、prediction ->
  annotation、非法 label/reason/state 全部明确失败。
- AC-3：Split manifest 可保存/重放，三种 strategy boundary 可执行，identity/content
  group leakage 断言为 0，非法 manifest 明确失败。
- AC-4：Metrics 对手算 fixture 逐项相等，含空分母行为；不只输出 accuracy。
- AC-5：Experiment manifest 包含冻结的全部 provenance/runtime 字段，prediction 独立存储，
  并能从 prediction 追溯 observation -> annotation -> dataset -> split -> run。
- AC-6：E0 runner 使用 TF-IDF character n-gram + Logistic Regression；在合格
  golden/split 上 deterministic replay，无合格 golden 时精确返回
  `BLOCKED_NO_GOLDEN_LABELS`。
- AC-7：E1–E3 只存在固定 model/revision/interface/dependency 声明，没有额外模型或
  伪造 metrics。
- AC-8：full pytest、lint/static、deterministic replay、leakage assertions、metric
  regression、provenance assertions 通过；真实 sampling/E0 结果或 blocker 有仓库证据。

## Specialists and gates

- Data Architect：**TRIGGERED / GATE**；dataset schema、state、lineage、versioning、prediction
  separation 和 artifact provenance contract。
- Technical Reviewer：**TRIGGERED / GATE**；只审 leakage、reproducibility、metric
  correctness 与 provenance。
- Finance/Sentiment Expert：不参与本轮常规流程。
- Solution Architect / Operator / Expert Acceptance / Code Reviewer：未触发。

## Known entry facts

- 工作区当前唯一可见真实 Collector SQLite 因 `SPEC_MISMATCH` 含
  `0 source_item_observations`。
- 仓库扫描未发现符合本轮 schema 的真实 human golden annotation dataset。
- 因此 E0 真实训练预期为 `BLOCKED_NO_GOLDEN_LABELS`；这是待 QA/执行复核的
  evidence-backed 预期，不是允许跳过 runner 实现。

## Closure

- AC-1--AC-8：全部满足；基础设施结论为 `ACCEPTED`。
- Core QA：`QA_PASS`；ROUND-002 suite 11 passed，full pytest 27 passed，ruff、
  compileall、deterministic replay、leakage、metrics、provenance 和 diff check 均通过。
- Risk-based Technical Review：首次 `REVIEW_BLOCKED` 作为历史保留；修复后独立复验为
  `REVIEW_PASS_REVALIDATION`。
- 唯一可见真实 Collector DB 仍为 0 observations；只读 hash 前后不变。E0 真实执行精确
  返回 `BLOCKED_NO_GOLDEN_LABELS`、`predictions=[]`、`metrics=null`。
- Capability change：新增 CAP-002，成熟度 `TESTED`；没有真实 golden 或非空真实样本，
  因此不声称 `DATA_VALIDATED` 或模型质量。
