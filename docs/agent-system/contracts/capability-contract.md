# Capability Contract

项目能力统一登记在 `docs/state/capability-ledger.md`，每条能力必须包含：

| 字段 | 说明 |
| --- | --- |
| Capability ID | 如 CAP-001 |
| Description | 能力描述 |
| Owner | 负责角色 |
| Implementation Location | 实现位置（代码/文档路径） |
| Validation Location | 验证位置（测试/实验路径） |
| Maturity | 成熟度（见 `protocol.md`：PROPOSED / PROTOTYPE / TESTED / DATA_VALIDATED / EXPERT_ACCEPTED） |
| Known Limitations | 已知限制 |
| Last Validated Round | 最近验证轮次 |

## 规则

- 成熟度必须与证据匹配，禁止跳级声明。
- 能力存在时必须同时登记 Known Limitations。
- 新能力提案（PROPOSED）也要登记，不隐藏。
- 能力被否定时保留记录并标注原因，不直接删除。
- 任何人不允许登记尚未存在的「数据读取 / 清洗 / 情绪分析 / 模型 / 聚合」能力。
