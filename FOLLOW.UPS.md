# Follow-ups

只记录已明确承诺未来处理的事项，不是所有「明确不做」的集合。`sdd-grill` 每次启动时检查本文件；待办必须有可判断的触发条件和完成标准。

状态：`待办` / `进行中` / `已完成` / `已取消`。按用户决定更新待办/进行中；有验证证据后才标记已完成，只有用户明确取消时才标记已取消。

| ID | 状态 | 事项 | 来源 spec | 触发条件 | 完成标准 |
|---|---|---|---|---|---|
| FUP-001 | 待办 | 补齐 FSD-11 严格分析器配置，并按该规范完成格式、分析和测试验证 | [p00-001 grill.md：Q12](specs/p00-001-schema-tables-page/grill.md) | 下一份需要新增或修改 Dart 代码的 spec，或专门处理分析器配置的 spec，启动 `sdd-grill` 时检查并决定由该 spec 承接还是单独建 spec | `analysis_options.yaml` 包含 FSD-11 要求的严格选项与 lint 规则；`dart format`、`flutter analyze`、`flutter test` 均通过 |
