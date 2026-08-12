# ROUND-002 Risk-Based Technical Review

> Role：Technical Completion Reviewer  
> Decision：**REVIEW_BLOCKED**  
> Date：2026-08-12  
> Scope：leakage、reproducibility、metric correctness、provenance only

## Decision

ROUND-002 当前不能通过 Technical Review。正常路径与现有 synthetic tests 均通过，
但独立的 content-addressed tamper probes 证明：攻击者或损坏的 artifact 只要重新计算
自身 hash，就能绕过 split strategy boundary 与多段 provenance link；metrics 也会静默
覆盖重复 observation identity，造成 false-reject 低报。这些是当前 Data Contract 的
required validator outcomes，不是未来优化。

本审查不评价模型质量，不提出新模型/label/threshold，也不改变 E0--E3 决策。

## Independent validation

在仓库根目录独立执行：

```text
python -m pytest                                  26 passed
python -m pytest -q tests/test_round002_infrastructure.py
                                                  10 passed
ruff check src tests                              PASS
python -m compileall -q src tests                 PASS
git diff --check                                  PASS
```

以上证明现有回归无失败，但不覆盖下列可重寻址绕过。另一个独立 probe 以相同 experiment
identity payload、不同 runtime/host 创建 manifest，确认两个 `experiment_id` 相等；该项
符合 runtime 不参与 logical experiment identity 的契约。

## Blocking findings

### TR-B1 — Persisted split manifest 不验证其声明的 strategy boundary

**Contract：** Data Contract lines 178--207、255--267；AC-3。`time_holdout` 与
`source_holdout` assignment 必须分别由 cutoff/source config 决定，非法 boundary 必须
失败。

**Code inspection：** `create_split_manifest` 在 `research.py:510--607` 正确构造三种
strategy；但 `validate_split_manifest` 在 `research.py:610--634` 只检查 assignment
完整性、group closure 与 manifest self-hash，未验证 `strategy/config` 形状，也未根据
config 重算 assignment。

**Independent probe：** 将一个有效 random split 改称 `source_holdout`，配置 held-out
source 为 `source-d`，保留与该 source boundary 不同的 assignments，并重新计算
`split_manifest_id`。`validate_split_manifest(...)` 返回成功：

```text
PROBE_SPLIT_ACCEPTED_WRONG_BOUNDARY True
```

这不会让同一个 exact-content key 横跨 split，但会让保存/重放的 strategy 语义失真，
也会让 source/time holdout 的 leakage boundary 无法可信重放。

**Repair acceptance：** validator 必须严格校验三种 strategy 的 canonical config，并用
dataset/sample facts 重演 frozen algorithm 或等价地比较 canonical expected assignments；
错误 source/time boundary、random config/assignment mismatch 均应稳定失败。三种 tamper
regression 必须在重新计算 manifest ID 后仍失败。

### TR-B2 — Dataset / annotation / experiment provenance links 未闭合

**Contract：** Data Contract lines 95--148、241--267；AC-2、AC-5。Annotation 必须属于
manifest 指定 sample，`source_record_lineage` 必须与该 sample 的 immutable CLEAN snapshot
一致，resolver 必须验证 experiment -> dataset/split -> annotation -> sample -> CLEAN 的
每个重复 ID/hash/key。

**Code inspection：**

- `build_annotation_dataset` (`research.py:385--407`) 验 annotation self-hash，却不验证
  annotation 的 `sample_record_id` 属于所给 sample manifest。
- `_dataset_maps` (`research.py:483--507`) 只比 sample ID、observation ID 与 content key，
  未比 `source_record_lineage` 的 clean ID/version、Collector fields、fact fingerprint、raw
  evidence/scopes；也未重算 `dataset_content_sha256`、`record_count` 或核对 manifest
  `dataset_state`。
- `resolve_prediction_provenance` (`research.py:807--835`) 未验证 experiment manifest 中的
  `dataset_version/dataset_content_sha256/split_manifest_id/hash` 与实际 artifacts 相等；也
  未调用完整 split validation。

**Independent probes（每次篡改后均重新计算对应 content ID）：**

```text
PROBE_SAMPLE_BINDING_ACCEPTED True
PROBE_LINEAGE_MISMATCH_ACCEPTED True
PROBE_EXPERIMENT_LINK_MISMATCH_ACCEPTED True
```

第一项把 sample A 的 annotation 装入 sample B 的 manifest；第二项将 annotation lineage
的 `clean_id` 改为伪造值后仍可创建 split；第三项令 experiment 指向不存在的 dataset/
split IDs，并同步重新地址 prediction，resolver 仍返回成功。

