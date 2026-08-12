# ROUND-002 Lightweight Acceptance Definition

状态：**ACCEPTED / QA_PASS / REVIEW_PASS_REVALIDATION / E0_BLOCKED_NO_GOLDEN_LABELS** ｜ Owner：Core QA ｜ 2026-08-12

本矩阵在任何 ROUND-002 production implementation 前冻结。所有 fixture 都是
`SYNTHETIC_TEST_ONLY`，只能证明 schema、determinism 与算法边界，不能作为真实
sampling、human golden、E0 训练或 capability `DATA_VALIDATED` 证据。

| AC | Frozen executable acceptance | Expected RED coverage |
| --- | --- | --- |
| AC-1 | `sample_clean_records(...)` 按 source/time/text-length filter 后，以 seed 选择 record 或 complete exact-content group；返回 canonical manifest 和 full CLEAN snapshots。缺 immutable ID/clean ID/fingerprint/raw evidence/scopes/content key 必须失败。 | `test_sampler_is_deterministic_filters_and_preserves_full_clean_snapshot` |
| AC-2 | `create_annotation_record` / `build_annotation_dataset` 验证 content-addressed IDs、state、label/reason、lineage/sample consistency 与 one-observation rule。TEACHER 只能 candidate；golden 必为 HUMAN、supersedes 与 human review attestation 完整；prediction field 不得混入 annotation。`export_teacher_candidates` / `import_teacher_candidates` 只生成 candidate。 | `test_annotation_state_teacher_and_prediction_boundaries_are_fatal` |
| AC-3 | `create_split_manifest` / `validate_split_manifest` 只消费 golden dataset，保存可重放 assignment；identity 与 exact-content group 均不可跨 train/test。三种 strategy 具备 frozen boundary failure。 | `test_split_manifest_has_three_strategy_boundaries_and_no_identity_or_content_leakage` |
| AC-4 | `compute_disposition_metrics(golden, predictions)` 输出 ordered 3×3 confusion matrix、per-class P/R/F1、macro F1、KEEP recall、false reject count/rate、EXCLUDE precision、REVIEW coverage，含空分母 `0.0` 规则。 | `test_metrics_match_hand_calculation_including_empty_denominators` |
| AC-5 | `create_experiment_manifest` 的 ID 只由 identity payload 决定，含 runtime evidence 但 runtime 不改变 ID。`create_prediction_records` 独立存储，不含 gold/state/reasons；`resolve_prediction_provenance` 验证 prediction → experiment → dataset/split → annotation → sample → clean → lineage。 | `test_experiment_prediction_provenance_is_independent_and_resolvable` |
| AC-6 | `run_e0` 使用固定 TF-IDF character n-gram + Logistic Regression。`SYNTHETIC_TEST_ONLY` replay 可用于单元证明但明确不可提升为运行证据；`REAL_EXECUTION` 缺合格 real human golden 时精确 `BLOCKED_NO_GOLDEN_LABELS`，不产生 predictions/metrics。 | `test_e0_is_deterministic_for_synthetic_test_only_and_blocks_without_real_golden` |
| AC-7 | `candidate_registry()` 仅有 E0–E3；E0 mandatory，E1–E3 只有冻结 model/revision/interface/dependency declaration；无 E4 与伪造 metrics。 | `test_e1_to_e3_registry_is_fixed_and_e4_is_absent` |
| AC-8 | Developer 后运行 full pytest、lint/static、deterministic replay、leakage、metrics、provenance assertions；真实 sampling/E0 只能有 real artifact 或 `BLOCKED_NO_GOLDEN_LABELS` evidence。 | Post-implementation QA gate |

## Frozen public API

测试冻结模块 `myresearcher_dataclean.research`。函数输入/输出一律为 JSON-serializable
mapping/list；成功 validator 返回 `None`，contract failure 抛 `ValueError` 并含稳定
failure category。实现可以增加私有 helper，但不得替换以下边界：

```text
sample_clean_records(clean_records, *, input_clean_artifact_id, seed, requested_count,
  sources=None, observed_at_start=None, observed_at_end=None, minimum_text_length=None,
  grouping_mode="record") -> {"manifest", "records"}
create_annotation_record(sample_record, *, dataset_state, disposition, reason_tags,
  annotator_type, annotator_id, annotation_version, annotated_at_utc,
  supersedes_annotation_id=None, golden_review=None) -> annotation
build_annotation_dataset(sample_manifest, annotations, *, prior_annotations=())
  -> {"manifest", "annotations"}
export_teacher_candidates(sample_manifest, sample_records, *, request_metadata) -> export
import_teacher_candidates(teacher_export, teacher_import, *, annotation_version,
  annotated_at_utc) -> annotations
create_split_manifest(dataset, sample_records, *, strategy, seed=None, test_fraction=None,
  cutoff_utc=None, held_out_sources=None) -> split_manifest
validate_split_manifest(split_manifest, dataset, sample_records) -> None
compute_disposition_metrics(golden_annotations, predictions) -> metrics
create_experiment_manifest(...) -> experiment_manifest
create_prediction_records(experiment_manifest, dataset, split_manifest, predictions) -> records
resolve_prediction_provenance(prediction, experiment_manifest, dataset, split_manifest,
  sample_records) -> resolved clean/lineage mapping
run_e0(dataset, sample_records, split_manifest, *, seed, execution_context) -> run result
candidate_registry() -> ordered E0–E3 mapping
```

## Acceptance constraints

