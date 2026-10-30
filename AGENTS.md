# AGENTS.md

本文件只声明 Agentic SDLC：每一步做什么、按什么顺序做、闸门是什么。它不包含项目本身的信息。

## 1. 读什么

开始任何任务前，必读本文件和 [steering.md](steering.md)。

- [steering.md](steering.md)：项目知识的地图索引，指向代码规范、实现方案、技术专题等文档。按索引加载需要的文档，不要凭记忆补规则。
- [project.md](project.md)：项目目标、范围、约束、工程命令。需要项目上下文时再读。
- 进入某个 spec 后：读该 spec 的 `spec.md`；执行阶段读 `plan.md`。
- 执行技能前：完整读取 `.agents/skills/<name>/SKILL.md`。

项目信息不写进本文件，写进 `project.md`；本文件只随流程演进。

## 2. 流程

**一个 spec 只解决一个问题。** 发现是两件事，先拆。

```text
sdd-grill   →  spec.md + grill.md   人批准
     ↓
sdd-plan    →  plan.md              自检
     ↓
sdd-impl    →  代码 + 测试 + 证据
     ↓
sdd-review  →  review.md            结论
```

| 步骤 | 技能 | 产出 | 通过条件 |
|---|---|---|---|
| 访谈 | `sdd-grill` | `spec.md`（第 1–7 节）、`grill.md` | `python .agents/skills/sdd-grill/tools/sdd_lint.py specs/pNN-NNN-<slug>` 退出码 0；人明确批准，Status 置为 `approved`，并在同一个 commit 上打 approval tag（批准凭据为 tag，见 `sdd-grill` §阶段 4） |
| 计划 | `sdd-plan` | `plan.md` | 每条 R 都有设计、任务与验证；无待决问题 |
| 实现 | `sdd-impl` | 代码、测试、命令输出 | plan 中每个任务的验证都通过 |
| 审查 | `sdd-review` | `review.md` | 结论有证据；不通过则回到最靠前的失效步骤 |

技能在 `.agents/skills/<name>/SKILL.md`；每个技能自己的模板放在该技能的 `templates/` 下，例如 `sdd-grill` 的 `.agents/skills/sdd-grill/templates/spec.md`。执行某个技能前，先完整读取它的 `SKILL.md`，按其中流程做，不要凭记忆简化。

## 3. 目录

```text
AGENTS.md
project.md
steering.md
.agents/
  skills/sdd-grill/
    SKILL.md
    templates/spec.md
    templates/grill.md
    rules/dimensions.md
    tools/sdd_lint.py     # 闸门校验，单文件纯标准库（L01–L10）
  skills/sdd-plan|sdd-impl|sdd-review/SKILL.md
specs/
  pNN-NNN-<slug>/
    spec.md    # 需求、边界、决策；人审阅
    grill.md   # 访谈决策日志；追加式
    plan.md    # 执行计划；Agent 阅读
    review.md  # 证据与结论
```

目录名 `pNN-NNN-<slug>`：`pNN` 是两位阶段号（`p00`、`p01`…，当前阶段见 `project.md`），`NNN` 是该阶段内的三位序号（从 `001` 起），`slug` 用英文短横线。新 spec 取当前阶段现有最大编号 +1；换阶段时序号从 `001` 重新开始。

DSH 按项目根只扫 `.agents/skills/` 一层，技能必须是 `<name>/SKILL.md`；嵌套的 bucket 目录不会被发现。

## 4. 文档契约

`spec.md` 给人看，`plan.md` 给 Agent 看。两者的内容不重叠。

- `spec.md`：只写需求、边界、决策和待决问题。不写文件清单、接口签名、任务拆分、测试命令。
- `plan.md`：一份可直接执行的完整文档，至少含需求（`spec.md` 第 4 节的 R 清单）、设计（结构与关键技术决策）、任务（含验证命令与预期结果）、风险与回滚。每条 R 至少被一个任务覆盖，并至少有一个验证项。
- `review.md`：记录做了什么、跑了什么、实际输出、结论。只有证据，不写“应该没问题”。
- 正文用中文；标识符、命令、字段名保持原样。

## 5. 硬规则

1. 未经人批准的 spec 不得进入 plan；未完成的 plan 不得写代码。
2. `spec.md` 第 6 节（风险与取舍）的决策，plan 不得推翻；要改就回 spec 重开。
3. `spec.md` 第 7 节的未决问题必须问人，不得自行选择。
4. 不做计划外改动。顺手发现的改进，写进当前 spec 的「明确不做」或下一个 spec。
5. 验证以命令输出为准。没跑就是没跑，不能写成通过；无法自动验证的部分，在 plan 中写明手工步骤并实际执行。
6. 只有 `sdd-review` 通过，才能宣称该 spec 完成并开始下一个。
7. 只有人明确要求跳过流程时才可跳过；跳过必须在回复里说明跳过了哪几步。

## 6. 流程自身也要迭代

`AGENTS.md`、技能及其模板都是受管文档。流程变更同样作为一个 spec 提出；批准后一次性同步修改，避免文档与技能漂移。项目信息变化改 `project.md`；新增或移动知识文档时同步更新 `steering.md`。

## 7. 现状

- 已有：`sdd-grill`（含 `spec.md` 模板，位于 `.agents/skills/sdd-grill/templates/`）。
- 待建：`sdd-plan`、`sdd-impl`、`sdd-review` 及对应模板；`specs/` 随第一个 spec 创建。
- 项目信息见 `project.md`，知识索引见 `steering.md`。
