# Evidence Contract

所有关键结论必须声明证据来源。本契约定义证据类型及其使用规则。

## 证据类型

| 类型 | 含义 |
| --- | --- |
| UNIT_TEST | 单元/集成测试结果 |
| GOLDEN_SET | 金标集评测结果 |
| MANUAL_REVIEW | 人工抽查/复核 |
| REAL_DATA | 真实数据运行结果 |
| STATISTICAL_ANALYSIS | 统计分析 |
| DOMAIN_EXPERT | 领域专家判断 |
| CODE_INSPECTION | 代码审查 |

## 规则

- 关键结论必须标注证据类型 + Evidence Level（`protocol.md`）。
- 同一结论可引用多类证据；声明时必须列出全部类型。
- DOMAIN_EXPERT 证据必须记录专家角色与日期。
- REAL_DATA 证据必须附带 processing version / rule version。
- 无法提供证据的声明降级为 HYPOTHESIS。
- 证据与结论一起记录在 Round 档案中，不允许结论与证据分离存放。
