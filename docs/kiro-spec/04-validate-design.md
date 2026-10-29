---
translated: true
source: .claude/skills/kiro-validate-design/SKILL.md
generated: 2026-10-29
---

# kiro-validate-design：设计的交互式评审

> 本文件是英文原文的中文译本，供阅读与评审。事实以 `.claude/skills/kiro-validate-design/SKILL.md` 为准。

## 技能元信息

| 项 | 内容 |
|---|---|
| name | `kiro-validate-design` |
| description | 交互式的技术设计质量评审与校验。在实现前评审设计时使用。 |
| allowed-tools | `Read`, `Grep`, `Glob`, `AskUserQuestion` |
| 参数提示 | `<feature-name>` |
| 共享规则 | `design-review.md` |

## 角色

你是一个专门做交互式设计质量评审的 skill，目标是确认技术设计已经具备实现条件。

## 核心任务

- **使命**：对技术设计做交互式质量评审，确保可以进入实现。
- **成功标准**：
  - 指出关键问题（最多 3 个最重要的担心）。
  - 评价平衡，该肯定的地方要肯定。
  - 给出明确的 GO / NO-GO 结论和理由。
  - 影响持久化的设计，检查是否写了 Persistence Delta 和数据模型契约影响。
  - 需要改进时，给出可执行的反馈。

## 执行步骤

### 第 1 步：收集上下文

如果对话里已经带有 steering / spec 上下文，就不要重复读文件。否则加载全部必要上下文：

- 读 `.kiro/specs/{feature}/spec.json`，取语言和元数据。
- 读 `.kiro/specs/{feature}/requirements.md`，取需求。
- 读 `.kiro/specs/{feature}/design.md`，取设计文档。
- 核心 steering：`product.md`、`tech.md`、`structure.md`。
- 以下情况才读额外的 steering 文件：与架构边界、集成、运行前置条件、领域规则、安全与性能约束，或影响实现就绪度的团队约定直接相关。
- 以下情况才读本地 agent skill 或 playbook：它明显匹配本特性的宿主环境或用例，并能提供与评审相关的上下文。
- 如果设计触及 Application SQLite 持久化、数据模型文档、迁移、仓储、schema 扫描缓存、项目配置、生成器配置、执行历史或 schema 影响处理，还要读 `docs/data-model/sqlite-implementation-contract.md`（存在时）、相关 `docs/data-model/*.md`，以及迁移入口 `internal/infra/sqlite/migrations.go`。

#### 并行调研

下面两件事彼此独立，可以并行：

1. **上下文与规则加载**：spec 文档、核心 steering、与任务相关的额外 steering、匹配的本地 agent skill/playbook，以及本 skill 目录下 `rules/design-review.md` 的评审标准。
2. **代码库模式勘察**：从代码库采集既有架构模式、命名约定和组件结构，作为评审参照。

全部完成后，先综合，再评审。

### 第 2 步：执行设计评审

- 参考对话历史：用上前面对需求的讨论，以及用户表达过的设计意图。
- 按 `design-review.md` 的流程走：分析 → 关键问题 → 优点 → GO/NO-GO。
- 对影响持久化的设计，在决定 GO 之前先做 Persistence Delta 评审：
  - 确认设计点清了范围内每一处迁移/表/字段/枚举/null/默认值/索引/外键/UNIQUE/CHECK 变化。
  - 确认每一处代码/设计差异都有契约状态：`implemented`、`alias`、`phase-subset`、`deferred`、`temporary`、`deviation`、`removed-from-design`。
  - 确认设计说明了 `docs/data-model/sqlite-implementation-contract.md`、受影响的 `docs/data-model/*.md`、schema 快照/巡检测试是否需要改。
  - 持久化在范围内却缺 Persistence Delta 时，直接算 NO-GO 问题。
- 最多只提 3 个最重要的担心。
- 与用户交互：提澄清问题，提出替代方案。
- 输出使用 `spec.json` 指定的语言。

### 第 3 步：给结论和下一步

- 给出明确的 GO / NO-GO 结论和理由。
- 给出具体可执行的下一步（见下方"下一阶段"）。

## 重要约束

- **做质量把关，不追求完美**：可接受的风险就接受。
- **只抓关键**：最多 3 个问题，且只挑显著影响成败的。
- **结合对话**：利用讨论历史理解需求背景和用户意图。
- **交互式**：以对话方式进行，提澄清问题，给替代方案。
- **评价平衡**：优点和缺点都要说。
- **反馈可执行**：所有建议都必须能落地。
- **上下文纪律**：从核心 steering 开始，只扩展与评审相关、且与本用例匹配的本地 agent skill/playbook。
- **持久化漂移纪律**：影响持久化的设计，如果缺 Persistence Delta、悄悄收窄已记录的枚举、改变 null/默认值语义、引入存储别名、新增临时持久化，或改变 unique / 外键 / check 约束却没有配套的契约和校验更新，**不得批准**。

## 工具指引

- **先读**：评审前加载 spec、核心 steering、相关本地 playbook/agent skill 和规则。
- **需要时用 Grep**：在代码库中核对模式、检查集成点。
- **保持交互**：整个评审过程与用户对话。

## 输出说明

按 `spec.json` 指定的语言输出：

1. **评审摘要**：2–3 句话，概述设计质量与就绪度。
2. **关键问题**：最多 3 个，格式遵循 `design-review.md`。
3. **Persistence Delta 评审**：持久化在范围内时必须给出结论；否则写 `N/A`。
4. **设计优点**：1–2 条正面评价。
5. **最终判定**：GO / NO-GO 结论、理由和下一步。

**格式要求**：

- 用 Markdown 标题分层，便于扫读。
- 遵循 `design-review.md` 的输出格式。
- 摘要保持简洁。

## 异常与兜底

### 错误场景

- **缺设计**：`design.md` 不存在时，停下并提示："先跑 `/kiro-spec-design {feature}` 生成设计文档。"
- **设计未标记为已生成**：`spec.json` 里设计阶段没标为已生成，给出告警但继续评审。
- **steering 目录为空**：提醒用户项目上下文缺失，可能影响评审质量。
- **语言未定义**：`spec.json` 没指定语言时，默认英文（`en`）。

### 下一阶段：生成任务

**设计通过校验（GO）时**：

- 双方同意后，落实建议的改进。
- 跑 `/kiro-spec-tasks {feature}` 生成实现任务。
- 或者跑 `/kiro-spec-tasks {feature} -y`，自动批准并直接继续。

**设计需要返工（NO-GO）时**：

- 处理评审指出的关键问题。
- 带着改进重跑 `/kiro-spec-design {feature}`。
- 再用 `/kiro-validate-design {feature}` 复评。

**说明**：设计评审是推荐动作，不是必选项。早做质量评审，能更早发现问题。
