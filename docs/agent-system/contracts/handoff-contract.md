# Handoff Contract

所有角色间交接必须满足本契约。**禁止只写「请继续」。**

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
- Handoff 记录存放在 `docs/rounds/ROUND-<NNN>/handoffs/`（或当前 Round 文档中）。
- 接收方必须重新读取状态文件与 Round Contract，不允许仅凭 handoff 文本记忆继续。
