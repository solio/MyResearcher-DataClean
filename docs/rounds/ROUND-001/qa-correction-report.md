# ROUND-001 QA Correction Validation Report

> Role：Core QA
>
> 状态：**QA_CORRECTION_PASS**（后续 Technical Review correction 已 PASS）
>
> 日期：2026-08-11

## Scope and independence

这是现有 `ROUND-001 — Collector Input Contract & Minimal Cleaning Baseline` 内的
correction validation，不是新 Round。QA 直接检查了冻结的 contract、input contract、Data
Architect correction、acceptance、RED evidence、production source 与全部 tests；Developer
handoff 只作为索引，不作为通过证据。Finance / Sentiment Expert 未调用。

旧 `technical-review.md` 的 PASS 仍为 superseded historical evidence。本报告只证明 QA
correction gate；要求的后续 risk-based Technical Review 已完成并以
`technical-review-correction.md` 重新 PASS。

## Independent findings

- **Record identity / content relationship**：batch 在 record processing 前拒绝重复的非空
  `observation_id`。两个不同 observations 清理成相同 `(title, content)` 时均输出 CLEAN，
  `exact_content_key` 相同，稳定后续成员以 `duplicate_content_of` 指向首条 `clean_id`；没有
  `EXACT_DUPLICATE` rejection/drop。
- **HTML preservation**：无属性 layout-only tag 转换边界 whitespace/newline；无属性 safe
  presentation wrapper 才剥离 tag syntax。`del` / `s` / `strike`、unknown markup、以及带属性
  的 `b` / `div` / `del` 均保留 start/end marker 与 child text。QA 新增 attributed-markup
  regression，将此前仅有 direct probe 的行为冻结为自动化证据。
- **Rejection lineage**：post-validation `EMPTY_CONTENT` 使用 full lineage；
  `INVALID_RECORD` 使用 best-effort lineage。storage/schema/collector/parser versions、fact
  fingerprint、drift reference、raw evidence 与 scopes 均有断言；QA 进一步加入 v2
  `PRESENT` / `PURGED` retention metadata，确认 rejection 原样保留 available evidence。
- **Reporting**：固定 corrected fields 均存在。exact-content 后续 observation 是 CLEAN 子集，
  不进入 reason distribution；mixed batch 覆盖 unchanged、modified、content relationship、
  `EMPTY_CONTENT` 与 `INVALID_RECORD`。
- **Replay and integration**：同一有序 Python input 两次结果相等；同一 SQLite input 的
  CLEAN JSONL、rejections JSONL 与 report 三个文件 byte-identical。v1 由本仓 SQLite/CLI
  fixture 覆盖；v2 由当前 sibling Collector persistence 生成数据库并完成读取和清洗。两者
  均为 synthetic test evidence，不是 AC-8 real-data evidence。

## Commands and evidence

```text
$ python --version
Python 3.13.9

$ python -m pytest --version
pytest 8.4.2

$ python -m pytest
................                                                         [100%]
16 passed in 0.08s

$ python -m pytest -q <11 correction / replay / v1-v2 integration nodes>
...........                                                              [100%]

$ python -m ruff check src tests
All checks passed!

$ python -m compileall -q src tests
PASS

$ git diff --check
PASS
```

定向 11 项包括：distinct-observation retention、duplicate observation identity failure、
`del/s/strike`、unknown markup、attributed markup、full/best-effort lineage、mixed report
equations、Python deterministic replay、CLI byte-identical replay、Collector v1 read 与当前
Collector v2 persistence integration。

## Report semantics accepted

```text
input_count = cleaned_count + rejected_count
cleaned_count = unchanged_count + modified_count
exact_content_duplicate_count <= cleaned_count
sum(reason_distribution.values()) = rejected_count
```

- `input_count` 计进入 record-level validation/cleaning 的 candidates。
- `cleaned_count` 保留每个独立 observation，包括 exact-content group 的全部成员。
- `unchanged_count` 与 `modified_count` 只划分 CLEAN observations。
- `exact_content_duplicate_count` 只计 CLEAN group 稳定首条之后的成员。
- `rejected_count` 与 `reason_distribution` 只计 record-level rejection；content equality 不计。

## Acceptance and remaining gates

AC-1–AC-7：**PASS — QA correction validation**。

AC-8 在 QA 交接时为 **BLOCKED_DATA_UNAVAILABLE**，synthetic fixtures 不得替代。后续
Technical Review correction 已 PASS，并在 `real-data-validation.md` 中对新出现的真实、
静止 Collector SQLite 完成只读探针；该库含 0 observations，因此当前
精确 blocker 已更新为 **BLOCKED_NO_REAL_OBSERVATIONS**。

QA 阶段未更新 `docs/state/` 或 capability evidence。在后续 Technical Review correction
PASS 后，Program Orchestrator 已基于完整证据恢复
`QA_PASS / REAL_DATA_BLOCKED` 和 CAP-001 `TESTED`。