- Synthetic fixture labels never satisfy a real golden-label precondition. E0 synthetic
  result must contain `status: SYNTHETIC_TEST_ONLY` and
  `promotable_execution_evidence: false`; it must not be persisted/reported as model outcome.
- Real E0 absence is only `BLOCKED_NO_GOLDEN_LABELS`, with empty predictions and `metrics: null`.
- Tests must never infer disposition/reason from financial text. Fixture labels are opaque
  contract values.
- Any random/sampling/canonical-ID result is replayed with identical ordered input/config/seed.

## Required evidence after implementation

Full pytest; lint/static; deterministic sample/split/E0 replay; all three strategy leakage
assertions; hand-calculated metric regression; provenance tamper assertion; and a repository
artifact proving either real execution or the real-data/golden blocker. Technical Review is a
separate required gate and is not satisfied by this QA matrix.

## Repair QA result

The prior `QA_FAIL / REVIEW_BLOCKED_REPAIR_PENDING` is retained as repair
history. Developer's compatible repair now closes the review findings and Core
QA independently revalidated it: the ROUND-002 suite is **11 passed**, the full
repository suite is **27 passed**, and ruff, compileall, and `git diff --check`
all pass. Risk-based Technical Review then independently revalidated the repair
and recorded `REVIEW_PASS_REVALIDATION` in
`technical-review-revalidation.md`.

| Review repair acceptance | Repair QA result |
| --- | --- |
| strategy/config canonical replay rejects rehashed forged split assignments | PASS |
| sample-manifest membership and full frozen lineage projection are closed by canonical sample bindings | PASS |
| golden/reviewed predecessor exists, is valid, and has matching observation/sample identity | PASS |
| duplicate gold/prediction observation identities fail before metric calculation | PASS |
| resolver closes experiment dataset/split version and hash links to actual artifacts | PASS |

The refreshed real Collector run still has `0 CLEAN` and is therefore an exact
`BLOCKED_NO_GOLDEN_LABELS` E0 result, not a quality claim. Its refreshed manifest
ID is recorded in `qa-report.md`.

## Final acceptance conclusion

| AC | Final conclusion | Current evidence |
| --- | --- | --- |
| AC-1 | PASS | deterministic sampler/filter/group replay; full CLEAN snapshot, canonical sample bindings, input artifact digest and versions retained. |
| AC-2 | PASS | content-addressed annotation states; human-golden attestation and immutable predecessor validation; teacher-candidate and prediction separation enforced. |
| AC-3 | PASS | random/time/source strategies replayed from canonical config; identity/content-group closure and self-rehashed tamper regressions pass. |
| AC-4 | PASS | hand-calculated metric regression passes; duplicate gold/prediction identities fail before joining. |
| AC-5 | PASS | experiment/prediction artifacts are independent and the complete prediction-to-Collector chain rejects self-rehashed dataset/split/lineage tamper. |
| AC-6 | PASS | deterministic E0 runner is implemented; synthetic replay is non-promotable; real empty input returns the exact allowed blocker with no predictions/metrics. |
| AC-7 | PASS | registry is exactly E0--E3; E1--E3 remain declaration-only; E4 is absent. |
| AC-8 | PASS | ROUND-002 11 passed; full pytest 27 passed; ruff, compileall and diff check pass; real read-only blocker evidence and Technical Review revalidation are recorded. |

All mandatory ROUND-002 infrastructure acceptance criteria are satisfied. The
real E0 execution remains `BLOCKED_NO_GOLDEN_LABELS`; this is the AC-6/AC-8
allowed outcome for the currently available empty Collector data, not an open
infrastructure acceptance failure and not `DATA_VALIDATED` evidence.

## Superseded review-blocked QA result

The previous post-implementation QA PASS below is superseded by the risk-based
Technical Review's provenance and leakage findings. Its historical evidence is
retained, but it is not a current acceptance conclusion.

These mandatory regressions were RED at review time and are now retained as
repair history; their independent PASS evidence is in the Repair QA result.

## Superseded post-implementation QA result

| AC | QA conclusion | Evidence |
| --- | --- | --- |
| AC-1 | PASS | deterministic sampler/filter/full-snapshot regression; manifest records input CLEAN digest, schema and cleaning version. |
| AC-2 | PASS | annotation state/teacher/prediction boundary, human-golden attestation, mixed-state rejection, confidence/note validation, and teacher-import source/content-ID tamper regression. |
| AC-3 | PASS | random/time/source split boundaries, observation/content-group leakage rejection, and feasible per-disposition stratification replay. |
| AC-4 | PASS | hand-calculated 3×3 metrics and empty-denominator regression. |
| AC-5 | PASS | runtime-excluded experiment identity, prediction independence, and prediction/split-manifest tamper provenance regressions. |
| AC-6 | PASS | deterministic synthetic-only E0 regression, qualified `REAL_EXECUTION` runner path, and real empty-sample result `BLOCKED_NO_GOLDEN_LABELS` with no predictions/metrics. |
| AC-7 | PASS | registry exactly E0–E3; E1–E3 declaration-only; no E4, external network, or teacher execution path; bounded scikit-learn dependency declared. |
| AC-8 | PASS — infrastructure evidence | full pytest, ruff, compileall, diff check, replay/leakage/metrics/provenance assertions passed; real sampling/E0 blocker evidence is recorded in `qa-report.md`. |

The superseded table above is retained only as historical evidence. The current
conclusion is the Final acceptance conclusion in this document; no real golden
label or model-quality conclusion is claimed.
