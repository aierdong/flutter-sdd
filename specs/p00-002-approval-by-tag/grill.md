# Grill 决策日志：p00-002-approval-by-tag

| 成本 | 值 |
|---|---|
| 类型 | `fix` |
| 问题数 | `2` |
| 问题上限 | `9` |
| 问题追加 | `—` |
| 工具调用 | `2` |
| 工具预算 | `8` |
| 工具追加 | `—` |
| 追加理由 | `—` |
| 开始 | `2026-10-30 22:37` |
| 结束 | `2026-10-30 22:58` |
| 重问 | `0` |

## 规范触碰

无。本 spec 只改 `AGENTS.md`、`sdd-grill` 技能/模板/lint，不触碰 `docs/standards/` 下的代码规范。

## 事实收集

- 已读：`AGENTS.md:32` → 访谈闸门只写“人明确批准，Status 置为 approved 并记录批准凭据”，没有定义凭据形式。
- 已读：`AGENTS.md:74-82` → 硬规则 1 要求未批准不得进入 plan；硬规则 7 允许人明确要求跳过。
- 已读：`AGENTS.md:84-86` → 流程变更本身要作为一个 spec 提出，批准后同步修改。
- 已读：`.agents/skills/sdd-grill/SKILL.md:56` → Agent 不得创建、修改或代签批准 commit；`Status: approved` 与 `Approved: <sha>` 只能由人填。
- 已读：`.agents/skills/sdd-grill/SKILL.md:206` → 头字段闸门要求 `Spec / 类型 / 上游 / 附带交付 / Status / 版本 / Approved` 七项。
- 已读：`.agents/skills/sdd-grill/SKILL.md:246-255` → 当前流程是内容 commit、批准 commit、再单独提交 grill；并校验 `git diff <Approved> -- spec.md` 为空。
- 已读：`.agents/skills/sdd-grill/templates/spec.md:15-23` → 头部使用 `Status` 与 `Approved`。
- 已读：`sdd_lint.py:62` → `HEAD_FIELDS` 包含 `Approved`；`:88` 用 SHA 正则；`:215-234` 在 approved 时要求 7–40 位十六进制 SHA。
- 已读：`specs/p00-001-schema-tables-page/spec.md:5-13` → p00-001 当前是 `Status: approved`、`Approved: d8f1c11…`。
- 已读：`git log --oneline -- specs/p00-001-schema-tables-page` → 产生 `d8f1c11`（内容）、`23343a4`（批准）、`2e39297`（grill）三个 commit。
- 已读：`git diff d8f1c11 -- spec.md` → 只差 `Approved` 一行；`git diff <Approved> -- spec.md` 不可能为空，证实自引用问题。
- 已读：`git tag -l` → 当前没有任何 tag；`specs/` 只有 p00-001，下一个编号是 p00-002。
- 已读：用户 2026-10-30 的说明 → demo 的价值是构建和验证 SDD 流程，不是 demo 本身的质量。
- 未读：无；工具调用 2/8，未超预算。

## 决策

起点（流程确认，不计入问题数）：用户同意把批准流程改成“一次 commit + 一个 tag”，并同意本流程变更作为 p00-002 立项。

Q1 p00-002 这个流程 spec 自己用哪套流程批准？
A: 旧流程最后一次；p00-002 走内容 commit + 批准 commit（带 SHA），新流程从 p00-003 起生效。
   放弃：在 p00-002 上直接演练新流程。
   何时重新评估：下次流程变更、或需要在新流程生效前做 dry run 时。
→ R8 / §6

Q2 p00-001 保留旧 `Approved` SHA 字段，lint 怎么兼容？
A: 具名例外；lint 只对 p00-001 和 p00-002 使用 legacy 分支，其余 spec 只认 `Approved-Tag`。
   放弃：lint 同时接受新旧字段；或迁移 p00-001。
   何时重新评估：p00-001 与 p00-002 退役、legacy 分支可以删除时。
→ R6 / §6

## 已有决策（来自用户 2026-10-30 的流程讨论，不计入问题数）

- D1 失败语义：tag 缺失、tag 被移动、`git diff <tag> -- spec.md` 非空、`Status` 不是 approved，任一发生就停止，不进入 plan；由人重新批准。→ R2 / §5
- D6 可逆性：只改流程文档、模板与 lint，git 可回滚；不迁移 p00-001/002；不删除旧 tag。→ §5 / §6
- F1 正确行为：一次人工 commit + 一个 annotated tag；spec 不写 SHA；approved 后冻结。→ R1 / R3
- F2 同源入口：`AGENTS.md`、`sdd-grill/SKILL.md`、`templates/spec.md`、`sdd_lint.py` 四处，加上 p00-001/002 的头部。→ R4 / R5 / R6
- F4 依赖现状：批准闸门、lint、p00-001/002、未来 plan/review 都依赖批准凭据。→ R2 / R4 / R5
- 批准 commit 可以包含 `grill.md`；tag 与 `git diff` 只校验 `spec.md`。→ R1 / R5
- tag 命名 `spec/pNN-NNN/approved-vN`，annotated，不要求签名；由人创建，Agent 只校验。→ R1
- lint 只校验 tag 名格式；tag 是否存在、是否指向当前内容由 Agent 用 git 校验。→ R2 / R4
- 冻结规则从严：任何改动都要版本 +1、重新批准、打新 tag。→ R3

## 覆盖矩阵

| 维度 | 状态 | 依据 |
|---|---|---|
| D1 失败与部分失败 | 已覆盖 | R2：tag 缺失/移动/diff 非空即停止；没有“部分批准”状态 |
| D6 可逆性 | 已覆盖 | §5/§6：只改文档与 lint，git 可回滚；不迁移 p00-001/002 |
| F1 正确行为的一句话定义 | 已覆盖 | R1/R3：一次 commit + tag，spec 无 SHA，approved 后冻结 |
| F2 同源入口 | 已覆盖 | R4/R5/R6：AGENTS、skill、template、lint、p00-001/002 |
| F3 已产生的错误数据 | 已覆盖 | R6/§6：p00-001/002 保留旧 SHA，具名例外，不迁移 |
| F4 谁在依赖现状 | 已覆盖 | R2/R4/R5：批准闸门、lint、p00-001/002、未来 plan/review |
