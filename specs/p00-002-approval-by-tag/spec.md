# 批准流程：一次 commit + 一个 tag

> 本文件供人类审阅。只读第 1–6 节，就能判断这条需求该不该做、做成什么样、代价是什么。

| 字段 | 值 |
|---|---|
| Spec | `p00-002-approval-by-tag` |
| 类型 | `fix` |
| 上游 | `p00-001-schema-tables-page` |
| 附带交付 | `—` |
| Status | `draft` |
| 版本 | `v1` |
| Approved | `—` |

## 1. 背景与问题

**现状**：`AGENTS.md:32` 的访谈闸门只写“人明确批准，Status 置为 `approved` 并记录批准凭据”，具体做法在 `.agents/skills/sdd-grill/SKILL.md:246-255`：先提交内容 commit，再把 `Approved` 填成该 commit 的 SHA、`Status` 改 `approved`，第二次提交；`grill.md` 再单独提交。`sdd_lint.py:62` 把 `Approved` 列为头字段，`:215-234` 要求 `approved` 时必须是 7–40 位十六进制 SHA。p00-001 实际产生了 `d8f1c11`（内容）、`23343a4`（批准）、`2e39297`（grill）三个 commit。

**问题**：SHA 只能在提交后知道，但提交又包含这个 SHA；改成两次提交后，只能把 `Approved` 指向内容 commit A，`git diff <Approved> -- spec.md` 永远包含头部变化，不可能为空。spec 再调整一次，A 又会过时；p00-001 里旧的 `cc77419` 已经是悬空 commit。批准一次要三次 commit，对以“验证 SDD 流程”为目的的 demo 来说，这是纯开销。

**为什么现在做**：p00-001 已批准，下一步是 plan；如果不先修，后面每个 spec 都会复制这个自相矛盾的批准契约。

## 2. 目标

- 让批准变成一次人工 commit 加一个 annotated tag；`spec.md` 不记录 commit SHA。
- 让 `approved` 的 spec 冻结：任何改动必须版本 +1、重新评审、重新批准并打新 tag。
- 让 `AGENTS.md`、`sdd-grill` 技能与模板、`sdd_lint.py` 同步到新契约；p00-001 与 p00-002 保留旧字段。

**成功后，你能看到/做到**：p00-003 的 spec 只用一个 commit + 一个 tag 就完成批准；Agent 用 tag 与 `git diff` 校验；`spec.md` 里没有 `Approved: <sha>`；p00-001、p00-002 仍能通过 lint。

## 3. 用户场景

### 场景 A：正常批准 p00-003

1. Agent 交付 `Status: draft`、`Approved-Tag: —` 的 spec。
2. 人读完第 1–6 节，把 `Status` 改为 `approved`、`Approved-Tag` 填 `spec/p00-003/approved-v1`。
3. 人提交一次（`spec.md`，可同时带 `grill.md`），并在该 commit 上创建同名 annotated tag。
4. Agent 校验 tag 存在、tag 名匹配、`git diff <tag> -- spec.md` 为空、`Status` 为 `approved`。
5. 校验通过，进入 plan。

### 场景 B：批准后 spec 被改

1. 某个 commit 修改了已批准 spec 的正文，但没有升版本或重新批准。
2. `git diff <Approved-Tag> -- spec.md` 非空。
3. Agent 停止，不进入 plan；要求人升版本、把 `Status` 回 `draft`、重新评审并打新 tag。

### 场景 C：tag 缺失或被移动

1. `spec.md` 写着 `Approved-Tag: spec/p00-003/approved-v1`，但本地没有这个 tag，或 tag 指向别的 commit。
2. Agent 的 `git rev-parse --verify` 或 `git diff` 校验失败。
3. Agent 停止，不把“文件里写着 approved”当作批准。

### 场景 D：p00-001 与 p00-002 的旧记录

1. 人查看 p00-001 或 p00-002 的 `spec.md`，仍看到 `Approved: <sha>`，没有 `Approved-Tag`。
2. lint 对这两个 spec 使用具名 legacy 分支，仍然通过。
3. 新建的 p00-003 不能再用 `Approved` 字段；用了就失败。

## 4. 必须做到

