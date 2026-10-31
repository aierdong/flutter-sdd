# Follow-ups

只记录已明确承诺未来处理的事项，不是所有「明确不做」的集合。`sdd-grill` 每次启动时检查本文件；待办必须有可判断的触发条件和完成标准。

状态：`待办` / `进行中` / `已完成` / `已取消`。按用户决定更新待办/进行中；有验证证据后才标记已完成，只有用户明确取消时才标记已取消。

| ID | 状态 | 事项 | 来源 spec | 触发条件 | 完成标准 |
|---|---|---|---|---|---|
| FUP-001 | 待办 | 补齐 FSD-11 严格分析器配置，并按该规范完成格式、分析和测试验证 | [p00-001 grill.md：Q12](specs/p00-001-schema-tables-page/grill.md) | 下一份需要新增或修改 Dart 代码的 spec，或专门处理分析器配置的 spec，启动 `sdd-grill` 时检查并决定由该 spec 承接还是单独建 spec | `analysis_options.yaml` 包含 FSD-11 要求的严格选项与 lint 规则；`dart format`、`flutter analyze`、`flutter test` 均通过 |
| FUP-002 | 进行中 | 建立 UI 规范（组件库、布局密度、间距与字号），并据此修订 `coding.md` 的 FSD-12 依赖白名单 | [p00-003 grill.md：Q2](specs/p00-003-lightweight-sdd-plan/grill.md) | `p00-001-schema-tables-page` 进入计划阶段前；或任何涉及 UI 组件库 / 布局密度的 spec 启动 `sdd-grill` 时 | `docs/standards/ui.md` 存在并在 `steering.md` 索引登记（已完成，v1）；FSD-12 允许新增的依赖清单包含该组件库或明确排除它（未完成）；`p00-001` 第 6 节的「依赖」决策已随之更新（未完成，按 `覆盖` 机制可先于白名单推进） |
