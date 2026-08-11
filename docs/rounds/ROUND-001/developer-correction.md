# ROUND-001 Developer Correction Evidence

> Role：Core Developer
>
> 状态：**DEVELOPER_CORRECTION_DONE — QA / TECHNICAL REVIEW PENDING**
>
> 日期：2026-08-11

## Scope

本次改动属于现有 `ROUND-001 — Collector Input Contract & Minimal Cleaning
Baseline` 的 contract correction；没有创建新 Round、架构、workflow、agent、phase 或治理层。
实现以 `contract.md`、`input-contract.md`、`data-contract-correction.md`、
`acceptance.md` 与 `qa-correction-red.md` 的冻结行为为准。

## Implementation

- `pipeline.py` 在任何 record-level processing 前检查有序 batch 中重复的非空
  `observation_id`，重复 identity 明确抛出 `ValueError` input-contract failure。
- 清理后 `(title, content)` 的 canonical SHA-256 命名为 `exact_content_key`。不同
  observations 始终各自产生 CLEAN；同组首条 `duplicate_content_of = null`，后续成员
  稳定指向首条 `clean_id`。exact-content equality 不再产生 rejection。
- `normalization.py` 对无属性 layout-only tags 保留边界 whitespace/newline，对显式
  presentation allowlist 的无属性 wrapper 只移除 tag syntax；`del` / `s` / `strike`、
  未知 tags、以及带未证明属性的 wrappers 保留可恢复 markers 与 child text。
- post-validation `EMPTY_CONTENT` 使用 full lineage；`INVALID_RECORD` 的 best-effort
  lineage 覆盖所有可用 storage/schema/collector/parser/fingerprint/drift/evidence/scopes
  字段，并保留 source/item identity。
- report 移除旧 `duplicate_count` 语义，固定输出
  `exact_content_duplicate_count`；实现检查四个冻结计数关系。`EXACT_DUPLICATE` 已从
  record-level rejection path 删除。

仅修改 production source：

- `src/myresearcher_dataclean/normalization.py`
- `src/myresearcher_dataclean/pipeline.py`

## Verification evidence

```text
$ python -m pytest
...............                                                          [100%]
15 passed in 0.08s

$ python -m pytest -q <8 frozen correction regressions>
........                                                                 [100%]

$ python -m ruff check src tests
All checks passed!

$ python -m compileall -q src tests
PASS

$ git diff --check
PASS
```

八项定向回归覆盖 duplicate occurrence retention、duplicate observation identity failure、
`del/s/strike`、unknown markup preserve-by-default、full/best-effort lineage、report
equations、Python deterministic replay 与 CLI byte-identical replay。另以直接 normalization
probe 确认带属性的 `b` / `div`、带 `href` 的 `a`、meaning-bearing tags 与 unknown tags
保留可恢复结构。

以上证据均为 synthetic contract/test evidence，不是 AC-8 真实 Collector data evidence。

## Handoff

Developer correction 已完成；状态尚不能恢复为 `QA_PASS / REAL_DATA_BLOCKED`。下一 gate
仍是 Core QA 全量复验，随后由 risk-based Technical Reviewer 重新审查 dedup semantics、
core pipeline、lineage 与 semantic preservation。旧 Technical Review PASS 不作为本次
实现的通过证据。
