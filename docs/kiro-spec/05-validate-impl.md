---
translated: true
source: .claude/skills/kiro-validate-impl/SKILL.md
generated: 2026-10-29
---

# kiro-validate-impl：特性级集成校验

> 本文件是英文原文的中文译本，供阅读与评审。事实以 `.claude/skills/kiro-validate-impl/SKILL.md` 为准。

## 技能元信息

| 项 | 内容 |
|---|---|
| name | `kiro-validate-impl` |
| description | 所有任务实现完之后，做特性级集成校验。检查跨任务一致性、完整测试套件和整体规格覆盖。 |
| allowed-tools | `Read`, `Bash`, `Grep`, `Glob`, `Agent` |
| 参数提示 | `<feature-name> [task-numbers]` |

## 角色

单个任务在实现过程中已经由任务级评审把关过了。你的活儿是抓那些**只有把所有任务放在一起看才会暴露**的问题。

边界术语的连续性：

- 发现阶段识别 `Boundary Candidates`
- 设计阶段确定 `Boundary Commitments`
- 任务阶段用 `_Boundary:_` 约束执行
- 特性校验阶段检查跨任务的 `Boundary Violations`

## 核心任务

- **成功标准**：
  - `tasks.md` 里所有任务都标了 `[x]`。
  - 完整测试套件通过（不只是每个任务自己的测试）。
  - 跨任务集成可用（组件间的数据流能走通，接口能对上）。
  - 需求在所有任务合起来之后被完整覆盖（任务之间没有缝）。
  - 设计结构端到端体现出来（不只是每个组件各自对）。
  - 影响持久化的工作，相对数据模型实现契约没有未归类的 schema 漂移。
  - 没有孤儿代码、互相冲突的实现、集成接缝问题，也没有边界溢出。

## 这个 skill 不做什么

任务级检查是 `/kiro-impl` 期间评审者的职责。这个 skill **不重复检查**：

- 单个任务的验收标准
- 逐文件的真实性检查（mock / stub 识别）
- 单任务的规格对齐

它要回答的主要问题是：把这些已完成任务放在一起看，它们是否仍然遵守设计定下的边界接缝和依赖方向。

## 执行步骤

### 第 1 步：确定校验对象

**没有参数时**：

- 从对话历史里解析 `/kiro-impl` 命令，找出最近实现的特性与任务。
- 扫 `.kiro/specs/`，找有已完成任务 `[x]` 的特性。
- 报告识别到的实现（例如 "user-auth: 1.1, 1.2, 1.3"）。

**给了特性名**（特性有，任务为空）：

- 用指定特性。
- 在 `.kiro/specs/{feature}/tasks.md` 里找出所有已完成的 `[x]` 任务。

**特性和任务都给了**（显式模式）：

- 只校验指定的特性和任务（例如 `user-auth 1.1,1.2`）。

### 第 2 步：收集上下文

如果对话里已经带有 steering / spec 上下文，就不要重复读文件。否则对每个识别到的特性：

- 读 `.kiro/specs/<feature>/spec.json`，取元数据。
- 读 `.kiro/specs/<feature>/requirements.md`，取需求。
- 读 `.kiro/specs/<feature>/design.md`，取设计结构。
- 读 `.kiro/specs/<feature>/tasks.md`，取任务清单和 Implementation Notes。
- 核心 steering：`product.md`、`tech.md`、`structure.md`。
- 以下情况才读额外的 steering 文件：与被校验边界、运行前置条件、集成、领域规则、安全与性能约束，或影响 GO/NO-GO 判断的团队约定直接相关。
- 如果已完成任务触及 Application SQLite 持久化、数据模型文档、迁移、仓储、schema 扫描缓存、项目配置、生成器配置、执行历史或 schema 影响处理，还要读 `docs/data-model/sqlite-implementation-contract.md`（存在时）、相关 `docs/data-model/*.md`，并从 `internal/infra/sqlite/migrations.go` 开始做迁移清单。

**找出规范的校验命令**：

- 按这个顺序查仓库内的权威来源：项目脚本/清单（`package.json`、`pyproject.toml`、`go.mod`、`Cargo.toml`、应用清单）、任务运行器（`Makefile`、`justfile`）、CI/工作流文件、既有的 e2e/集成配置，最后才是 `README*`。
- 推导出本仓库特性级的校验命令集：`TEST_COMMANDS`、`BUILD_COMMANDS`、`SMOKE_COMMANDS`。
- 优先用仓库自动化已经在用的命令，而不是临时拼的 shell 管道。
- `SMOKE_COMMANDS` 要选与应用形态匹配、最轻但可信的运行时存活检查（例如：打开根 URL、启动 Electron、CLI `--help`、服务健康端点、已有的移动端模拟器/e2e 夹具）。
- 有多个候选时，选设置成本最低、但仍能跑真实构建产物的那个。

