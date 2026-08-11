# Decision Log

项目关键决策登记处。新决策由做出该决策的角色填写，Orchestrator 确认。

格式：`D-<NNN> | 日期 | 决策 | 理由 | 状态 | Evidence Level`

| ID | 日期 | 决策 | 理由 | 状态 | Evidence Level |
| --- | --- | --- | --- | --- | --- |
| D-001 | 2026-08-07 | 长期 Agent 能力通过 Git 持久资产积累，而不是依赖长会话记忆 | 模型参数不会随运行自动成长；会话记忆不可检索、不可复用 | ACTIVE | CONFIRMED |
| D-002 | 2026-08-07 | canonical Agent definitions 位于 docs/agent-system/roles；Claude/Codex 配置只是 adapter | 单一事实源，避免 prompt drift | ACTIVE | CONFIRMED |
| D-003 | 2026-08-07 | QA 在开发之前参与 | 测试先行才能约束实现并沉淀 Expected RED tests 与验收矩阵 | ACTIVE | CONFIRMED |
| D-004 | 2026-08-07 | 代码 Review 默认不阻塞研发主流程 | 普通技术债不得阻塞研究；仅数据破坏、严重逻辑错误、安全问题可升级 | ACTIVE | CONFIRMED |
| D-005 | 2026-08-07 | 真实数据执行和专家验收与技术测试分离 | 测试通过不等于研究价值成立 | ACTIVE | CONFIRMED |
| D-006 | 2026-08-07 | 一个项目通过多个 Round 演进，不追求一次完成 | 需求本身不确定，必须靠真实数据、实验与专家验收逐轮演化 | ACTIVE | CONFIRMED |
| D-007 | 2026-08-11 | DataClean 只负责 RAW -> CLEAN，刻意保持 semantic ignorance | sentiment/stance/finance interpretation 属于下游；语义驱动清理可能误删有效文本 | ACTIVE | CONFIRMED（用户边界 + Collector contract） |
| D-008 | 2026-08-11 | 普通 Round 使用 Orchestrator/Developer/QA core，其他角色按风险调用 | 治理必须与轻量数据工程规模匹配；未触发 specialist 不应制造 gate | ACTIVE | CONFIRMED（用户指令） |
| D-009 | 2026-08-11 | ROUND-001 读取 Collector SQLite v1/v2 的 immutable observation/evidence 共同子集，不发明另一套 RAW envelope | v2 只新增 raw retention state，核心 observation/evidence 字段兼容；DataClean 保留 storage/schema versions 与 lineage | ACTIVE | CONFIRMED（CODE_INSPECTION + integration test） |
| D-010 | 2026-08-11 | ROUND-001 的 record identity 只基于 Collector immutable `observation_id`；exact-content key 仅是 relationship/group，不用于 reject 不同 observation | content equality 不等于 observation occurrence/identity equality；按内容驱逐会不可逆地丢失 source item、occurrence 与 lineage | ACTIVE | CONFIRMED（Collector schema CODE_INSPECTION + EXTERNAL_REVIEW） |
| D-011 | 2026-08-11 | HTML normalization 对未证明安全的 markup preserve-by-default，`del/s/strike` 保留可恢复 markers，不建 rich-text AST | 只保留内部文本会消除删除/划除关系；可见 markers 是 ROUND-001 内最小可回放方案 | ACTIVE | CONFIRMED（EXTERNAL_REVIEW + CODE_INSPECTION） |
| D-012 | 2026-08-11 | 已通过 validation 的 non-CLEAN outcome 保留 full available Collector lineage，`INVALID_RECORD` 仅作 best-effort | validation 后已拥有完整 lineage 事实，不应因 cleaning outcome 丢失；无效输入则不能补造 | ACTIVE | CONFIRMED（EXTERNAL_REVIEW + CODE_INSPECTION） |

## 追加记录规则

- 状态：ACTIVE（生效）/ SUPERSEDED（被替代，注明替代者）/ REJECTED（被否定）。
- 关键结论同时标注 Evidence Level（`docs/agent-system/protocol.md`）。
- 被否定或替代的决策保留记录，不删除。
