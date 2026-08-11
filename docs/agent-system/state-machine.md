# State Machine — Lean Round

## Core states

| 状态 | 最小 Artifact | 下一状态 |
| --- | --- | --- |
| PLANNED | Round Contract draft、trigger、scope/out of scope | READY / BLOCKED |
| READY | 冻结的 acceptance、invariants、fixtures/negative cases、真实数据计划 | IMPLEMENTING / BLOCKED |
| IMPLEMENTING | 当前实现与测试证据 | VALIDATING；失败回 IMPLEMENTING；或 BLOCKED |
| VALIDATING | QA 结果、真实数据执行统计与抽样（若 contract 要求） | IMPLEMENTING / ACCEPTED / BLOCKED |
| BLOCKED | 原因、证据、恢复条件、责任层 | 条件满足后回到正确 core state |
| ACCEPTED | Orchestrator 对全部 mandatory AC 的结论 | CLOSED |
| CLOSED | Round 关闭记录与 state/capability/decision/backlog 更新 | NO_ACTIVE_ROUND 或合法 trigger 的下一 Round |

`NO_ACTIVE_ROUND` 是 Round 之外的项目状态，不是需要走过的 Round gate。

## Start transition

```text
NO_ACTIVE_ROUND + valid ROUND_START_TRIGGER
  -> CREATE docs/rounds/ROUND-<NNN>/contract.md
  -> update docs/state/current-round.md
  -> PLANNED
```

Trigger 只有：用户明确启动具体研发；上一 Round 已接受且记录 approved next question 并有继续上下文；Decision Log 中具体问题为 `APPROVED_FOR_NEXT_ROUND`。无 trigger 不创建 Round。

## Mandatory path

- `PLANNED -> READY`：Orchestrator 与 QA 已在实现前冻结 lightweight acceptance。
- `READY -> IMPLEMENTING`：输入/输出边界和 negative cases 可执行。
- `IMPLEMENTING <-> VALIDATING`：Developer 与 QA 循环；Two Repair Rule 生效。
- `VALIDATING -> ACCEPTED`：当前 Round 的所有 mandatory AC 都有对应证据；若要求真实数据，则 synthetic tests 不能替代。
- `ACCEPTED -> CLOSED`：持久状态与资产更新完成。

## Optional specialist activities

Research、experiment、architecture、technical review、operator execution 和 expert review 是按 `workflow.md` 触发的活动，不是普通 Round 必经 state。需要时把活动及 artifact 记录在当前 core state 下；未触发时不得制造空报告或阻止流转。

任何 core state 都可进入 `BLOCKED`。数据破坏、安全、breaking schema 未决必须立即阻塞；普通 improvement 与 non-blocking review finding 进入 backlog。
