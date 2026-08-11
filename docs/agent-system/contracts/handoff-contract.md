# Handoff Contract

发生责任所有权切换、跨执行器继续或 specialist 调用时，handoff 必须满足本契约。Developer/QA 同一工作上下文中的日常反馈不要求每次制造独立文档；但禁止只有「请继续」。

## 必须记录字段

| 字段 | 说明 |
| --- | --- |
| From | 交接角色 |
| To | 接收角色 |
| Current State | 当前状态机位置与原因 |
| Artifacts | 交接的 artifact 清单（路径） |
| Evidence | 已完成工作的证据 |
| Decisions | 本次工作做的决定 |
| Unresolved Issues | 未解决问题（含为何未解决） |
| Exact Next Responsibility | 接收方精确的下一步任务与完成定义 |

## 规则

- Exact Next Responsibility 必须可执行、可验收（做什么、产出什么、怎么算完成）。
- 存在未解决问题时 Unresolved Issues 不得留空。
- Handoff 可存放在 `docs/rounds/ROUND-<NNN>/handoffs/` 或当前 Round 的验证/状态文档中，不创建空 artifact。
- 接收方必须重新读取状态文件与 Round Contract，不允许仅凭 handoff 文本记忆继续。
