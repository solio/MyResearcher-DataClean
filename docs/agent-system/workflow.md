# Workflow — 研发流程

本流程是**循环，不是瀑布**：每轮失败都会路由回正确阶段，而不是从头重来，也不是一次性做完。

## Stage A — 独立需求研究

Finance Expert / Sentiment Expert / Data Architect 各自**独立**研究。

- 各自产出：研究报告、假设、领域问题、标签/数据层建议。
- 完成后进入 Stage B。

## Stage B — 整合与设计

Requirements & Solution Architect 整合专家意见。

- 如果存在未知问题：进入 `research → experiment → expert reconsideration` 循环，直到收敛。
- 产出：需求、Acceptance Criteria、Out of Scope、Hypothesis、Experiment、架构、Data Contract、可增量交付 Slice。

## Stage C — QA 测试设计（开发前）

QA Test Designer 在**代码出现之前**定义：

- Acceptance Matrix
- Golden Fixtures
- Expected RED tests
- 人工抽查计划
- 真实数据验收方式

## Stage D — 开发与 QA 循环

Developer ↔ QA 循环。

- Developer 每次只实现一个明确 Slice，必须运行真实测试。
- 真实 Bug 必须进入 regression。
- 同一问题两轮失败（Two Repair Rule）返回上层。

## Stage E — 技术完成审查

Technical Completion Reviewer 只审当前需求完成度。

- 不得因为未来优化 BLOCK。
- 通过后进入 Stage F。

## Stage F — 真实数据执行

Operator 对代表性数据真正执行。

- 产出：运行报告、数据分布、异常样本、无法处理样本、与上一版本差异。
- 不得修改数据让结果更漂亮。

## Stage G — 专家验收

Finance Expert / Sentiment Expert / Data Architect 分别**独立**验收真实输出。

- Expert Acceptance Coordinator 汇总。
- 发现问题后必须按 `protocol.md` Failure Routing 路由回正确阶段。
- 拒绝后不允许不经专家直接回到 Developer 打补丁。

## Round Close（成功路径）

成功关闭 Round：

- 更新 Knowledge（`docs/knowledge/`）
- 更新 Capability Ledger（`docs/state/capability-ledger.md`）
- 更新 Decision Log（`docs/decisions/decision-log.md`）
- 更新 Backlog（`backlog/`）
- 归档 Round 档案（`docs/rounds/ROUND-<NNN>/`）

关闭后，未来才开启下一 Round。

## 失败路径

- Stage C/D 失败 → 返回对应阶段或上层；记录为知识或 regression 资产。
- Stage G 专家拒绝 → 分类后路由回正确阶段。
- 任何阶段出现数据破坏、严重逻辑错误、安全问题 → 立即 BLOCK 并升级（见 `state-machine.md`）。
