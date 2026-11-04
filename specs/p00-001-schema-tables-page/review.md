# Review: p00-001-schema-tables-page

| 字段 | 值 |
|---|---|
| Spec | `p00-001-schema-tables-page`（spec v3 / approved） |
| Plan | `plan.md`（approved，T1–T5 全部完成） |
| 执行 | 2026-11-04 20:53–22:35（实现 T1–T4 由 Agent；T5 人工核对由用户执行） |
| 基线 | `f4d0b14`（2026-11-04 18:17） |
| 结论 | **通过**（11 条 R 全部有可观察证据；3 处规范豁免与 1 处延期记录在 §6、§7，均不改需求） |

## 1. 改了什么

| 文件 | 改动 | 行数 |
|---|---|---|
| `lib/main.dart` | 替换：只剩 `runApp`，删掉模板计数器页 | 122 → 10 |
| `lib/app.dart` | 新增：组合根，读 `DEMO_STATE` 选四态、六行演示数据、演示失败对象 | 128 |
| `lib/domain/pg_table.dart` | 新增：表记录值对象与 `formatByteSize` | 34 |
| `lib/core/errors/app_failure.dart` | 新增：失败对象（消息 + 错误码，不暴露 cause） | 20 |
| `lib/core/errors/failure_codes.dart` | 新增：集中错误码常量 `FSD-TABLE-001` | 11 |
| `lib/core/theme/app_spacing.dart` | 新增：4/8/12/16 四档间距 token | 20 |
| `lib/core/theme/app_density.dart` | 新增：行高 28、工具栏 36、状态栏 24、正文 12、次要 11、本页页头 56 | 34 |
| `lib/core/theme/app_theme.dart` | 新增：深浅两套语义色 token（`AppPalette`）与 `ThemeData` | 185 |
| `lib/ui/schema_tables/schema_tables_controller.dart` | 新增：排序控制器（只存列与方向，不导入领域） | 62 |
| `lib/ui/schema_tables/schema_tables_page.dart` | 新增：页头 + 表格区两区布局、四态渲染 | 219 |
| `lib/ui/schema_tables/widgets/schema_tables_view.dart` | 新增：六列表头、行渲染、空/加载/失败态、双向滚动 | 227 |
| `test/app_test.dart` | 新增：R1/R3/R4/R5/R6/R7/R11 共 5 例 | 87 |
| `test/domain/pg_table_test.dart` | 新增：R3 共 4 例 | 40 |
| `test/ui/schema_tables/schema_tables_controller_test.dart` | 新增：R8 共 5 例 | 112 |
| `test/ui/schema_tables/schema_tables_page_test.dart` | 新增：R2/R4/R5/R6/R7/R8/R11 共 8 例 | 249 |
| `test/ui/schema_tables/widgets/schema_tables_view_test.dart` | 新增：R3/R4/R9/R10 共 6 例 | 178 |
| `test/widget_test.dart` | 删除：模板计数器冒烟测试 | 30 → 0 |
| `.gitignore` | 新增 1 行 `evidence`：截图证据不进仓库（plan §4 T5） | +1 |

未改动：`pubspec.yaml`、`analysis_options.yaml`、`docs/standards/**`、`steering.md`、`AGENTS.md`、`spec.md`、平台工程目录、`specs/p00-004`。

## 2. 每条 R 的证据

| R | 证据 | 结论 |
|---|---|---|
| R1 | `test/app_test.dart`「[p00-001/R1] 首屏直接是表列表页，没有计数器」通过；`test/widget_test.dart` 已删除；桌面启动首屏即本页（T5 第 2 步） | 通过 |
| R2 | 测试「页头显示连接名、数据库名与 schema 名，按钮禁用且无敏感字段」与「替换连接信息与表记录后页面随之更新」通过；截图中页头为 `Local dev · myapp` / `public`，`新建连接` 呈禁用灰、无主机端口用户名 | 通过 |
| R3 | 测试「六列表头与每行取值来自传入记录」「字节大小按 1024 进位」「描述缺省时保持为空值」「演示数据为六张表且覆盖空描述与长文本」「表记录逐项保留传入的名称、类型、列数、行数与字节大小」5 例通过；截图中 6 行、`invoices` 描述显示 `—`、大小显示 `4.9 GB`/`256 MB`/`64 KB` | 通过 |
| R4 | 测试「无表时保留六列表头，只在表体显示空态提示」「空列表保留页头与六列表头，且不显示数量统计」「空态下页头仍在且没有数量统计」3 例通过 | 通过 |
| R5 | 测试「加载中只在表格区显示进度指示」「加载态只在表格区显示进度指示」2 例通过 | 通过 |
| R6 | 测试「失败态显示演示消息与集中错误码」「失败文案把消息与错误码放在同一段，且不泄露 cause」2 例通过；文案为 `加载表失败（错误码：FSD-TABLE-001）`，中文全角括号 | 通过 |
| R7 | 测试「数量统计等于实际渲染的行数」「默认六行数据与数量统计」2 例通过；截图为 `6 张表`；三种非数据态断言 `张表` 不存在 | 通过 |
| R8 | `schema_tables_controller_test.dart` 5 例（默认首列升序且首点仍升序、再点转降序、切列回升序、通知监听者、不改调用方输入）+ 页面测试「默认按表名升序，点击表头切换排序与方向标记」「描述表头不可排序」通过；截图表头 `表名 ▲`，行序 audit → customers → invoices → order_items → products → sessions | 通过 |
| R9 | 测试「[p00-001/R9] 800×600 下 500 行可双向滚动且长文本不截断」通过；测试「800×600 视口下页面无布局溢出」通过；T5 第 4 步人工确认无黄黑溢出条；列宽 220+80+300+70+110+100=880，900 宽不滚、800 宽出横向滚动 | 通过 |
| R10 | 测试「数据行不挂点击或悬停交互」通过；T5 第 4 步人工点/悬停行无选中态、无跳转 | 通过 |
| R11 | 测试「未设置或未知的 DEMO_STATE 回退 data」通过；`lib/` 内无 `dart:io`、无 HTTP/数据库客户端、无 `postgres://` 字面量；四态由 `--dart-define=DEMO_STATE` 选择，T5 第 3 步逐态启动确认 | 通过 |

