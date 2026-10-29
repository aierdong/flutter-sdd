---
translated: true
source: .claude/skills/kiro-spec-design/SKILL.md
generated: 2026-10-29
---

# kiro-spec-design：把需求翻译成技术设计

> 本文件是英文原文的中文译本，供阅读与评审。事实以 `.claude/skills/kiro-spec-design/SKILL.md` 为准。

## 技能元信息

| 项 | 内容 |
|---|---|
| name | `kiro-spec-design` |
| description | 带发现过程，把需求（WHAT）翻译成架构（HOW）的完整技术设计。需要从需求产出架构时使用。 |
| allowed-tools | `Read`, `Write`, `Edit`, `Grep`, `Glob`, `WebSearch`, `WebFetch`, `Agent` |
| 参数提示 | `<feature-name>` |
| 共享规则 | `design-principles.md`、`design-discovery-full.md`、`design-discovery-light.md`、`design-synthesis.md`、`design-review-gate.md` |

## 核心任务

- **成功标准**：
  - 每条需求都映射到技术组件，接口清晰。
  - 设计的责任边界足够明确，能直接指导任务拆分和评审。
  - 该做的架构发现与调研都做了。
  - 设计与 steering 上下文和既有模式一致。
  - 影响持久化的设计，包含明确的 Persistence Delta（持久化增量）和数据模型契约影响说明。
  - 复杂架构配了图。

## 执行步骤

### 第 1 步：收集上下文

如果对话里已经带有 steering / spec 上下文，就不要重复读文件。否则加载全部必要上下文：

- `.kiro/specs/{feature}/spec.json`、`requirements.md`、`design.md`（如果已存在）。
- `.kiro/specs/{feature}/research.md`（如果存在，里面是 `/kiro-validate-gap` 的差距分析）。
- 核心 steering：`product.md`、`tech.md`、`structure.md`。
- 以下情况才读额外的 steering 文件：与需求覆盖、架构边界、集成、运行前置条件、安全与性能约束，或影响实现就绪度的团队约定直接相关。
- `.kiro/settings/templates/specs/design.md`，取文档结构。
- 读本 skill 目录下的 `rules/design-principles.md`，取设计原则。
- `.kiro/settings/templates/specs/research.md`，取调研日志结构。
- 如果本特性会创建、修改、读取或校验 Application SQLite 持久化，额外加载：
  - `docs/data-model/sqlite-implementation-contract.md`（存在时）。
  - 相关的 `docs/data-model/*.md` 实体文档。
  - 相关迁移入口，**从 `internal/infra/sqlite/migrations.go` 开始查，而不是只看某一个具名迁移文件**。

### 第 2 步：发现与分析

**关键：这一步是为了确保设计建立在完整、准确的信息上。**

1. **判定特性类型**：
   - **新特性**（绿地）：做完整发现。
   - **扩展**（改既有系统）：做以集成为主的发现。
   - **简单增量**（CRUD / UI）：做最小发现，或不做。
   - **复杂集成**：做全面分析。

2. **按类型执行发现流程**：

   **复杂/新特性**：
   - 读并执行本 skill 目录下的 `rules/design-discovery-full.md`。
   - 用 WebSearch / WebFetch 做深入研究：
     - 最新的架构模式与最佳实践。
     - 外部依赖核实（API、库、版本、兼容性）。
     - 官方文档、迁移指南、已知问题。
     - 性能基准与安全考量。

   **扩展**：
   - 读并执行 `rules/design-discovery-light.md`。
   - 聚焦集成点、既有模式、兼容性。
   - 用 Grep 分析现有代码库的写法。

   **简单增量**：
   - 跳过正式发现，只做一次快速模式检查。

#### 并行调研（派子代理）

下面几块调研彼此独立，可以通过 Agent 工具派成**子代理**。怎么拆由你按特性复杂度决定：拆开、合并、追加或跳过。每个子代理只返回**结论摘要**（不是原始材料），保持主上下文干净，便于综合。

**典型调研域**（按需调整）：

- **代码库分析**：既有架构模式、集成点、代码约定（用 Grep/Glob）。
- **外部调研**：依赖、API、最新最佳实践（用 WebSearch/WebFetch）。
- **上下文加载**（通常留主上下文）：steering 文件、设计原则、发现规则、模板。