### 第 3 步：执行集成校验

#### 子代理派发（并行）

下面这些校验维度彼此独立，可以通过 Agent 工具派成**子代理**。怎么拆由你按特性范围决定：拆开、合并或跳过。每个子代理返回**结构化的问题摘要**，保持主上下文干净，便于综合出 GO/NO-GO。

**典型校验维度**（按需调整）：

- **测试执行**：跑完整测试套件，报告通过/失败细节。
- **需求覆盖**：建立需求 → 实现的对应矩阵，报告缺口。
- **设计对齐**：核实架构与 `design.md` 一致，报告漂移和依赖违规。
- **持久化漂移**：影响持久化的工作，把 `ProductionMigrations()` 和变更后的仓储行为，与 `docs/data-model/sqlite-implementation-contract.md` 及受影响的 `docs/data-model/*.md` 对照，报告未归类的漂移。
- **跨任务集成**：核实数据流、API 契约、共享状态的一致性。

简单特性（任务少、范围小）不必派子代理，在主上下文里直接查。

#### 机械检查（跑命令，用结果说话）

这些检查在特性级执行。**以命令输出为主要信号。**

**A. 完整测试套件**

- 跑第 2 步找到的规范全量测试命令，用退出码判定。
- 测试失败 → NO-GO。不需要再做判断。
- 找不到规范测试命令 → `MANUAL_VERIFY_REQUIRED`。

**B. 残留 TBD/TODO/FIXME**

- 执行：`grep -rn "TBD\|TODO\|FIXME\|HACK\|XXX" <files-in-feature-boundary>`
- 如果命中项是本特性引入的 → 记为 Warning。

**C. 残留硬编码密钥**

- 执行：`grep -rn "password\s*=\|api_key\s*=\|secret\s*=\|token\s*=" <files-in-feature-boundary>`（忽略大小写）
- 如果命中项不是环境变量引用 → 记为 Critical。

**D. 运行时存活（Smoke 启动）**

- 跑第 2 步找到的规范 smoke 命令，证明构建产物真的能起来并到达第一个可用状态。
- 相关时的例子：在无头浏览器里打开根 URL，要求启动期零控制台错误；启动 Electron 并等主进程就绪信号和首次渲染加载；跑 CLI 的 `--help`；起服务并打健康端点。
- 启动过程出现运行时崩溃、未处理异常、模块加载失败、原生 ABI 不匹配、缺少必需环境变量或配置 → NO-GO。
- 找不到可信的 smoke 命令，或所需运行环境不可用 → `MANUAL_VERIFY_REQUIRED`。

**D.5. 持久化 schema 漂移证据**

- 当已完成任务触及 Application SQLite 持久化、数据模型文档、迁移、仓储、schema 扫描缓存、项目配置、生成器配置、执行历史或 schema 影响处理时，执行本项。
- **从 `ProductionMigrations()` 出发，检查完整迁移集合**，而不是只看任务里点名的文件。
- 核实实现说明里包含 `SCHEMA_DRIFT_EVIDENCE`，且有：
  - 迁移清单来源
  - 受影响的表和列
  - 数据模型契约更新
  - 有意的别名、当前阶段子集、延后项、临时持久化、已从设计移除的项，以及偏差
  - schema 快照/巡检测试或等价证据
- 只要有变更或发现的差异没有契约状态，或该更新契约/文档却没更新 → NO-GO。

#### 判断类检查（读代码，与 spec 对照）

**E. 跨任务集成**

- 找出任务之间共享接口、数据模型或 API 契约的地方。
- 核实任务 A 的输出格式与任务 B 的预期输入对得上。
- 检查任务之间是否有冲突的假设（命名约定、错误码、数据形状）。
- 核实共享状态（数据库 schema、配置、环境）在任务间一致。
- 核实集成发生在设计预定的接缝上，而不是把一个边界的行为漏进另一个边界。

**F. 需求覆盖缺口**

- 把每个需求章节映射到至少一个已完成任务。
- 找出没有单个任务能完整覆盖的需求（横切需求）。
- 找出被多个任务各覆盖一部分、但没有任何任务完整覆盖的需求。
- 使用 `requirements.md` 的原始章节编号，**不要自造 `REQ-*` 别名**。

**G. 设计与实现端到端对齐**

- 核实整体组件图与 `design.md` 一致。
- 检查集成模式（事件流、API 边界、依赖注入）是否按设计工作。
- 核实依赖方向符合 `design.md` 的架构（不允许向上导入）。
- 核实 File Structure Plan 与实际文件布局一致。
- 找出相对原始设计的架构漂移。
- 影响持久化的工作，核实设计里的 Persistence Delta 已实现，或已在数据模型契约里显式修订。
- 使用 `design.md` 的原始章节编号。

