# Sentiment Knowledge — Archived Bootstrap Scope

状态：**OUT_OF_SCOPE_FOR_DATACLEAN**（2026-08-11）

sentiment、stance、emotion、action intent 的标签、标注规范、Golden Set、模型和评估属于下游 DataLabel / Sentiment / Analyze。本文件不再积累这些资产，也不得作为 DataClean cleaning/drop 的依据。

DataClean 内唯一允许的 sentiment specialist 输入是：某个 cleaning operation 是否破坏未来分析可能需要的表面信息。该输入必须以具体 before/after 反例进入当前 Round regression，不执行分类。参见 `docs/agent-system/roles/sentiment-expert.md`。