简单增量不要派子代理，直接在主线做一次模式检查。

所有结论返回后，先在主上下文里综合，再往下走。

3. **保留发现结论，留给第 3 步**：

   - 外部 API 契约与约束。
   - 技术决策及其理由。
   - 要遵循或扩展的既有模式。
   - 集成点与依赖。
   - 已识别的风险与缓解策略。
   - 边界候选、越界决策，以及可能触发的重新校验（revalidation）条件。
   - 与持久化相关时的事实：`ProductionMigrations()` 的迁移清单、当前 SQLite 的表/列/枚举/约束、数据模型契约条目、有意的存储别名、当前阶段子集、延后字段，以及仅用于临时验证的表。

4. **把结论落到调研日志**：

   - 用共享模板创建或更新 `.kiro/specs/{feature}/research.md`。
   - 概述发现范围与关键结论。
   - 记录查证过程、来源与影响。
   - 记录架构模式评估、设计决策和风险。
   - 写 `research.md` 时使用 `spec.json` 指定的语言。

### 第 3 步：综合

**在动笔写设计之前，先对发现结论做综合。**

- 读并应用本 skill 目录下的 `rules/design-synthesis.md`。
- 这一步需要看到发现结论的全貌，**必须在主上下文执行，不能放进子代理**。
- 把综合结果（找到的泛化机会、自建还是采用、简化决策）记进 `research.md`。

### 第 4 步：写设计草稿

1. **生成设计草稿**：

   - **严格遵循 `specs/design.md` 模板的结构和生成说明**。
   - **边界优先**：在展开支撑章节之前，先把边界说清楚。草稿必须明确：本规格负责什么、不负责什么、允许依赖谁、哪些变更会要求下游重新校验。
   - **整合全部发现结论与综合结果**：把调研到的信息（API、模式、技术）和综合决策（泛化、自建或采用、简化）贯穿到组件定义、架构决策和集成点里。
   - **文件结构计划（必需）**：File Structure Plan 章节要填具体文件路径和职责。分析代码库，判断哪些文件要新建、哪些要改。每个文件只能有一个清晰职责。这一节直接决定任务的 `_Boundary:_` 标注和实现阶段的 Task Brief。**文件结构写糊，实现必然糊。**
   - **测试策略**：测试项从需求的验收条件推导，不要套通用模板。每条测试项都应引用本设计里的具体组件和行为。E2E 路径要对应需求里的关键用户流程。避免"测一下登录能用"这种含糊条目，要写清验证的是什么、为什么重要。
   - **Persistence Delta（必需，条件见下）**：当特性触及 Application SQLite 持久化、数据模型文档、迁移、仓储（repository）、schema 扫描缓存、项目配置、生成器配置、执行历史或 schema 影响处理时，必须加一节说明：
     - 新增、变更或有意保持不变的 SQLite 表与迁移。
     - 必须更新的数据模型文档和 `sqlite-implementation-contract.md` 条目。
     - 字段、枚举、null/默认值、CHECK、外键、索引、UNIQUE 约束的变化。
     - 有意的存储别名，以及当前阶段的枚举/字段子集。
     - 带阶段门（phase gate）的延后设计字段/实体。
     - 仅用于临时验证、不得当作最终数据模型的持久化。
     - 预期的 schema 漂移证据，以及 schema 快照/巡检测试。
   - 第 1 步如果发现已有 `design.md`，把它当作参考上下文（合并模式）。
   - 应用设计规则：类型安全、可视化表达、正式语气。
   - 使用 `spec.json` 指定的语言。
   - 在评审门禁通过之前，它一直是草稿：**此时还不要写 `design.md`**。

### 第 5 步：评审设计草稿

