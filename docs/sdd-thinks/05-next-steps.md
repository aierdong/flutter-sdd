# 落地与下一步

> 这里说的"落地"，是把流程产物放进**第一个使用它的项目**（Flutter Demo）。流程的所有权仍在本目录；迁移动作只是让技能在一个真实项目里跑起来，不是把流程交给那个项目。

## 一、把草案落成可用技能：6 处改动

草案目前在 `../kiro-spec/`，是按"仓库级模板 + 相对链接"组织的。Flutter Demo 的 `AGENTS.md` 约定不同，迁入前要改：

### 1. 目录落位

```text
.agents/skills/sdd-grill/
├── SKILL.md
├── rules/dimensions.md
└── templates/spec.md        ← 从 docs/kiro-spec/templates/ 移进来
```

`AGENTS.md` 明确"每个技能自己的模板放在该技能的 `templates/` 下"。移入后，`SKILL.md` 里的链接要从 `../../templates/spec.md` 改成 `templates/spec.md`。

### 2. 输入改为新仓库的约定文件

| 现在写的 | 改成 |
|---|---|
| 项目约定文档（`.kiro/steering/`） | `steering.md`（地图索引）+ `project.md`（项目上下文）+ `docs/standards/*`（按索引加载） |

顺带删掉所有 `.kiro/` 字样，新仓库不依赖旧结构。

### 3. spec 路径约定

`AGENTS.md` 与 `steering.md` 用的是 `specs/pNN-NNN-*/`：

```text
specs/p00-001-connections-schema-list/
├── spec.md
├── grill.md
└── plan.md
```

`pNN` 是阶段（当前 `p00`），`NNN` 在阶段内递增。`spec.md` 模板头部的 `Spec:` 字段同步改成 `pNN-NNN-<slug>`。

### 4. 批准凭据（对应 Q1）

`AGENTS.md` 只写了"人明确批准，Status 置为 `approved` 并记录批准凭据"。建议定成：

```markdown
| Status | approved |
| Approved | <人工提交的 commit sha> |
| Approved-by | <git author> |
```

配套两条硬规则写进 `SKILL.md`：

- Agent **不得创建、修改、代签**批准 commit；
- 审阅区内容一变，旧的 `Approved` 立即失效，`plan.md` 标 `stale`。

### 5. 检查脚本移植（Flutter）

Go 版原型在原仓库 `loomidbx-v3` 的 `scripts/sdd-check.ps1` / `sdd-check.sh`（**未随文档迁入本仓库**，需要时回原仓库取）。移植时只换命令层，框架不变：

| 检查项 | Go 版 | Flutter 版 |
|---|---|---|
| 编译/静态 | `go build ./...` + `go vet` | `flutter analyze`（一次，秒级到十几秒） |
| 测试 | 改动包的 `go test` | 先按改动文件映射到 `test/**`；映射不出来时跑 `flutter test` 全量 |
| 前端 | `npm --prefix frontend run typecheck` | 无（去掉） |
| 卫生 | TBD/密钥 grep | 保留 |
| 边界 | `-Boundary` 前缀比对 | 保留 |
| 证据复用 | `tree_stamp` 缓存 | 保留，逻辑可原样搬 |

`flutter build windows` 太慢，不要放进每次提交前的检查；只在 spec 末的运行时存活检查里用一次（或先只做 `flutter test` + 手工启动）。

### 6. 例子要换成本项目的

`dimensions.md` 现在用的是原仓库（数据库工具）的例子，有几处必须替换：

- `secret://` 引用、truncate 目标表、MySQL/PostgreSQL 差异 → 改成"连接串与密码不进入仓库/日志/错误信息"（`project.md` 的约束）、"只读元数据"、"schema 列表为空/表很多"。
- 保留仍然成立的：部分失败（连上了但枚举 schema 超时）、空与极值（0 个 schema、1000 张表）、并发（刷新期间表被修改）。

## 二、第一个 spec 怎么拆

`project.md` 写的是"第一个 spec 建议：连接 → 树 → 表详情"。按"一个 spec 只解决一个可独立验收的问题"，这是**三件事**：

| 拆分 | 可独立验收的标志 |
|---|---|
| `p00-001` 连接并列出 schema | 输入连接信息 → 界面上出现 schema 列表（哪怕还是一行行文本） |
| `p00-002` 树上展开到表 | schema 节点能展开出表节点 |
| `p00-003` 表详情与刷新 | 选中表能看到字段/约束/外键；能刷新 |

建议：**只做 `001`**，用它验证流程本身。理由：001 已经是一个完整的纵向切片（UI → 应用层 → 驱动 → 目标库 → 渲染），能暴露流程的全部环节；而 002/003 是同一模式的重复。

如果 001 跑完发现"验证流程"这个目标需要更多真实感，再决定 002 与 003 合并还是分开。

