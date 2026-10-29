---
translated: true
generated: 2026-10-29
scope: .claude/skills/kiro-spec-*、.claude/skills/kiro-validate-*、CLAUDE.md
---

# Kiro SDD 中文译读本与自我流程草案

> 本目录现在放两类材料：
> 1. **Kiro 流程的中文译读**（`00`–`05`、`rules/`）——事实来源是 `.claude/skills/kiro-*/SKILL.md` 与根目录 `CLAUDE.md`，译本是快照。
> 2. **自建 SDD 流程的草案**（`analysis.md`、`proposal.md`、`skills/`、`templates/`）——它们不是 Kiro 的译文，而是准备替代它的新流程。

## 这个目录解决什么问题

Kiro 的 skill 文本是写给 Agent 执行的，句法压缩、术语密集、大量短句并列。人读起来的感觉是"每句都懂，读完不知道它到底在管什么"。

所以这份译读本做了三件事：

1. **按中文阅读习惯重写句子**：拆长句、补主语、把条件从句提到前面、把并列的约束写成条目。术语保留英文原文，第一次出现时用 `中文（English）` 标注。
2. **不改事实**：验收编号、`_Requirements:_` / `_Boundary:_` / `_Test profile:_` 这类机器标记、文件路径、命令、字段名，全部逐字保留。所有 `MUST` / `MUST NOT` 级别的约束，语义强度不降级。
3. **标注原文位置**：每个译本开头写明源文件路径，便于对照核对。

## 目录结构

| 文件 | 原文 | 内容 |
|---|---|---|
| `00-claude.md` | `CLAUDE.md` | 项目级流程约定：路径、阶段、审批、写作纪律 |
| `01-spec-requirements.md` | `.claude/skills/kiro-spec-requirements/SKILL.md` | 需求生成：EARS 验收条件、需求评审门禁 |
| `02-spec-design.md` | `.claude/skills/kiro-spec-design/SKILL.md` | 技术设计：发现、综合、设计评审门禁 |
| `03-spec-tasks.md` | `.claude/skills/kiro-spec-tasks/SKILL.md` | 任务生成：依赖、边界、测试档位、任务图体检 |
| `04-validate-design.md` | `.claude/skills/kiro-validate-design/SKILL.md` | 设计交互式评审：最多 3 个关键问题 + GO/NO-GO |
| `05-validate-impl.md` | `.claude/skills/kiro-validate-impl/SKILL.md` | 特性级集成校验：测试、覆盖、边界、持久化漂移 |
| `rules/ears-format.md` | `kiro-spec-requirements/rules/ears-format.md` | EARS 五种句式与固定短语规则 |
| `rules/requirements-review-gate.md` | `kiro-spec-requirements/rules/requirements-review-gate.md` | 需求落盘前的自检项 |
| `rules/design-review-gate.md` | `kiro-spec-design/rules/design-review-gate.md` | 设计落盘前的自检项 |
| `rules/design-review.md` | `kiro-validate-design/rules/design-review.md` | 设计评审的四条准则与输出格式 |
| `rules/tasks-generation.md` | `kiro-spec-tasks/rules/tasks-generation.md` | 任务粒度、排序、并行、门禁 |
| `analysis.md` | — | 分析：Kiro 怎么跑流程，怎么保证 spec 的质量与一致性 |
| `proposal.md` | — | 思考：对"双视角、单文件"改造方案的评审与落地建议（含第 5 节"执行成本与验证时机"） |

配套原型：[scripts/sdd-check.ps1](<scripts/sdd-check.ps1>)、[scripts/sdd-check.sh](<scripts/sdd-check.sh>) —— 用一个命令替代校验阶段的六条机械检查，并按代码树指纹复用证据。用法见 `proposal.md` 5.4。

### 新流程草案

新流程是一条独立的轻量 SDD，只借鉴 Kiro 中经受住检验的部分，不继承它的文档结构：

```text
sdd-grill   →  spec.md   审阅区：干什么、为什么、做成什么样、不做什么（人批准）
     ↓
sdd-plan    →  plan.md   执行区：改哪里、按什么契约、怎样验证、边界在哪
     ↓
sdd-impl    →  代码与提交
     ↓
sdd-review  →  证据与结论
```

目前只完成了第一段。

| 文件 | 用途 |
|---|---|
| `skills/sdd-grill/SKILL.md` | 需求访谈：先分型（新建 / 增量 / 修正），再一次一问问透，产出 `spec.md` 第 1–6 节与决策日志 |
| `skills/sdd-grill/rules/dimensions.md` | 三种类型各自的必问维度、通用六维度问题库、覆盖矩阵、追问话术 |
| `templates/spec.md` | `spec.md` 审阅区模板（第 1–7 节，`R#` 编号，含 `上游` 字段） |

这三个文件按未来 skill 目录的结构摆放：`skills/sdd-grill/` 是自包含的 skill（`SKILL.md` + `rules/`），`templates/spec.md` 留在仓库级模板目录，将来由 `sdd-grill`、`sdd-plan` 共用。迁移时整棵 `docs-zh/kiro-spec` 一起搬，skill 内部只用相对路径引用，不需要改写链接。

## 阅读顺序建议

- 只想知道"Kiro 到底卡在哪几道门"：先看 `analysis.md`，再按需回查译本。
- 想理解某个阶段的完整规则：直接读对应编号的译文，末尾的"下一步"段落会指向下一阶段。
- 想改造流程：读 `analysis.md` → `proposal.md`，两份文档共用同一套术语。

## 术语约定

### 新流程

| 术语 | 说明 |
|---|---|
| spec | 一条需求的审阅区（`spec.md`）。一条需求 = 一个新能力或一次改动，可独立验收 |
| 类型 | `new`（新建）/ `extend`（增量）/ `fix`（修正），决定要读什么、问什么 |
| 上游 | 增量/修正所基于的既有 spec，形如 `001-connections-list` |
| plan | 执行区（`plan.md`）：改哪里、按什么契约、怎样验证、边界在哪 |
| `R#` | 第 4 节"必须做到"的稳定编号，plan、测试、完成定义都引用它 |
| grill.md | 决策日志：每次问答的选择、放弃了什么、何时重新评估 |
| 门禁 | 进入下一阶段前必须通过的检查 |
| 决策 / 事实 | 事实自己查（代码、测试、文档），决定必须问人 |

### Kiro 译本

| 术语 | 说明 |
|---|---|
| steering | `.kiro/steering/` 下的项目级常驻约束（新流程只把它当"项目约定文档"，不依赖这个路径） |
| EARS | 验收条件句式标准，见 `rules/ears-format.md` |
| traceability | 需求编号 → 设计组件 → 任务 → 测试的对应关系 |

## 维护方式

- 译本（`00`–`05`、`rules/`）与英文原文一一对应，**不合并、不省略、不改写规则强度**。
- 原文更新后，按 `source` 字段定位并重新翻译该文件，不要局部打补丁。
- 新流程草案（`analysis.md`、`proposal.md`、`skills/`、`templates/`）是活文件，随讨论直接改，不需要保留历史版本。
- `kiro-sdd-thinks.md` 是当时的对话记录，只作存档，不维护、不引用。
- 发现译文与原文冲突时，以原文为准，并修译文。