**Repair acceptance：** 使用现有 artifact/schema 边界完成全链校验，不需新增治理层：

1. dataset 构建/验证须核对 annotation sample ID 属于 source sample manifest，并校验
   manifest record count/state/content digest/ordered IDs；
2. annotation `source_record_lineage` 的完整冻结投影须逐项等于引用 sample 的 CLEAN/
   lineage，不能只比 fingerprint 是否非空；
3. experiment/prediction/resolver 必须将实际 dataset content hash、split ID/hash/version
   与 experiment identity payload 逐项闭合，并运行完整 split validator；
4. 新 tamper tests 即使重算所有被修改 artifact 的自身 ID 也必须失败。

### TR-B3 — Golden `supersedes_annotation_id` 不验证真实 transition

**Contract：** Data Contract lines 137--155；AC-2。Reviewed/golden 必须 supersede 一个
相同 observation 的 candidate/reviewed immutable annotation，teacher record 本身不可
原地 promotion。

**Code inspection：** `create_annotation_record` / `_validate_annotation`
(`research.py:303--365`) 仅要求 `supersedes_annotation_id` 是 non-empty string。当前 API
没有接收或查询 immutable prior annotation 集，因此任意字符串都能满足 golden gate；
现有 `_golden` fixture 也只构造 predecessor ID，未把 predecessor 交给 validator。

**Repair acceptance：** 在现有 annotation/dataset API 内增加可验证的 immutable prior
annotation registry 或明确的 transition validator 输入；必须验证 predecessor 存在、
content-addressed ID 正确、observation/sample 一致、state 为 candidate/reviewed，且 teacher
predecessor 只能由新 HUMAN annotation review。随机/不存在/跨 observation predecessor
须稳定失败。这是补齐现有 contract reference，不要求新 workflow 或架构层。

### TR-B4 — Metrics 对重复 observation identity 静默覆盖

**Contract：** INV-6、AC-4，以及 Data Contract lines 249--252。False reject 仅为
`gold=KEEP && prediction=EXCLUDE`，metrics 输入必须按 provenance chain 一一 join。

**Code inspection：** `compute_disposition_metrics` (`research.py:637--668`) 先用 dict
comprehension 建表；重复 gold/prediction identity 被最后一条静默覆盖。公式在 identity
唯一的合法输入上是正确的，包括 false-reject rate 分母为 gold KEEP count 与空分母
`0.0`。

**Independent probe：** 输入同一 `observation_id=x` 的 gold KEEP、gold EXCLUDE 与一条
prediction EXCLUDE，函数未拒绝，且把实际包含的一次 KEEP->EXCLUDE 静默算成：

```text
PROBE_METRIC_DUPLICATE_ACCEPTED 0 0.0
```

**Repair acceptance：** 在 dict 化前拒绝 duplicate gold/prediction observation IDs，验证
gold 为 golden annotation、prediction schema/hash/chain 合格（或由已验证 join boundary
提供），并加入重复 identity 会稳定失败、合法手算 fixture 仍完全相等的 regression。

## Controls that did pass inspection

- Sample selection 对 ordered input/config/seed deterministic；exact-content group mode 保留
  整组，不把 content key 当 observation identity。
- `create_split_manifest` 的正常构造路径对 observation identity 与 exact-content group
  closure 正确，三种策略的 constructor boundary 已实现。
- Annotation 与 prediction 使用不同 schema/artifact；teacher import 只创建 candidate，
  prediction 字段被禁止混入 annotation。
- Experiment logical ID 包含 frozen identity payload，并正确排除 runtime 与 registry；
  canonical replay 与独立 runtime probe 通过。
- False-reject、per-class P/R/F1、macro F1、KEEP recall、EXCLUDE precision、REVIEW coverage
  的公式对唯一 identity fixture 正确。
- E0 在缺真实 golden 时返回 `BLOCKED_NO_GOLDEN_LABELS` 且不生成 prediction/metrics；
  synthetic branch 明确 non-promotable。
- Registry 恰为 E0--E3，无 E4；E1--E3 为 declaration-only；`pyproject.toml` 声明
  `scikit-learn>=1.8,<2`。

## Handoff

Decision 为 **REVIEW_BLOCKED**。路由到 Developer 修复 TR-B1--TR-B4，再由 Core QA 增加
上述 tamper/duplicate/transition regressions 并全量复验；随后重新执行同范围 risk-based
Technical Review。在此之前，不应把 ROUND-002 标为 Technical Review PASS 或完成。
