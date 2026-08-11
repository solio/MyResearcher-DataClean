# Agent System

本目录是 DataClean 研发组织的 Source of Truth。它服务于业务交付，不是项目本身的交付目标。

## 核心模型

```text
Orchestrator -> Contract / Acceptance Definition -> QA
              -> Developer <-> QA -> Real Data Validation
              -> Round Acceptance -> Close
```

常驻角色只有 Orchestrator、Developer、QA。`roles/` 中其他定义作为 specialist toolbox 保留并按风险调用；普通 Round 不因缺少 Finance、Sentiment、Solution Architecture、Technical Review、独立 Operator 或 Expert Acceptance Coordinator 而被阻塞。

## 不变原则

- Git 是共享事实源；聊天不是项目契约。
- QA 在实现之前定义轻量、可执行的验收标准。
- RAW 不可变，RAW -> CLEAN 可回放、可追溯、可审计。
- 相同 input + cleaning version 产生相同 output。
- 失败回到正确责任层；Two Repair Rule 防止无限 patch。
- 技术测试、真实数据验证和领域专家结论是不同证据层，只有当前 Round 明确需要的层才成为 gate。
- DataClean 保持 semantic ignorance，不承担下游 sentiment/label/analyze 职责。

## 目录

- `workflow.md`：core workflow 与 specialist 触发条件
- `state-machine.md`：七个 core states 与可选 specialist 活动
- `protocol.md`：证据、成熟度、失败路由和决策门
- `roles/`：核心角色与 specialist canonical definitions
- `contracts/`：Round、handoff、evidence、capability 契约
- `templates/`：轻量 artifact 模板

Claude/Codex adapter 只引用 canonical role，不得另行发明强制流程。
