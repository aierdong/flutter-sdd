# AGENTS.md

本文件只声明 Agentic SDLC：每一步做什么、按什么顺序做、闸门是什么。它不包含项目本身的信息。

## 1. 读什么

开始任何任务前，必读本文件和 [steering.md](steering.md)。

- [steering.md](steering.md)：项目知识的地图索引，指向代码规范、实现方案、技术专题等文档。按索引加载需要的文档，不要凭记忆补规则。
- [project.md](project.md)：项目自述——我是谁、做什么、常用工程命令。只作背景，**不构成约束**；约束来自 `docs/` 下已生效的规范、当前 spec 与 `grill.md`。
- 进入某个 spec 后：读该 spec 的 `spec.md`；执行阶段读 `plan.md`。
- 启动 `sdd-grill` 时：检查仓库根目录 `FOLLOW.UPS.md` 中的待办。
- 执行技能前：完整读取 `.agents/skills/<name>/SKILL.md`。

项目信息不写进本文件，写进 `project.md`；本文件只随流程演进。

## 2. 流程

**一个 spec 只解决一个问题。** 发现是两件事，先拆。

```text
sdd-grill   →  spec.md + grill.md   人明确确认后进入下一步
     ↓
sdd-plan    →  plan.md              方案摘要经人确认；plan_lint 退出码 0
     ↓
sdd-impl    →  代码 + 测试 + 证据
     ↓
sdd-review  →  review.md            结论
```

| 步骤 | 技能 | 产出 | 通过条件 |
|---|---|---|---|
| 访谈 | `sdd-grill` | `spec.md`（第 1–7 节）、`grill.md` | `python .agents/skills/sdd-grill/tools/sdd_lint.py specs/pNN-NNN-<slug>` 退出码 0；用户明确确认需求可以进入下一步，Agent 将 Status 记为 `approved`（不要求 tag 或专用 commit） |
| 计划 | `sdd-plan` | `plan.md` | `python3 .agents/skills/sdd-plan/tools/plan_lint.py specs/pNN-NNN-<slug>` 退出码 0；方案摘要经人确认（`Status` 走到 `design-ok`）；用户明确确认可以进入实现后，Agent 将 Status 记为 `approved` |
| 实现 | `sdd-impl` | 代码、测试、命令输出 | plan 中每个任务的验证都通过 |
| 审查 | `sdd-review` | `review.md` | 结论有证据；不通过则回到最靠前的失效步骤 |

技能在 `.agents/skills/<name>/SKILL.md`；每个技能自己的模板放在该技能的 `templates/` 下，例如 `sdd-grill` 的 `.agents/skills/sdd-grill/templates/spec.md`。执行某个技能前，先完整读取它的 `SKILL.md`，按其中流程做，不要凭记忆简化。

## 3. 目录

```text
AGENTS.md
project.md
steering.md
FOLLOW.UPS.md   # 明确承诺未来处理的待办；sdd-grill 启动时检查
.agents/
  skills/<name>/SKILL.md   # 流程 Skill：模板、规则、校验脚本都放在同目录下
specs/
  pNN-NNN-<slug>/
    spec.md    # 需求、边界、决策；人审阅
    grill.md   # 访谈决策日志；追加式
    plan.md    # 执行计划；Agent 阅读
    review.md  # 证据与结论
```

目录名 `pNN-NNN-<slug>`：`pNN` 是两位阶段号（`p00`、`p01`…，当前阶段见 `project.md`），`NNN` 是该阶段内的三位序号（从 `001` 起），`slug` 用英文短横线。新 spec 取当前阶段现有最大编号 +1；换阶段时序号从 `001` 重新开始。

Agent 按项目根只扫 `.agents/skills/` 一层，技能必须是 `<name>/SKILL.md`；嵌套的 bucket 目录不会被发现。

## 4. 文档契约

`spec.md` 给人看，`plan.md` 给 Agent 看。两者的内容不重叠。

