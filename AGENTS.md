# AGENTS.md

本仓库用一套自定义的 spec-driven development（SDD）流程开发。本文件是流程的入口与最上层约定：声明做什么、按什么顺序做、每一步的闸门是什么。具体做法写在 `.sdd/skills/` 的各技能里，两者冲突时以本文件的流程与闸门为准。

开始任何任务前，按顺序读：本文件 → 当前 spec 的 `spec.md` → `plan.md`（若存在）→ 相关技能的 `SKILL.md`。

## 1. 项目

一个 Flutter 桌面应用，只读浏览 PostgreSQL 的库结构：

- 连接一个数据库，枚举其全部 schema，再取每个 schema 下的表。
- database / schema / table 组成一棵可展开的树。
- 选中表后可查看：表名、字段列表、约束、外键。
- 允许刷新某个表的详情信息（表可能在查看期间修改）

它存在的目的是验证上面这套 SDD 流程，不是生产应用。取舍顺序：流程可验证 > 功能完整 > 健壮性与性能。

项目约束：

- 对目标库只读，不写入、不修改。
- 连接串与密码不进入仓库、日志或错误信息。

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
| 访谈 | `sdd-grill` | `spec.md`（第 1–7 节）、`grill.md` | 人明确批准，Status 置为 `approved` 并记录批准凭据 |
| 计划 | `sdd-plan` | `plan.md` | 每条 R 都有设计、任务与验证；无待决问题 |
| 实现 | `sdd-impl` | 代码、测试、命令输出 | plan 中每个任务的验证都通过 |
| 审查 | `sdd-review` | `review.md` | 结论有证据；不通过则回到最靠前的失效步骤 |

技能在 `.sdd/skills/<name>/SKILL.md`，模板在 `.sdd/templates/`。执行某个技能前，先完整读取它的 `SKILL.md`，按其中流程做，不要凭记忆简化。

## 3. 目录

```text
AGENTS.md
.sdd/
  skills/sdd-grill|sdd-plan|sdd-impl|sdd-review/SKILL.md
  templates/spec.md, plan.md, review.md
specs/
  NNN-<slug>/
    spec.md    # 需求、边界、决策；人审阅
    grill.md   # 访谈决策日志；追加式
    plan.md    # 执行计划；Agent 阅读
    review.md  # 证据与结论
```

`NNN` 为三位递增编号，取现有最大值 +1；`slug` 用英文短横线。

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

`AGENTS.md`、技能和模板都是受管文档。流程变更同样作为一个 spec 提出；批准后一次性同步改这三处，避免文档与技能漂移。

## 7. 现状

- 已有：`sdd-grill`、`spec.md` 模板。
- 待建：`sdd-plan`、`sdd-impl`、`sdd-review` 及对应模板；`specs/` 随第一个 spec 创建。
- 第一个 spec 建议：应用的最小可用版本（连接 → 树 → 表详情）。
- 项目级约定暂以本文件为准，需要时再拆成独立文档。

## 8. 验证命令

应用创建后统一使用：

```bash
flutter analyze
flutter test
```

命令写进 `plan.md`，实际输出贴进 `review.md`。
