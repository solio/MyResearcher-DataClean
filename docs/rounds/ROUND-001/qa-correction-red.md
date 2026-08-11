# ROUND-001 QA Correction RED Evidence

> Role：Core QA
>
> 状态：**CORRECTION_EXPECTED_RED**
>
> 日期：2026-08-11

## Scope

这是当前 ROUND-001 的 contract correction QA gate，不是新 Round。QA 已依据
`contract.md`、`input-contract.md` 与 `data-contract-correction.md` 重写
`acceptance.md`，并在修改 production code 之前冻结最小 regression。Finance / Sentiment
Expert 未调用。

旧 AC-5 的 `normalized(title, content) equality -> EXACT_DUPLICATE rejection`
已明确 supersede；旧 Technical Review PASS 不作为本次 correction 的通过证据。

## Frozen regressions

- 不同 `observation_id` / `source_item_id` 且 normalization 后内容相同：两个 observation
  都是 CLEAN；后续成员带稳定 `duplicate_content_of`；content relationship 不进入
  rejection。
- 同一 `observation_id` 在有序 batch 重复交付：明确 input-contract failure；不按
  content 选择代表。
- `del` / `s` / `strike` 的成对 meaning-bearing markers 与 child text 可恢复；未知
  markup preserve-by-default。
- post-validation `EMPTY_CONTENT` 保留 full available Collector lineage；
  `INVALID_RECORD` best-effort 保留输入中所有可用同类字段。
- corrected report 字段及四个计数关系；Python 与 CLI deterministic replay。

## Commands and environment

```text
$ python --version
Python 3.13.9

$ python -m pytest --version
pytest 8.4.2

$ python -m compileall -q tests
PASS

$ git diff --check -- docs/rounds/ROUND-001/acceptance.md tests/test_pipeline.py tests/test_cli.py
PASS

$ python -m pytest
7 failed, 8 passed in 0.13s
```

`python -m pytest` 是 full repository test suite；exit code 为 1，符合 Developer correction
前的预期 RED。

## RED failure evidence

| Regression | Current failure | Corrected expectation |
| --- | --- | --- |
| CLI report semantics | `KeyError: 'exact_content_duplicate_count'`；当前仍输出旧 `duplicate_count` | 输出 corrected fixed fields，并满足计数关系 |
| Meaning-bearing HTML | CLEAN content 为 `明天涨停 明天跌停；旧值 新值；旧结论 新结论`，`<del>` / `<s>` / `<strike>` markers 被删除 | 成对、可见、可恢复 markers 和 child text 保留 |
| Rejection lineage | `EMPTY_CONTENT` lineage 缺少 `collector_storage_version`（并缺 schema/collector/parser/fingerprint/drift 等） | post-validation rejection full lineage；invalid best-effort all available lineage |
| Distinct observation retention | 期望 `['obs-1', 'obs-2']`，实际只有 `['obs-1']` | 两个不同 identity 都输出 CLEAN |
| Duplicate observation identity | `DID NOT RAISE ValueError` | 明确 input-contract failure，不选择代表 |
| Mixed report counts | 实际 `cleaned_count=1`、`rejected_count=3` 且 `reason_distribution` 含 `EXACT_DUPLICATE` | `cleaned_count=2`、`rejected_count=2`、content relationship 不进入 reasons |
| Deterministic relationship replay | 两次 Python result 本身相等，但都只保留一条 CLEAN；期望两条 | 两条 observation 均保留，stable content key/predecessor metadata 可回放 |

通过的 8 个测试仅说明未触及的既有读取/基础清理行为仍可运行，不构成 correction
QA PASS。CLI byte-for-byte comparison 与 Python `first == second` 在到达 corrected
behavior assertions 前已通过，因此当前实现是“可重复地产生错误的 data-loss 结果”，不能据此恢复 capability evidence。

## Handoff

Developer 应只实现已冻结 contract：identity/content relationship、meaning-bearing HTML、
rejection lineage 与 report semantics。实现后由 QA 运行 full pytest、lint/static checks、
duplicate occurrence、HTML、lineage 与 deterministic replay；全部通过后再交给 risk-based
Technical Reviewer。Technical Review 重新 PASS 前不得恢复 `QA_PASS / REAL_DATA_BLOCKED`。
