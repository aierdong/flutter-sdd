---
translated: true
source: .claude/skills/kiro-spec-tasks/SKILL.md
generated: 2026-10-29
---

# kiro-spec-tasks：把需求和设计拆成可执行任务

> 本文件是英文原文的中文译本，供阅读与评审。事实以 `.claude/skills/kiro-spec-tasks/SKILL.md` 为准。

## 技能元信息

| 项 | 内容 |
|---|---|
| name | `kiro-spec-tasks` |
| description | 依据需求和设计生成实现任务。需要产出可执行任务清单时使用。 |
| allowed-tools | `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Agent` |
| 参数提示 | `<feature-name> [--sequential]` |
| 共享规则 | `tasks-generation.md`、`tasks-parallel-analysis.md` |

## 核心任务

- **成功标准**：
  - 所有需求都映射到具体任务。
  - 任务大小合适（每个 1–3 小时）。
  - 任务之间有清晰的层次和推进关系。
  - 任务描述用自然语言，聚焦能力而不是代码结构。
  - 影响持久化的规格，包含迁移、契约、数据模型和 schema 漂移证据的显式任务。
  - 写 `tasks.md` 之前，做一次轻量的任务图可执行性体检。

## 执行步骤

### 第 1 步：收集上下文

如果对话里已经带有 steering / spec 上下文，就不要重复读文件。否则加载全部必要上下文：

- `.kiro/specs/{feature}/spec.json`、`requirements.md`、`design.md`。
- `.kiro/specs/{feature}/tasks.md`（如果存在，进入合并模式）。
- 核心 steering：`product.md`、`tech.md`、`structure.md`。
- 以下情况才读额外的 steering 文件：与需求覆盖、设计边界、运行前置条件，或影响任务可执行性的团队约定直接相关。
- `.kiro/steering/testing-profiles.md` 存在时**必须加载**。它定义了任务必须带的测试档位标注，以及 `full` 档位的原生环境前置条件。
- 如果设计里有 Persistence Delta，或本特性触及 Application SQLite 持久化、数据模型文档、迁移、仓储、schema 扫描缓存、项目配置、生成器配置、执行历史、schema 影响处理，还要加载 `docs/data-model/sqlite-implementation-contract.md`（存在时）和相关 `docs/data-model/*.md`。
- 确定执行模式：
  - `sequential = (sequential 参数为真)`

### 第 2 步：生成实现任务

- 读本 skill 目录下的 `rules/tasks-generation.md`，取生成原则。
- 读本 skill 目录下的 `rules/tasks-parallel-analysis.md`，取并行判定标准。
- 读 `.kiro/settings/templates/specs/tasks.md`，取格式（支持 `(P)` 标记）。

#### 并行调研

下面几块彼此独立，可以并行：

1. **上下文加载**：spec 文档（`requirements.md`、`design.md`）、steering 文件。
2. **规则加载**：`tasks-generation.md`、`tasks-parallel-analysis.md`、tasks 模板。

全部完成后，先综合再生成任务。

**按规则生成任务清单**：

- 使用 `spec.json` 指定的语言。
- 把所有需求映射到任务，只列数字需求 ID（逗号分隔）。不要加描述性后缀、括号、翻译或自由标签。
- 确保设计里的全部组件都有对应任务。
- 检查任务推进是否合乎逻辑、逐步增量。
- 每个可执行任务至少有一条细节条目，用可观察的方式说明"做完是什么样"。
- 给每个可执行任务**恰好一个** `_Test profile: fast|local|integration|full|none_` 标注，取能提供所需验证证据的最低档位。
- `none` 只能用于"按设计就没有可运行验证"的任务；这种任务必须说明一种可观察的非测试验证方式。
- 每个 `full` 任务要加 `_Full environment:_`，写明所需的 DSN 变量名；当夹具或 smoke 路径会修改目标库时，还要写明 `LOOMIDBX_SPIKE_ALLOW_MUTATION=1`。**永远不要写变量的值。**
- 环境校验不要做成复选框任务，也不要加编号任务或 `_Depends:_` 依赖边。只要选中的计划里含 `full` 任务，`kiro-impl` 会在特性工作开始前统一做一次快速失败门禁。
- 常规实现任务要留在单一责任边界内；跨边界的活儿，做成显式的集成任务。
- 如果设计影响持久化，必须包含这些显式任务：
  - 更新迁移与仓储
  - 更新 `docs/data-model/sqlite-implementation-contract.md`
  - 设计契约变化时，更新受影响的 `docs/data-model/*.md`
  - 生成或刷新 schema 快照/巡检测试或证据
  - 把已知的每处 schema 差异归类为 `implemented`、`alias`、`phase-subset`、`deferred`、`temporary`、`deviation`、`removed-from-design`
- 在 `!sequential` 时，给满足并行条件的任务加 `(P)` 标记。
- 对"看起来能并行、实际不安全"的任务，明确写出阻止 `(P)` 的依赖。
- sequential 模式为真时，完全不加 `(P)`。
- 已有 `tasks.md` 时，与新内容合并。

### 第 3 步：评审任务计划

- 任务计划先放在工作记忆里，**此时还不要写 `tasks.md`**。
- 执行 `rules/tasks-generation.md` 里的 `Task Plan Review Gate`。
- 检查覆盖度：
  - 每个需求 ID 至少出现在一个任务里。
  - 每个设计组件、契约、集成点、运行前置条件和验证关注点都有对应任务。
  - 设计里有 Persistence Delta 时，任务计划包含迁移/仓储工作、数据模型契约更新、schema 快照或巡检证据，以及可复核的 schema 漂移证据。
