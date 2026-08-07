# Current Round

状态：**NO_ACTIVE_ROUND**

- 含义：当前没有正在执行的 Round，等待合法的 Round Start Trigger。这不是死锁状态。
- 新 Round 只能通过 canonical ROUND_START_TRIGGER 转移创建，完整规则见 `docs/agent-system/state-machine.md`；此处不重复定义。
- Phase 0 说明：Bootstrap 在没有合法 Trigger 时不得自动进入 Round 001；用户明确要求启动研发时，Orchestrator 必须创建 Round。

状态机位置：不适用（无 Round 运行中）。

维护者：Program Orchestrator
最近更新：2026-08-07
