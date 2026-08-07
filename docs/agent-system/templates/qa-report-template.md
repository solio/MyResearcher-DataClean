# QA Report

> Round：ROUND-<NNN> ｜ QA 角色：QA Test Designer ｜ 日期：<YYYY-MM-DD>

## 测试设计状态

- Acceptance Matrix：<路径>（<已冻结/已更新>）
- Golden Fixtures：<数量> 条（<路径>）
- Synthetic Cases：<数量> 条（<路径>）
- Expected RED tests：<数量> 条（<路径>）
- 人工抽查计划：<方式与样本量>
- 真实数据验收方式：<方式>

## 执行结果

| 测试组 | 通过 | 失败 | 证据类型 |
| --- | --- | --- | --- |
| <单元测试> | <n> | <n> | UNIT_TEST |
| <Golden Set> | <n> | <n> | GOLDEN_SET |
| <人工抽查> | <n> | <n> | MANUAL_REVIEW |

## 失败与路由

| 失败项 | 分类（标签/规范/实现/测试本身） | 路由目标 | Two Repair 计数 |
| --- | --- | --- | --- |
| <ID> | <分类> | <目标> | <0/1/2> |

## 新增 Regression Cases

- <案例与来源 Bug>

## 结论

- <QA_PASS / QA_FAIL>