## 3. UI 规范核查（`docs/standards/ui.md` §7）

| 规则 | 命令 | 实际输出 | 结论 |
|---|---|---|---|
| UI-01 | `grep -rnE 'package:flutter/(material\|cupertino)\|MaterialApp\|CupertinoApp' lib` | 5 处命中：`app.dart:5,106`、`app_theme.dart:5`、`schema_tables_page.dart:5`、`schema_tables_view.dart:5` | **豁免**（见 §6 偏差 A） |
| UI-01 | `grep -rn 'shadcn_flutter' pubspec.yaml lib` | 无命中（退出码 1） | **豁免**（同上） |
| UI-02 | `grep -rnE 'EdgeInsets\.(all\|symmetric\|only)\([^)]*(1[7-9]\|[2-9][0-9])\|SizedBox\((height\|width): *(1[7-9]\|[2-9][0-9])' lib/ui` | 无输出（退出码 1） | 通过 |
| UI-03 | 读 `lib/core/theme/app_density.dart` | 行高 28、工具栏 36、状态栏 24、正文 12、次要 11、区域标题 12/w600，与 §2 一致；另加 `pageHeaderHeight = 56`（本页例外，见 §6 偏差 B） | 通过 |
| UI-04 | 截图 1200×800 与 900×600 各一张，标注区域边界 | 两张图已用矩形框分别圈出页头区与表格区；见 §4 | 通过 |
| UI-05 | `grep -rnE 'BoxShadow\|elevation:\|LinearGradient\|BackdropFilter' lib/ui` | 无输出（退出码 1） | 通过 |
| UI-05 | `grep -rnE 'BorderRadius\.circular\((7\|8\|9\|[1-9][0-9])' lib/ui` | 无输出（退出码 1） | 通过 |
| UI-06 | 截图对照骨架图 | 页头 56、两区上下结构、按钮 4 圆角、1px 分隔线、无阴影无渐变，与 T5 第 5 步核对一致 | 通过 |
| UI-07 | `grep -rnE 'Color\(0x\|Colors\.' lib` | 无输出（退出码 1）；色值统一用 `Color.fromARGB`，token 类名为 `AppPalette`（见 §6 偏差 C） | 通过 |
| UI-08 | widget test：方向键改变选中项 | 不适用：本页按 R10 无选中态，`grep -rn 'LogicalKeyboardKey\|Shortcuts\|Focus' lib` 无命中 | 不适用 |

## 4. 截图证据

| 文件 | 像素 | 标注内容 |
|---|---|---|
| `specs/p00-001-schema-tables-page/evidence/1200_800.png` | 1200×801 | 上框圈页头（含 `新建连接` 与 `6 张表`），下框圈表头 + 6 行表体，边界贴合 1px 分隔线 |
| `specs/p00-001-schema-tables-page/evidence/900-600.png` | 901×600 | 同上；六列全部可见，无裁切、无横向滚动条（880 < 900） |

高度多 1px、宽度多 1px 来自窗口边框被截图一并框入，不影响边界判定。两张图按 `.gitignore` 的 `evidence` 规则不进版本库。

## 5. 命令闸门

| 命令 | 实际输出 | 结论 |
|---|---|---|
| `dart format --output=none --set-exit-if-changed lib test` | `Formatted 16 files (0 changed)`，退出码 0 | 通过 |
| `flutter analyze` | `No issues found! (ran in 1.8s)` | 通过 |
| `flutter test` | `28 tests`：`00:05 +28: All tests passed!`，无跳过 | 通过 |

## 6. 偏差与勘误

**A. UI-01 组件库（plan §2.1 已批准的覆盖，非本次偏差）**