**G.5 边界审计**

- 把已完成工作与设计的 `Boundary Commitments`、`Out of Boundary`、`Allowed Dependencies`、`Revalidation Triggers` 对照。
- 找出跨任务溢出：某个领域悄悄接管了另一个边界的职责。
- 找出"为了集成方便"而嵌进上游的下游专用变通。
- 找出设计里没声明的新隐藏依赖或共享权属。
- 如果有 revalidation trigger 被触发，核实受影响的相邻规格或集成点真的重新检查过了。

**H. 阻塞任务与实现说明**

- 检查是否还有任务标着 `_Blocked:_`，报告原因并评估对特性完整性的影响。
- 翻一遍 `tasks.md` 的 `## Implementation Notes`，找需要注意的横切洞察。

### 第 4 步：出报告

在给出 `GO` 之前，对特性级结论应用 `kiro-verify-completion` 协议。**只有测试不足以支撑结论**：证据里要包含全量测试、运行时存活、覆盖度、集成、设计对齐和阻塞任务状态。

写整改意见之前，先按归属给具体失败分类：

- `LOCAL`：缺陷属于正在校验的这个特性
- `UPSTREAM`：根因属于某个依赖、地基、共享平台或更早的规格
- `UNCLEAR`：凭现有证据无法确定归属

如果归属是 `UPSTREAM`，不要把问题压成本特性的局部整改。点明所属的上游规格，并说明上游修复落地后哪些下游规格应该重新校验。

按 `spec.json` 指定的语言给出摘要（下列模板的字段名是机器可读标识，保留英文）：

```
## Validation Report
- DECISION: GO | NO-GO | MANUAL_VERIFY_REQUIRED
- MECHANICAL_RESULTS:
  - Tests: PASS | FAIL (command and exit code)
  - TBD/TODO grep: CLEAN | <count> matches
  - Secrets grep: CLEAN | <count> matches
  - Smoke boot: PASS | FAIL | MANUAL_REQUIRED
- INTEGRATION:
  - Cross-task contracts: <status>
  - Shared state consistency: <status>
  - Boundary audit: <status>
- COVERAGE:
  - Requirements mapped: <X/Y sections covered>
  - Coverage gaps: <list of uncovered requirement sections>
- DESIGN:
  - Architecture drift: <findings>
  - Dependency direction: <violations if any>
  - File Structure Plan vs actual: <match/mismatch>
- PERSISTENCE_DRIFT:
  - Applicable: yes | no
  - Migration inventory: <ProductionMigrations() checked | N/A>
  - Contract updated: yes | no | N/A
  - Schema evidence: <snapshot/inspection/test evidence | missing | N/A>
  - Unclassified drift: <none | list>
- OWNERSHIP: LOCAL | UPSTREAM | UNCLEAR
- UPSTREAM_SPEC: <feature-name | N/A>
- BLOCKED_TASKS: <list and impact assessment>
- REMEDIATION: <if NO-GO: specific, actionable steps to fix each issue>
```

判定为 NO-GO 时，`REMEDIATION` 是必填项：写清具体问题，以及需要改什么。**不接受含糊反馈。**

## 重要约束

- **严格的最终门禁**：所有集成检查通过才返回 `GO`；出现具体失败返回 `NO-GO`；必需的校验做不了，返回 `MANUAL_VERIFY_REQUIRED`。
- **边界完整性优先于省事**：即使测试都通过，只要这个特性是靠把职责糊过边界才跑通的，就不能返回 `GO`。
- **不允许未归类的持久化漂移**：影响持久化的工作，只要有一处迁移/数据模型差异没有显式契约状态，或缺少必需的契约/schema 证据，就不能返回 `GO`。

## 异常与兜底

### 错误场景

- **找不到实现**：没有任何 `[x]` 任务时，报告 "未检测到实现"。
- **测试命令未知**：返回 `MANUAL_VERIFY_REQUIRED`，说明缺哪条校验命令；**不要返回 `GO`**。
- **spec 文件缺失**：`spec.json` / `requirements.md` / `design.md` 缺失时，直接报错停止。

### 下一步指引

**判定 GO 时**：

- 特性已端到端校验，可以部署或进入下一个特性。

**判定 NO-GO 时**：

- 处理 `REMEDIATION` 里列出的问题。
- 针对具体修复重跑 `/kiro-impl {feature} [tasks]`。
- 再用 `/kiro-validate-impl {feature}` 复验。

**判定 MANUAL_VERIFY_REQUIRED 时**：

- **不要**把这个特性当成已完成。
- 给出确切缺失的校验步骤或环境前置条件。