- 检查可执行性：
  - 每个子任务是 1–3 小时能做完的执行单元。
  - 每个子任务有可验证的交付物。
  - 每个可执行子任务都写了可观察的完成态。
  - 没有隐藏的前置条件。
  - `_Depends:_`、`_Boundary:_`、`(P)` 标记仍然与依赖图和架构边界一致。
- 如果问题只出在任务计划局部，就地修好，重跑门禁再写。
- 修复循环最多 2 轮。
- 如果评审暴露真正的需求/设计缺口或矛盾，停下来把用户送回需求/设计阶段，**不要靠编造填充任务把坑填上**。

### 第 3.5 步：任务图体检

写 `tasks.md` 之前，对任务图做一次轻量的独立体检。

- 能派新子代理就派一个全新评审子代理做这步。否则就在当前上下文里做同样的检查。
- 只给它文件路径、任务计划草稿，以及（如果是在更新已有 `tasks.md`）合并上下文。评审者应自己读 `requirements.md`、`design.md` 和任务生成规则，**不要依赖父上下文给的覆盖度摘要**。
- 只查这几件事：
  - 隐藏的前置条件或缺失的搭建任务
  - 依赖或排序错误
  - 任务之间边界重叠或权属不清
  - 任务过大、过虚、跨边界却不是显式集成任务，或缺可验证交付物
  - 需求、设计、任务图之间新引入的矛盾
- 只给一个结论：
  - `PASS`
  - `NEEDS_FIXES`
  - `RETURN_TO_DESIGN`
- 结论是 `NEEDS_FIXES`：修一轮草稿，再体检一次（只一次）。
- 结论是 `RETURN_TO_DESIGN`：不写 `tasks.md`，直接指回需求/设计里的具体缺口。
- 这一步要有边界，别把它做成第二轮完整规划。

### 第 4 步：定稿

**写 `tasks.md`**：

- 创建或更新 `.kiro/specs/{feature}/tasks.md`。
- 更新 `spec.json` 元数据：
  - 设置 `phase: "tasks-generated"`。
  - 设置 `approvals.tasks.generated: true`。
  - 更新 `updated_at` 时间戳。
- 展示任务摘要（任务数、主要分组、并行标记）。
- 回复："任务已生成。用 `/kiro-impl {feature}` 开始实现。"

## 关键约束

- **任务必须接入系统**：每个任务都要与系统相连，不允许孤立工作。
- **边界标注**：`(P)` 任务必须有，所有任务建议有（`_Boundary: ComponentName_`）。
- **显式依赖**：跨边界且不直观的依赖，用 `_Depends: X.X_` 声明。
- **测试档位标注**：每个可执行任务声明恰好一个 `_Test profile: fast|local|integration|full|none_`；`full` 任务还要声明 `_Full environment:_`，且不含密钥值。环境校验永远不做成复选框任务，因为 `kiro-impl` 会做整计划的统一门禁。
- **可执行交付物粒度**：每个任务必须产出可验证交付物（文件、端点、UI 组件、配置）。基础设施类工作（项目脚手架、manifest、宿主集成、构建配置）必须显式成任务，**不要假设它们已经存在**。
- **可观察的完成态**：每个可执行子任务至少有一条细节条目，让人不用新增记账字段就能看到完成状态。
- **没有隐含前置条件**：任务需要运行时、SDK、框架初始化或配置文件时，这些搭建工作必须是它前面一个独立任务。
- **持久化契约对齐**：任务触及 Application SQLite 持久化或数据模型文档时，必须要求一条 `SCHEMA_DRIFT_EVIDENCE` 实现说明，从 `ProductionMigrations()` 出发，逐项写明契约/文档更新、有意别名、当前阶段子集、延后项、临时表，以及未解决的偏差。

## 输出说明

按 `spec.json` 指定的语言给出简短摘要：

1. **状态**：确认任务已生成于 `.kiro/specs/{feature}/tasks.md`。
2. **任务摘要**：
   - 总计：X 个主任务，Y 个子任务
   - Z 条需求全部覆盖
   - 平均任务规模：每个子任务 1–3 小时
3. **质量校验**：
   - 所有需求已映射到任务
   - 设计覆盖与运行前置条件已评审
   - 任务依赖已核实
   - 任务计划评审门禁已通过
   - 独立任务图体检已通过
   - 适用时已包含持久化契约/schema 漂移任务
   - 已包含测试任务
4. **下一步动作**：审阅任务，准备好后开干。

**格式**：简洁，200 词以内。

## 异常与兜底

### 错误场景

**需求或设计缺失**：

- **停止执行**：两份文档都必须存在。
- **给用户的消息**："`.kiro/specs/{feature}/` 下缺少 `requirements.md` 或 `design.md`。"
- **建议动作**："先完成需求和设计阶段。"

**需求覆盖不全**：

- **告警**："并非所有需求都映射到了任务，请复核覆盖情况。"
- **需要用户处理**：确认是有意留空，还是重新生成任务。

**任务评审期间发现 spec 缺口**：

- **停止执行**：不要写一份打补丁的 `tasks.md`。
- **给用户的消息**："需求/设计不足以支撑一份可执行的任务计划。"
- **建议动作**："完善 `requirements.md` 或 `design.md`，然后重跑 `/kiro-spec-tasks {feature}`。"

**模板/规则缺失**：

- **给用户的消息**："`.kiro/settings/` 下缺少模板或规则文件。"
- **兜底**：用内置的基础结构，并给出告警。
- **建议动作**："检查仓库配置，或恢复模板文件。"
- **缺数字需求 ID**：
  - **停止执行**：`requirements.md` 里所有需求都必须有数字 ID。只要有一条没有，停下来要求先修好 `requirements.md`，再生成任务。

### 下一阶段：实现

任务生成之后：

- 自治实现：`/kiro-impl {feature}`
- 只做指定任务：`/kiro-impl {feature} 1.1,1.2`