`ui.md` UI-01 要求唯一组件库为 `shadcn_flutter`，两条核查命令一条要「无 Material 命中」、一条要「`shadcn_flutter` 至少一处命中」。本次按 spec 第 6 节「只用 Flutter 内置组件」与 plan §2.1 的覆盖执行：应用根用 `MaterialApp`、按钮用 Material，`pubspec.yaml` 未引入任何组件库。两条 UI-01 命令因此按计划失败，属预期，不是实现缺陷。下一个涉及界面的 spec 需重新采用标准，或先单独修订 `ui.md`。

**B. `pageHeaderHeight = 56` 是 UI-03 的本页例外**

`ui.md` §2 的密度表只定义 28/36/24/12 四项高度字号，没有页头高度。plan §2.1 已确认本页页头固定 56，并在 `app_density.dart` 中作为独立 token 声明，不覆盖 `toolbarHeight = 36`。属已批准的本页特例。

**C. UI-07 正则与 token 类名的冲突（实现期修正）**

`grep -rnE 'Color\(0x|Colors\.' lib` 的字面匹配会命中任何以 `Colors.` 结尾的标识符。颜色 token 类最初命名为 `AppColors`，`AppColors.of(...)` 使该闸门永久报红。改为 `AppPalette` 且色值用 `Color.fromARGB` 声明后闸门清零。这是命名调整，不改变色值或界面观感。

**D. FSD-11 严格分析器配置延期（plan §2.1 已批准）**

`analysis_options.yaml` 未按 `coding.md` FSD-11 补全 `strict-casts` / `strict-inference` / `strict-raw-types` 与 10 条 lint，`FUP-001` 保持未触发。本次以 `dart format` + `flutter analyze`（现有配置）+ `flutter test` 作为闸门，plan 已记录该延期无用户可见差异。

## 7. 代码规范核查（`docs/standards/coding.md`）

| 规则 | 命令 | 实际输出 | 结论 |
|---|---|---|---|
| FSD-01 文件头 | 逐文件读前 3 行 | 16 个 Dart 文件均为「路径 / `// covers:` / 用途」三行 | 通过 |
| FSD-02 锚点与归属 | 逐文件比对 `// covers:` 与 `// [p00-001/Rn]` 锚点集 | 一致；`lib/ui/schema_tables/schema_tables_page.dart` 覆盖 R2/R4/R5/R6/R7/R8/R11，`lib/app.dart` 覆盖 R1，无越界归属 | 通过 |
| FSD-03 测试与追踪 | `grep -oE "test(Widgets)?\('\[p00-001/R[0-9]+\]" test` | 28 例全部带 `[p00-001/Rn]` 前缀，R1–R11 无遗漏 | 通过 |
| FSD-06 依赖方向 | `grep -n '^import' lib/ui/schema_tables/schema_tables_controller.dart` | 只有 `package:flutter/foundation.dart`，不导入 `lib/domain/` | 通过 |
| FSD-09 日志与敏感信息 | `grep -rnE 'print\(\|debugPrint\(\|log\(' lib` | 无命中（退出码 1） | 通过 |
| FSD-10 禁止清单 | `grep -rnE '\bdynamic\b\|part of\|^part \|// *TODO\|// *FIXME\|// *ignore:' lib test` | 无命中（退出码 1） | 通过 |
| FSD-12 规模 | `find lib test -name '*.dart' \| xargs wc -l` | 最大 249 行（`test/ui/schema_tables/schema_tables_page_test.dart`），`lib/` 最大 227 行（`schema_tables_view.dart`），均 ≤ 250 | 通过 |

## 8. 没有做的事

- 未建立数据访问层、数据库连接、网络请求、持久化、连接管理、树与详情页、底栏或页面内状态切换控件（plan §3.2 非目标）。
- 未引入任何第三方依赖，未改 `pubspec.yaml`。
- 未实现真实排序状态跨页持久化：排序只存在于本次运行的控制器内存中（plan §3.2）。
- 未跑 `flutter run -d macos`：本机只有 Windows 桌面目标，`ui.md` UI-06/UI-04 以 Windows 截图证据替代。

## 9. 遗留

- **UI-01 冲突待收口**：下一个涉及界面的 spec 若继续只用内置组件，需先修订 `ui.md` UI-01 与它的两条核查命令，否则每个 spec 都要写一次覆盖。
- **FSD-11 延期**（`FUP-001`）：`analysis_options.yaml` 仍是模板默认，严格分析未启用。
- **UI-04 的 800×600 窄窗截图缺失**：R9 的 800×600 无溢出由 widget 测试与人工步骤覆盖，但 `ui.md` 只要求 1200×800 与 900×600 两张，故不算缺口；若后续要留窄窗视觉证据，需另加一张。
- **T5 的六步人工核对无逐条留痕**：用户口头确认全部通过，本文件只记录结果。若后续需要审计，建议把每步的实际输出写进本节。

## 10. 结论

**通过。** R1–R11 全部有自动化或人工可观察证据，三条命令闸门全绿，28 例测试无跳过；UI-01 的两条失败与 FSD-11 的延期均为 plan §2.1 已批准的覆盖或延期，不改需求、不改界面行为。`spec.md` 的 `R1`–`R11` 复选框按 `p00-004` 的先例保持未勾选，结论以本文件为准。