- 读并应用本 skill 目录下的 `rules/design-review-gate.md`。
- 定稿前，检查需求覆盖、架构就绪度和实现可执行性。
- 如果草稿触及 Application SQLite 持久化，核对 Persistence Delta 存在，并且把每一处代码/设计差异归类为：`implemented`、`alias`、`phase-subset`、`deferred`、`temporary`、`deviation`、`removed-from-design` 之一。
- 出现下列情况直接驳回草稿：悄悄收窄了已记录的数据模型枚举；改变了 null/默认值语义；新增迁移表；改变 unique / 外键 / check 约束；引入存储别名却没有契约或更新路径。
- 如果问题只出在草稿局部，就地修好，再评审一次。
- 修复循环最多 2 轮。
- 如果草稿暴露了真正的需求/设计缺口，停下来回到需求澄清，**不要在 `design.md` 里糊过去**。

### 第 6 步：定稿

1. **写最终设计**：

   - 只有在设计评审门禁通过后，才写 `.kiro/specs/{feature}/design.md`。
   - 写 `research.md`，记录发现结论与综合结果（如果之前没写）。

2. **更新 `spec.json` 元数据**：

   - 设置 `phase: "design-generated"`。
   - 设置 `approvals.design.generated: true`。
   - 更新 `updated_at` 时间戳。

## 关键约束

- **类型安全**：
  - 按项目技术栈强制强类型。
  - 静态类型语言：定义显式类型/接口，禁止不安全的类型转换。
  - TypeScript：绝不用 `any`，用精确类型和泛型。
  - 动态类型语言：在有类型提示的地方补齐（例如 Python type hints），并在边界处校验输入。
  - 公开接口与契约要写清楚，保证跨组件的类型安全。
- **需求追溯 ID**：只用数字需求 ID（例如 `1.1`、`1.2`、`3.1`、`3.3`），且必须与 `requirements.md` 里定义的一致。不要自造新 ID，也不要用字母标签。

## 输出说明

**命令执行输出**（与 `design.md` 正文分开）：

按 `spec.json` 指定的语言给出简短摘要：

1. **状态**：确认设计文档已生成于 `.kiro/specs/{feature}/design.md`。
2. **发现类型**：执行了哪种发现流程（full / light / minimal）。
3. **关键结论**：2–3 条塑造了本设计的关键洞察。
4. **评审门禁**：确认设计评审门禁已通过。
5. **Persistence Delta**：适用时，确认 Application SQLite / 数据模型契约影响已归类；否则写 `N/A`。
6. **下一步动作**：跑 `/kiro-spec-tasks {feature}` 生成实现任务。
7. **调研日志**：确认 `research.md` 已更新到最新决策。

**格式**：简洁 Markdown，200 词以内。这是命令输出，不是设计文档本身。

**说明**：真正的设计文档遵循 `.kiro/settings/templates/specs/design.md` 的结构。

## 异常与兜底

### 错误场景

**需求缺失**：

- **停止执行**：需求文档必须存在。
- **给用户的消息**："在 `.kiro/specs/{feature}/requirements.md` 没找到需求文档。"
- **建议动作**："先跑 `/kiro-spec-requirements {feature}` 生成需求。"

**模板缺失**：

- **给用户的消息**："模板文件缺失：`.kiro/settings/templates/specs/design.md`。"
- **建议动作**："检查仓库配置，或恢复模板文件。"
- **兜底**：用内置的基础结构，并给出告警。

**Steering 上下文缺失**：

- **告警**："steering 目录为空或缺失，设计可能与项目标准不一致。"
- **继续**：可以继续生成，但要在输出里注明这个限制。

**需求 ID 不合法**：

- **停止执行**：如果 `requirements.md` 缺少数字 ID，或用了非数字标题（例如 `Requirement A`），停下来，让用户先修好 `requirements.md` 再继续。

**设计评审期间发现 spec 缺口**：

- **停止执行**：不要写一份打补丁的 `design.md`。
- **给用户的消息**："设计评审发现真实的需求缺口或歧义，必须先解决，设计才能定稿。"
- **建议动作**：澄清或修正 `requirements.md`，然后重跑 `/kiro-spec-design {feature}`。

### 下一阶段：生成任务

**下一步**：

- **可选**：跑 `/kiro-validate-design {feature}` 做交互式质量评审。
- 跑 `/kiro-spec-tasks {feature}` 生成实现任务。

**需要修改时**：

- 给反馈，重跑 `/kiro-spec-design {feature}`。
- 已有设计作为参考（合并模式）。
