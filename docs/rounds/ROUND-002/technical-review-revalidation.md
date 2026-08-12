# ROUND-002 Risk-Based Technical Review Re-validation

> Role：Technical Completion Reviewer  
> Decision：**REVIEW_PASS_REVALIDATION**  
> Date：2026-08-12  
> Scope：leakage、reproducibility、metric correctness、provenance only

## Decision

ROUND-002 在本次限定技术风险面通过复验。原
`technical-review.md` 的 **REVIEW_BLOCKED** 结论作为发现与修复历史永久保留；本报告
不删除或改写它，而是记录 `TR-B1`--`TR-B4` 已由实现修复、QA repair regressions 与本次
独立自洽重寻址 probes 闭合。

该结论只证明本轮 infrastructure contract 的技术边界。它不是模型质量、真实 golden
labels、非空真实 Collector sampling 或 E0 真实表现证据；当前真实执行仍受
`BLOCKED_NO_GOLDEN_LABELS` 约束。

## Independent quality gates

在仓库根目录独立执行：

```text
python -m pytest                                  27 passed
python -m pytest -q tests/test_round002_infrastructure.py
                                                  11 passed
ruff check src tests                              PASS
python -m compileall -q src tests                 PASS
git diff --check                                  PASS
```

测试与开发报告仍属于 synthetic infrastructure evidence。本审查另行执行下列 probes，
没有依赖 pytest 对异常的断言。

## TR-B1 — Split strategy replay：CLOSED

`_split_assignments` (`research.py:625--710`) 现在严格校验三种 strategy 的 canonical
config 并以 immutable dataset/sample facts 重算 assignments；`validate_split_manifest`
(`research.py:748--779`) 在 identity/content group closure 与 self-hash 之外比较重放结果。

独立构造有效 split 后篡改 assignments，并重新计算 `split_manifest_id`：

```text
TR_B1_RANDOM_REHASH=REJECTED:split strategy replay mismatch
TR_B1_TIME_REHASH=REJECTED:split strategy replay mismatch
TR_B1_SOURCE_REHASH=REJECTED:split strategy replay mismatch
```

因此 self-consistent content address 不再能掩盖 random/time/source boundary 失真；
observation identity 与 exact-content group closure 均仍由同一 validator 强制。

## TR-B2 — Provenance chain closure：CLOSED

Sampler manifest 现在保存 canonical sample bindings 与 source-lineage digest
(`research.py:135--146`, `235--258`)。Dataset build/validation 将 annotation membership、
sample ID、observation ID、exact-content key、完整 source lineage、record count、state、
ordered IDs 与 content digest 逐项闭合 (`research.py:388--493`, `569--622`)。

Experiment/prediction resolver 现在比较实际 dataset version/hash 与 split ID/hash，并调用
完整 split validator (`research.py:925--953`, `1002--1032`)。

所有篡改后均重新计算受影响 artifact 自身 ID：

```text
TR_B2_SAMPLE_MEMBERSHIP=REJECTED:annotation sample manifest binding is missing
TR_B2_FULL_LINEAGE=REJECTED:annotation source lineage mismatch
TR_B2_EXPERIMENT_DATASET_LINK=REJECTED:provenance experiment dataset version mismatch
TR_B2_EXPERIMENT_SPLIT_LINK=REJECTED:provenance experiment split ID mismatch
```

合法 prediction 仍可解析为原 sample 的 `clean_id` 与 Collector lineage，证明修复没有
把正常 provenance 路径一并阻断。

## TR-B3 — Immutable annotation transition：CLOSED

`build_annotation_dataset(..., prior_annotations=...)` 保持 candidate 构建兼容，同时为
reviewed/golden 提供明确的 immutable predecessor registry；每个 prior 先验证 schema 与
content ID，再验证存在性、state 和 observation/sample identity
(`research.py:431--476`)。

独立 probes：

```text
TR_B3_MISSING_PRIOR=REJECTED:supersedes annotation is missing
TR_B3_CROSS_OBSERVATION=REJECTED:supersedes annotation identity mismatch
TR_B3_BAD_STATE_PRIOR=REJECTED:supersedes annotation has invalid state
```

因此随机、跨 observation 与 golden/bad-state predecessor 都不能满足 human-golden
transition gate；teacher 本身仍只能保持 candidate，prediction 仍不能写入 annotation。

## TR-B4 — Metric identity and formulas：CLOSED

`compute_disposition_metrics` 在 dict join 前检查 gold/prediction observation identity
唯一性；schema-bearing annotation/prediction 还会验证 state/schema/content address
(`research.py:782--839`)。独立 probes：

```text
TR_B4_DUPLICATE_GOLD=REJECTED:duplicate golden observation_id
TR_B4_DUPLICATE_PRED=REJECTED:duplicate prediction observation_id
```

原手算 fixture 继续通过：false reject 仅为 `gold=KEEP && prediction=EXCLUDE`；rate 分母
为 gold KEEP count；per-class P/R/F1、macro F1、KEEP recall、EXCLUDE precision、REVIEW
coverage 与空分母 `0.0` 行为未改变。

## Reproducibility and retained boundaries

- 相同 ordered input/config/seed 的 sampler、split 与 synthetic E0 replay 测试通过。
- 独立使用相同 identity payload、不同 host/Python runtime 创建 experiment，得到相同
  `experiment_id`：`RUNTIME_INDEPENDENT_EXPERIMENT_ID=True`。
- Annotation 与 prediction 保持不同 schema/artifact；teacher import 只生成 candidate。
- E0 缺合格真实 golden 时仍返回 `BLOCKED_NO_GOLDEN_LABELS`，无 predictions/metrics；
  synthetic result 仍不可提升为真实 evidence。
- Registry 仍严格为 E0--E3；无 E4；E1--E3 仍是 declaration-only；E0 的 bounded
  `scikit-learn>=1.8,<2` dependency 保持声明。

## Handoff

Technical Review decision 为 **REVIEW_PASS_REVALIDATION**。旧
`technical-review.md` 的 REVIEW_BLOCKED 继续保留为历史证据，但其中 TR-B1--TR-B4
在当前实现上均已闭合。交回 Program Orchestrator；Round/acceptance/state/capability 的
最终更新仍由其按 Core QA 当前结论和真实 `BLOCKED_NO_GOLDEN_LABELS` evidence 处理。
