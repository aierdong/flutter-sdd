---
translated: true
source: CLAUDE.md
generated: 2026-10-29
---

# Agentic SDLC 与规格驱动开发

在 Agent 驱动的软件生命周期（agentic SDLC）上，跑 Kiro 风格的规格驱动开发（Spec-Driven Development，SDD）。

## 项目上下文

### 路径

- Steering（常驻约束）：`.kiro/steering/`
- Specs（特性规格）：`.kiro/specs/`

### Steering 与 Spec 的分工

**Steering**（`.kiro/steering/`）：用项目级规则和背景，指导 AI 的长期行为。
**Specs**（`.kiro/specs/`）：把单个特性的开发过程形式化。

### 在做的规格

- 到 `.kiro/specs/` 下查看当前有哪些规格。
- 用 `/kiro-spec-status [feature-name]` 查进度。

## 开发约定

- 用英文思考。
- 项目文档一律用英文撰写，除非用户明确要求别的语言。这包括写进项目文件的 Markdown，比如 `requirements.md`、`design.md`、`tasks.md`、`research.md` 和各类校验报告。
- 面向控制台的输出用中文，包括可见的推理摘要、进度更新和最终总结。
- 向缺少项目背景的读者解释问题、评审意见、阻塞点、修复方案或取舍时，用清晰的白话中文，同时不降低技术准确度。按情况组织成这些部分：背景/上下文、问题是什么、一个具体场景、影响、建议方案、范围与取舍、小结。先定义读者可能不熟悉的术语，再把已确认的事实和风险/证据缺口分开写。
- `/kiro-validate-gap`、`/kiro-validate-design`、`/kiro-validate-impl` 这三个命令，先输出英文校验原文，紧接着输出同一内容的中文翻译。

## 最小工作流

- 阶段 0（可选）：`/kiro-steering`、`/kiro-steering-custom`
- 发现阶段：`/kiro-discovery "idea"`。它决定走哪条行动路径；对包含多个规格的项目，写出 `brief.md` + `roadmap.md`。
- 阶段 1（规格化）：
  - 单规格：`/kiro-spec-quick {feature} [--auto]`，或按步骤执行：
    - `/kiro-spec-init "description"`
    - `/kiro-spec-requirements {feature}`
    - `/kiro-validate-requirements {feature}`（可选：逐条需求评审）
    - `/kiro-validate-gap {feature}`（可选：已有代码库时做差距分析）
    - `/kiro-spec-design {feature}`
    - `/kiro-validate-design {feature}`（可选：设计评审）
    - `/kiro-spec-tasks {feature}`
  - 多规格：`/kiro-spec-batch`。按依赖波次并行，从 `roadmap.md` 生成全部规格。
- 阶段 2（实现）：`/kiro-impl {feature} [tasks]`
  - 不给任务编号：自治模式（每个任务一个子代理 + 独立评审 + 最终校验）。
  - 给任务编号：手动模式（在主上下文里执行选定任务，但完成前仍要过评审门）。
  - `/kiro-validate-impl {feature}`：独立重跑校验。
- 查进度：`/kiro-spec-status {feature}`，任何时候都能用。

## Skills 的结构

Skills 放在 `.claude/skills/kiro-*/SKILL.md`。

- 每个 skill 是一个目录，里面有一个 `SKILL.md`。
- Skill 在当前对话里内联执行，能读到对话上下文。
- Skill 可以把并行调研派给子代理，以提高效率。
- Skill 目录里可以再放模板、示例等附加文件。
- `kiro-review`：任务级对抗式评审协议，评审子代理用它。
- `kiro-validate-requirements`：串行评审需求文档，一次只抛一个发现。
- `kiro-debug`：先定位根因的调试协议，调试子代理用它。
- `kiro-verify-completion`：在宣称成功或完成之前，要求新鲜证据的门禁。
- **只要当前任务有 1% 的可能用到某个 skill，就调用它。** 不要因为任务看起来简单就跳过。

## 已完成规格的追溯审计

- 在做的特性要走当前特性 GO 门禁，用 `/kiro-validate-impl {feature}`。
- 回顾一个已经完成的历史特性，用 `/kiro-audit-completed {feature} [--baseline <git-ref>] [--mode historical_baseline|current_head|dual_compare]`。
- 追溯审计把"完成时的基线"和"当前 HEAD"分开比较。审计本身不得改动 `spec.json` 里的叶子任务完成状态、审批记录或编写阶段。
- 审计证据放在 `.kiro/audits/`。当前退化的问题要归到所属的现行规格；然后按它们的 Revalidation Triggers 重新校验下游。

## 开发规则

- 保持 steering 常新，并用 `/kiro-spec-status` 核对一致性。
- 精确遵循用户指令，在这个范围内自主行动：收集必要上下文，本轮就把要求的工作端到端做完。只有在缺少关键信息、或指令存在关键歧义时才提问。
- 被同一个具体问题卡住时，最多做三次有意义的尝试。仍然解决不了就停止重试，报告阻塞点、尝试过程和证据，并请人给出决策或介入。

### 权威来源纪律

当某个含义、术语、数值边界或产品规则已经有归属时，只保留唯一一个权威来源。

- 来源可以是已有项目文档的某个章节，也可以是当前规格里的一段话或一条验收标准。
- 其他地方只能引用这个来源。不得复制规则、不得改写成同义词、不得另造一套并行术语。
- 如果还没有来源，先建立来源，再引用。不要把同一条规则散落在 requirements、design、主题文档和代码注释里。
- 规格编写、需求评审、设计、实现都要遵守这条纪律。它不是可选的风格偏好。

## Steering 配置

- 把整个 `.kiro/steering/` 当作项目记忆加载。
- 默认文件：`product.md`、`tech.md`、`structure.md`。
- 支持自定义文件，由 `/kiro-steering-custom` 管理。

## Agent skills

### 问题跟踪

本仓库的 issue 和 PRD 记在 GitHub Issues。见 `docs/agents/issue-tracker.md`。

### 分诊标签

本仓库使用默认的五标签分诊词表。见 `docs/agents/triage-labels.md`。

### 领域文档

本仓库使用单上下文（single-context）领域文档布局。见 `docs/agents/domain.md`。

### 工作流指引

任务涉及规划、需求、设计、实现、校验、调试、调研、重构、评审、领域建模、issue 流程或架构决策时，先简要推荐一条路线：Kiro 工作流、Matt Pocock 工程 skill、两者先后串联，或直接执行。正式的特性规格工作优先用 Kiro；调研、诊断、TDD、原型、领域建模、代码评审、合并冲突处理、方案拷问这类支撑性工程工作，优先用 Matt Pocock 的 skill。见 `docs/agents/engineering-skills-guide.md`。
