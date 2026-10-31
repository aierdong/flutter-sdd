# Review: p00-004-dependency-scope

| 字段 | 值 |
|---|---|
| Spec | `p00-004-dependency-scope`（spec v1 / approved） |
| 执行 | 2026-10-31 22:41–22:52 |
| 结论 | **通过**（7 条 R 全部有命令证据；2 处 spec 勘误记录在下方，不改变需求） |

## 1. 改了什么

| 文件 | 改动 | 行数 |
|---|---|---|
| `docs/standards/coding.md` | 版本 v1→v2；适用去掉 `pubspec.yaml`；`FSD-12` 改名「规模与豁免」并删除依赖白名单、代码生成两条；`FSD-03:109` 删「不引入 mockito 等代码生成」；`FSD-09:243` 删「不得为保存连接新增依赖」；`A9` 删「新增依赖」；证据表 `FSD-12` 行改为只看 `A6` | 523 → 521 |
| `docs/standards/ui.md` | 版本 v1→v2；`UI-01` 删除指向 `coding.md` FSD-12 的子项，组件库规定保留 | 160 → 159 |
| `steering.md` | 索引里 `coding.md`、`ui.md` 两行版本标注改为 v2 | — |
| `FOLLOW.UPS.md` | `FUP-002` 改为已完成，完成标准改写为「`coding.md` 不再规定可引入哪些依赖」，证据指向本文件 | — |

未改动：`AGENTS.md`、`project.md`、`pubspec.yaml`、`.agents/skills/**`、`specs/p00-001`。

## 2. 每条 R 的证据

| R | 命令 | 实际输出 | 结论 |
|---|---|---|---|
| R1 | `sed -n '/^### FSD-12/,/^## /p' docs/standards/coding.md` | 段落只剩 3 条：250 行、固定豁免、版本化；标题为「规模与豁免」 | 通过 |
| R1 | 同上段落内 `grep -nE '第三方依赖\|依赖只允许\|build_runner\|json_serializable\|mockito'` | 0 命中 | 通过 |
| R1 | 同上段落内 `freezed` 计数 | 1 处，仅在「固定豁免」行的 `*.freezed.dart` —— 文件名，不是工具禁令（见 §4 勘误 A） | 通过 |
| R2 | `grep -n '\| 适用 \|' docs/standards/coding.md` | `\| 适用 \| lib/**、test/**、analysis_options.yaml \|` | 通过 |
| R2 | `grep -c '^\| 适用 \|.*pubspec' docs/standards/coding.md` | `0` | 通过 |
| R3 | `grep -c '新增依赖' docs/standards/coding.md` | `0` | 通过 |
| R3 | `grep -c '不引入 mockito' docs/standards/coding.md` | `0` | 通过 |
| R3 | `grep -n '不得写入文件' / '测试替身手写'` | `:243 - 连接信息只存在于内存：不得写入文件、SharedPreferences、数据库或剪贴板。` / `:109 - 测试替身手写，命名 FakeXxx 或 StubXxx。` | 通过（安全与测试写法保留） |
| R4 | `grep -c 'FSD-12' docs/standards/ui.md` | `0` | 通过 |
| R4 | `grep -n 'shadcn_flutter\|唯一组件库' docs/standards/ui.md` | `:23 ### UI-01 唯一组件库是 shadcn_flutter`，另 3 处使用条款完好 | 通过 |
| R5 | `grep -n '版本 \|' docs/standards/{coding,ui}.md` | 两份均为 `v2` | 通过 |
| R5 | `grep -n '已有（v' steering.md` | `:12 已有（v2，可审计）`、`:13 已有（v2）` | 通过 |
| R6 | `grep -c '^### FSD-'` / `grep -c '^### A[0-9]'` | 改前 `12 / 10`，改后 `12 / 10` | 通过 |
| R7 | 脚本逐字比对 `grill.md`「删除原文」与改前 9 段 | `全部 9 段逐字存在` | 通过 |

## 3. 没有做的事

- 未改 `p00-001` 第 6 节「只用 Flutter 内置组件」：按 `覆盖` 处理，留给它的 plan。
- 未在 `AGENTS.md` 新增依赖相关硬规则：`p00-004` §5 明确不做。
- 未改 `pubspec.yaml`：本次只解除规范层面的阻断，是否引入 `shadcn_flutter` 由 `p00-001` 的计划与实现决定。
- 未跑 `flutter analyze` / `flutter test`：本次只改 Markdown，`lib/`、`test/` 无变化。

## 4. 偏差与勘误

**A. R1 的可观察证据原文与 §5 冲突（已按勘误修正，未升版本）**

R1 原本写「`FSD-12` 段落内不再出现 … `freezed` …」，而 §5 明确保留「固定豁免」行里的 `*.freezed.dart`。按原文执行必然失败。经确认 §5 是实际决定（豁免的是规模统计口径，不是工具许可），因此把证据改成「`freezed` 只允许出现在豁免行的文件名里，不得作为工具禁令出现」。需求与决策未变，属证据口径勘误。

**B. R6 的动作编号范围写错（已按勘误修正）**

R6 原文写「`A1`–`A9`」，而 `coding.md` 的审计动作实际是 `A0`–`A9`（`A0` 为建立基线）。改为 `A0`–`A9`，数量仍为 10，不受影响。

**C. 跳过了 `plan.md`**

用户明确要求直接执行；`sdd-impl` 技能尚未创建，`sdd-plan` 也没有为本次生成计划。本次改动全部是删除 4 处条文、改 5 处文字与 3 处版本标注，7 条 R 自带可观察证据，因此按「跳过计划阶段」处理。需要留档的话可以补一份 `plan.md`，但它的内容将与本文件第 1、2 节重复。

## 5. 遗留

- `p00-001` 计划阶段遇到 `ui.md` 与第 6 节冲突时，需按 `覆盖` 留痕（`plan_lint` 的 L04/L08 会核对）。
- `ui.md:125` 的验证表仍要求 `grep -rn 'shadcn_flutter' pubspec.yaml lib` 至少一处命中。这是 `UI-01` 的落地检查，不是依赖策略，故保留；判定为不涉及。
- `FUP-001`（FSD-11 分析器配置）仍未触发。

## 6. 结论

**通过。** `coding.md` 不再规定可引入哪些依赖，`ui.md` 不再向它追认流程，两份规范之间的死锁解除；`FUP-002` 关闭。