> 第一次跑 `sdd-grill` 时，第一个问题就应该是这个拆分判断——它正好演练"发现是两件事，先拆"这条规则。

## 三、接下来的顺序

| 顺序 | 做什么 | 为什么这个顺序 |
|---|---|---|
| 1 | 按上面 6 处改动，把 `sdd-grill` 落成 `.agents/skills/sdd-grill/` | 没有可用技能，后面都是纸上讨论 |
| 2 | 真实跑一次 `sdd-grill`，产出 `p00-001` 的 `spec.md` | 用真实需求检验模板与维度清单 |
| 3 | 写 `sdd-plan`（`plan.md` 模板 + 自检矩阵） | spec 批准后的下一步，需求最清楚 |
| 4 | 写 `sdd-impl` + 移植检查脚本 | 实现阶段需要有证据可复用 |
| 5 | 写 `sdd-review`（`review.md`） | 收口，且能反过来检验前三段 |
| 6 | 第二个 spec 用 `extend` 型跑 | 验证分型与"上游不做清单"比对 |

## 四、怎么判断流程本身有效

跑完 `p00-001` 之后，用这五条检验，不合格就改流程，不要急着做 002：

1. **只读 `spec.md`（不打开 `plan.md`），你能做出批准决定**，并说出至少一个取舍。
2. **`plan.md` 能只凭 `spec.md` 生成**，过程中没有冒出新的人口决定；自检矩阵全绿。
3. **实现的 diff 全部落在 `plan.md` 声明的范围内**，没有"顺手加"的功能。
4. **`review.md` 至少指出一个 spec/plan 没预见的问题。** 一条都说不出，说明评审是橡皮章。
5. **记录基线**：这次 spec 的总耗时、token 量、以及"回到 spec 的次数"。

第 5 条尤其重要：后面所有关于"更轻""更快"的判断都需要这个基线，否则又会变成拍脑袋。

## 五、关于 `docs/kiro-spec/`

它是历史材料（Kiro 译文 + 机制分析 + 早期提案），已经完成使命。建议：

- 保留，但加一处标注"历史材料，不维护"（`README.md` 已写）；
- 后续所有结论以 `docs/sdd-thinks/` 为准；
- 里面的 `skills/`、`templates/` 是草案来源，迁到 `.agents/skills/` 之后就可以当只读参考。

## 六、脚手架化（流程跑通之后）

目标：用脚本把 `.agents/skills/` 与 `AGENTS.md` 打包，同时生成 `project.md`、`steering.md` 模板，新项目一条命令就能起一套流程。

### 先定唯一权威来源，再写脚本

现在同一个技能有两份实体：`docs/sdd-thinks/`（设计）与 `.agents/skills/sdd-grill/`（运行副本），而 `.agents/skills/sdd-grill/` 的所有权属于流程项目、物理位置却在 Demo 仓库里。

**脚本必须从"流程项目的源"取文件，Demo 里的 `.agents/skills/` 是产物，不是源。** 否则同一份 `SKILL.md` 活在两处，迟早漂移——这个坑在上一轮已经踩过一次（两个目录下的 skill 内容不一致）。

建议的源目录形态（在流程项目里，与 `sdd-thinks` 同级）：

```text
skills/            # 唯一权威来源
├── sdd-grill/{SKILL.md, rules/, templates/}
├── sdd-plan/...
└── sdd-impl/...
templates/         # 脚手架生成 project.md / steering.md / AGENTS.md 的模板
```

生成动作：复制 `skills/*` 到目标项目的 `.agents/skills/`，渲染 `AGENTS.md`、`project.md`、`steering.md` 三个模板，只填空（项目名、技术栈、命令、阶段），**不引入分支逻辑**。

### `steering.md` 模板要带的三样

1. **`## 范围外` 段**——每代项目都可能需要排除某些目录（本仓库排除的是流程材料）。模板里留一个空段 + 一句用法说明，比事后补更容易被记住。
2. **"索引里没有的文档视为未生效"**——这是索引制能成立的前提。
3. **"规范文档带版本号，改动时同步递增"**——避免规范悄悄变了而没人知道。

### 脚手架本身要版本化

生成的 `AGENTS.md` 与技能会继续演进，脚手架必须有版本（如 `scaffold v0.1`），并在生成的 `AGENTS.md` 顶部标注"由 scaffold vX 生成"。否则三个月后没人知道某个项目用的是哪一版流程。

### 落地前的验收

- 生成的技能目录结构完整：每个技能都有 `SKILL.md`，引用到的 `rules/`、`templates/` 都存在；
- 生成文档里的相对链接全部可解析；
- 在一个空项目上跑一遍 `sdd-grill`，能产出 `spec.md` 而不是报错要人补信息。
