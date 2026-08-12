# A Dataset Infrastructure

ROUND-002 的 CLEAN sampling、annotation dataset、saved split、experiment、prediction 与
metrics 基础设施已实现并通过 AC-1--AC-8。所有 artifact 使用 canonical JSON SHA-256
寻址，record identity 只使用 immutable `observation_id`；`exact_content_key` 只用于
sampling/split group closure。Capability CAP-002 成熟度为 `TESTED`，不是
`DATA_VALIDATED`。

# B Sampling Evidence

唯一可见真实 Collector SQLite 以只读方式执行，输入 SHA-256 前后均为
`6c4d3c7acff34acc731698ea260442a376dfdd6eb6c0472e9f26cb04996f4825`。该库含
0 observations；ROUND-001 产生 0 CLEAN，ROUND-002 真实 sample count 为 0，刷新后的
sample manifest ID 为
`4a88913f3aed779bc23eb2c9f16933b0126f5c3eb7ea037b9c20b66eecab0822`。
Synthetic sampler replay 只证明 filter、seed、group selection、full CLEAN snapshot 与
lineage 的确定性，不作为真实数据表现。

# C Annotation Schema

Primary disposition 固定为 `KEEP | EXCLUDE | REVIEW`；secondary reason tags 固定为
`ADVERTISEMENT`、`BOT_TEMPLATE`、`LOW_INFORMATION`、`OFF_TOPIC`、
`MARKET_QUOTE_ONLY`、`REPOST`、`BROKEN_CONTENT`、`OTHER`，且不自动推导 disposition。
Annotation state 为 `candidate | reviewed | golden`；teacher 只能生成 candidate，golden
必须有 HUMAN attestation 和可验证的 immutable predecessor。Prediction 使用独立 schema，
不能回写 annotation。

# D Split / Leakage Controls

支持可保存、可重放的 `random_stratified`、`time_holdout`、`source_holdout`。Validator
从 canonical strategy config 和 immutable dataset/sample facts 重算 assignment，并同时
强制 observation identity 与 exact-content group 闭包。首次 Technical Review 发现的
self-rehashed split/provenance/transition/duplicate-identity 绕过均已修复；独立复验为
`REVIEW_PASS_REVALIDATION`，旧 `REVIEW_BLOCKED` 保留为历史。

# E Metrics

统一输出 ordered 3x3 confusion matrix、per-class precision/recall/F1、macro F1、KEEP
recall、false reject count/rate、EXCLUDE precision、REVIEW coverage；空分母为 `0.0`。
False reject 仅为 `gold=KEEP && prediction=EXCLUDE`。手算 regression 通过，重复 gold 或
prediction `observation_id` 在 join 前即 fatal。

# F Experiment Runner

Registry 严格只有 E0--E3。E0 的 TF-IDF character n-gram + Logistic Regression runner
已实现，bounded dependency 为 `scikit-learn>=1.8,<2`；相同 input/config/seed 的 synthetic
replay 确定，且明确不可提升为运行证据。E1--E3 仅保留冻结的 model/interface/dependency
declaration；没有 E4。Experiment ID 排除 host/runtime 差异，prediction 可完整追溯到
run、dataset/split、annotation、sample、CLEAN 与 Collector evidence。

# G E0 Result or Blocker

真实执行结论为 `BLOCKED_NO_GOLDEN_LABELS`。证据是可见 Collector DB 为 0 observations、
sample 为 0 records，且仓库中没有合格 real HUMAN golden dataset。执行结果严格为
`predictions=[]`、`metrics=null`；没有伪造训练、预测或质量数字。ROUND-002 基础设施因此
按合约关闭，但 E0 没有真实模型结果。

# H Research Questions

- `RESEARCH_QUESTION RQ-002-01`：哪个可审计的 Collector artifact 将提供非空、符合
  ROUND-001 contract 的真实 observations？Evidence：当前唯一可见库为 0 observations。
  Why it matters：没有非空输入就不能验证真实 sampling 分布、group leakage incidence 或
  E0 数据路径。

- `RESEARCH_QUESTION RQ-002-02`：由哪个 human owner 提供并批准 annotation guideline/
  version、review authorization 和 real human labels？Evidence：仓库中没有合格 golden，
  且本轮禁止自行定义 review policy 或制造 labels。Why it matters：只有通过 human
  review gate 的 golden dataset 才能解除 E0 的真实执行 blocker。