- [ ] **R1** 批准一个 spec 只要一次人工 commit 加一个 annotated tag：人把 `Status` 置为 `approved`、`Approved-Tag` 填 `spec/<pNN-NNN>/approved-v<版本号>`，提交一次（`spec.md`，可同时带 `grill.md`），再在同一 commit 上创建同名 annotated tag；`spec.md` 内不记录任何 commit SHA。
  - **反例**：仍要求第二次批准 commit；仍在 `spec.md` 写 SHA；tag 未创建；tag 名与 `Approved-Tag` 不一致；由 Agent 填 Status 或创建 tag。
  - **可观察证据**：对一个新 spec（p00-003 或测试 fixture）执行一次 commit + tag 后，`git log` 只有一次人工批准 commit，`git tag -n` 有对应 tag，`spec.md` 中没有 `Approved: <sha>`。

- [ ] **R2** Agent 在进入 plan/impl 前必须校验：`git rev-parse --verify <Approved-Tag>` 成功；tag 名匹配 `spec/<pNN-NNN>/approved-v<版本>`；`git diff <tag> -- spec.md` 为空；`Status` 为 `approved`。任一不满足就停止，要求人重新批准，不得继续。
  - **反例**：tag 缺失或指向别的 commit；diff 非空；`Status` 为 draft/stale；Agent 只看文件不看 tag；Agent 继续写 plan。
  - **可观察证据**：有效 tag 下四条命令都通过；手动改 `spec.md` 后 diff 非空，Agent 拒绝进入 plan。

- [ ] **R3** `approved` 的 spec 冻结：任何改动必须把 `版本` +1、`Status` 回 `draft`、`Approved-Tag` 回 `—`，重新评审后用新版本 tag 重新批准；旧 tag 保留，不得移动或复用。
  - **反例**：批准后直接改 spec 不升版本；复用旧 tag；移动旧 tag 到新 commit；plan 继续基于旧 tag。
  - **可观察证据**：改 spec 后 `git diff <旧 tag> -- spec.md` 非空；新版本只有在新 tag 出现后才通过 R2。

- [ ] **R4** `spec.md` 模板与 lint 同步到新契约：新 spec 的头部字段为 `Spec`、`类型`、`上游`、`附带交付`、`Status`、`版本`、`Approved-Tag`；`Status` 为 `approved` 时 `Approved-Tag` 必须匹配 tag 命名，非 `approved` 时为 `—`；lint 不再要求 `Approved` SHA（legacy 见 R6）。
  - **反例**：模板仍是 `Approved`；lint 仍校验 SHA；lint 接受不匹配的 tag；新 spec 用旧字段。
  - **可观察证据**：`sdd_lint.py` 对 new-style fixture 通过，对错误 tag 失败；模板中搜索不到 `| Approved |`。

- [ ] **R5** `AGENTS.md` 与 `sdd-grill/SKILL.md` 的批准条款改为上述流程：删除“两次提交 / `Approved` SHA”的步骤；明确 tag 由人创建，Agent 不得创建或移动 tag；允许 `grill.md` 与 `spec.md` 同 commit，不再要求 `grill.md` 排除在批准 commit 外。
  - **反例**：文档仍写 `Approved` SHA 或两次提交；仍要求 grill 单独 commit；Agent 可以打 tag。
  - **可观察证据**：进程文档中搜索不到旧的 SHA 批准句式；新流程文本存在。

- [ ] **R6** p00-001 与 p00-002 作为旧流程的最后两个 spec，保留 `Approved` SHA 字段；lint 对这两个 spec 使用具名 legacy 分支，其余 spec 只认 `Approved-Tag`。该例外在两者退役后删除。
  - **反例**：p00-003 用旧字段；legacy 集合多出第三个 spec；p00-001/002 被强制迁移；lint 对它们报错。
  - **可观察证据**：`sdd_lint.py` 对 p00-001/002 退出 0；对 p00-003 fixture 用旧字段失败；legacy 集合只含两个 id。

- [ ] **R7** 本次只改流程文档、模板、lint 与 `specs/p00-002-approval-by-tag/`；不修改 `lib/`、`test/`、`pubspec.yaml`、`analysis_options.yaml`，不改变应用运行行为。
  - **反例**：diff 触及产品代码；新增依赖；UI 变化。
  - **可观察证据**：`git diff --name-only` 只列流程文档、模板、lint 与 p00-002 目录；`flutter analyze` 与 `flutter test` 结果不变。