- `spec.md`：写本次变更的需求、行为、技术/质量约束、边界、决策和待决问题；用户提出的实现约束、测试要求可作为需求保留。不写文件清单、接口签名、任务拆分、执行命令，除非用户明确把某项指定为验收约束。
- `plan.md`：一份可直接执行的完整文档，含方案摘要（路线、代价、待拍板项）、约束与来源、设计与影响文件清单、任务（含验证命令与预期结果）、`R → 验证`、风险与回滚。每条 R 恰好一个验证项；任务用 `- [ ]` 标记，checkbox 只表示断点位置，不构成完成证据。方案摘要须先经人确认，之后才写设计与任务。约束与通用规范冲突时按 `覆盖` 处理，写明被覆盖的条款与失效条件。
- 长效技术约定（组件库、密度、目录与命名）写在 `docs/standards/` 并由 `steering.md` 索引，不写进 `project.md`，也不靠对话口头传递。
- `review.md`：记录做了什么、跑了什么、实际输出、结论。只有证据，不写“应该没问题”。
- `FOLLOW.UPS.md`：只放仍在生效的待办，状态只有 `待办` / `进行中`。一项完成或取消后从表中删除，证据进 `review.md`、取消理由回该 spec——不保留已完成或已取消的行，这份文件是活跃清单，不是历史记录。
- 正文用中文；标识符、命令、字段名保持原样。

## 5. 硬规则

1. lint 通过不代表需求已批准；只有用户明确确认 spec 可以进入下一步，才能进入 plan。确认后 Agent 将 `Status` 记为 `approved`；不要求批准 tag、专用 commit 或其它自我证明。未完成的 plan 不得写代码。
2. `spec.md` 第 6 节（风险与取舍）的决策，plan 不得推翻；要改就回 spec 重开。
3. `spec.md` 第 7 节的未决问题必须问人，不得自行选择。
4. 不做计划外改动。顺手发现的改进，写进当前 spec 的「明确不做」；若明确延期到未来处理，`sdd-grill` 必须将待办追加到根目录 `FOLLOW.UPS.md`。
5. 验证以命令输出为准。没跑就是没跑，不能写成通过；无法自动验证的部分，在 plan 中写明手工步骤并实际执行。
6. 只有 `sdd-review` 通过，才能宣称该 spec 完成并开始下一个。
7. 只有人明确要求跳过流程时才可跳过；跳过必须在回复里说明跳过了哪几步。
8. 约束冲突按层解决，越具体越优先：本次实现特例 > spec 第 4/6 节 > `docs/standards/*`。用更具体的来源覆盖更一般的来源是正常做法，但必须标 `覆盖`、写明被覆盖的条款，并在 `plan.md` 第 3.2 节给出理由与可判断的失效条件。反方向不允许：plan 不得推翻 spec 的 R 或第 6 节决策（见规则 2）。
9. 影响所有后续 spec 的约定若无标准文档可依，中断当前 spec 先补约定（单独开 spec 或会话），再回来；只在本 spec 成立的写进 `plan.md` 第 2 节并标 `仅本次`。

## 6. 流程自身也要迭代

`AGENTS.md`、技能及其模板都是受管文档。流程变更作为一个 spec 提出；用户明确确认后一次性同步修改，避免文档与技能漂移。确认只需对话中的明确同意，不要求 tag 或专用 commit。项目信息变化改 `project.md`；新增或移动知识文档时同步更新 `steering.md`。

本项目的交付物是 `.agents/skills/` 这一整套流程技能，`specs/pNN-NNN-*` 是迭代过程文件，记录当时怎么想的。规则被后续 spec 取代后，旧 spec 保持原样：不回溯修正，也不拿历史 spec 当现行规则引用。现行规则只看 `AGENTS.md`、技能文件和 `docs/standards/`。过程文件里的矛盾不需要修，需要修的是技能本身。

## 7. 现状

- 已有：`sdd-grill`、`sdd-plan`（各自带模板、规则与校验脚本，见 `.agents/skills/`）。
- 待建：`sdd-impl`、`sdd-review` 及对应模板。
- 已有 specs 见 `specs/` 目录，不在这里逐条维护——它们是过程文件，不是流程的一部分。
- 项目信息见 `project.md`，知识索引见 `steering.md`。