- [ ] **R8** p00-002 自身用旧流程批准（内容 commit + 批准 commit 带 SHA），新流程从 p00-003 起生效；p00-002 不按新 tag 流程重新批准。
  - **反例**：p00-002 在文档更新前使用 `Approved-Tag` 导致 lint 失败；p00-003 仍用旧流程；p00-002 被反复重批。
  - **可观察证据**：p00-002 的历史有旧流程的 content/approval commit；p00-003 的第一个批准 commit 是新流程的一 commit + tag。

## 5. 明确不做

- 不迁移 p00-001 与 p00-002 的头部内容。理由：用户选择保留历史，新流程从 p00-003 起生效。
- 不实现 `approval.md`、签名 tag 或外部审批系统。理由：annotated tag 加 tag 名校验已足够；文件方案留作备选。
- 不修改 sdd-plan、sdd-impl、sdd-review（尚不存在）。理由：本 spec 只改 sdd-grill、AGENTS、模板与 lint；未来技能在自己的 spec 里采用 tag 校验。
- 不修改 `lib/`、`test/`、`pubspec.yaml`、`analysis_options.yaml`。理由：纯流程变更，不涉及产品代码。
- 不改变访谈维度、问题上限或 R 数量上限。理由：只改批准流程，不改访谈方法。
- 不改变 `docs/standards/coding.md`。理由：不涉及代码规范。
- 不自动创建或移动 tag，不自动 approve。理由：批准必须由人做，Agent 只校验。
- 不要求 tag 签名或特定的 tag 推送策略。理由：demo 阶段先验证流程，安全加固可以后置。

## 6. 风险与取舍

| 决策 | 选择 | 理由 | 放弃了什么 | 何时重新评估 |
|---|---|---|---|---|
| 批准凭据 | 用 annotated tag，不在 spec 写 SHA | 无自引用，tag 可被 Agent 校验 | 单文件内的批准记录 | tag 经常丢失或未推送时 |
| commit 数量 | 一次 commit + 一个 tag | 去掉内容、批准、grill 三段 | 单独的 content commit 和 spec-only 批准 commit | 需要逐步审计每次批准时 |
| grill 归属 | 可与 spec 同 commit | 减少 commit | 批准 commit 只含 spec.md | 需要把决策日志单独审阅时 |
| legacy | p00-001/002 具名例外 | 不折腾历史 | 统一头部与 lint | 两者退役时 |
| lint 校验 | 只校验 tag 名格式；tag 存在与 diff 由 Agent 用 git 校验 | lint 保持纯 Python | 单一机械闸门 | lint 允许调用 git 时 |
| 引导 | p00-002 用旧流程，p00-003 起用新流程 | 不在流程未批准前改 lint | 在 p00-002 上验证新流程 | 下次流程变更时 |
| 冻结 | 任何改动都要重新批准 | 批准语义明确 | 快速修 typo | 编辑性修改变得频繁时 |
| tag 绑定 | annotated tag 加 approver/date，不加 spec 哈希或签名 | 足够 demo | 密码学绑定 | 需要防 tag 移动时 |
| 迁移 | 不迁移 p00-001/002 | 避免二次批准 | 统一历史 | 两者退役时 |

## 7. 审阅问题

**必须你决定**：本次无需你决定的事项。

**建议确认**：

- p00-002 走旧流程批准；新流程从 p00-003 起生效；legacy 集合是 p00-001 与 p00-002。
- 批准 commit 可以包含 `grill.md`；tag 与 `git diff` 只校验 `spec.md`。
- tag 命名 `spec/pNN-NNN/approved-vN`，annotated，不要求签名，由人创建。
- `approved` 后 spec 冻结；任何改动都要版本 +1、重新批准、打新 tag。
- lint 只校验 tag 名格式；tag 是否存在、是否指向当前内容，由 Agent 用 git 校验。

---

<!-- 以下不属于本文件：文件清单、接口签名、任务拆分、测试命令、验收脚本 → plan.md -->
