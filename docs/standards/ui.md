# Flutter 界面设计规范（桌面工具型）

| 字段 | 值 |
|---|---|
| 版本 | v2 |
| 状态 | 生效 |
| 适用 | `lib/ui/**`、`lib/core/theme/**`、`lib/app.dart` |
| 目的 | 让“界面是否符合设计基调”能用命令、截图和 widget test 判定，而不是靠观感争论 |

本文件只约束**长什么样**，不约束代码写法（写法见 [coding.md](coding.md)）。这是 Demo 规范：条款少，但每条都能验。没有建议项，全部强制。

## 0. 一句话基调

**桌面工具，不是网页。** 信息密度优先；功能区域靠**线条和底色**切分，不靠留白；窗口缩到 900×600 仍可读。

通过判据（人工，二选一即算违反）：

- 遮挡所有空白后，各区域边界依然清晰可辨。
- 把任意两块区域的间距减半，界面不会变得“更挤一点点”——挤不挤不该由留白决定。

## 1. 组件库

### UI-01 唯一组件库是 shadcn_flutter

- `lib/ui/**` 与 `lib/app.dart` 只使用 `package:shadcn_flutter/shadcn_flutter.dart`；主题根用 `ShadcnApp`，不用 `MaterialApp` / `CupertinoApp`。
- 不得 import `package:flutter/material.dart`、`package:flutter/cupertino.dart`。
- shadcn_flutter 里没有的组件，先在 `lib/ui/<feature>/widgets/` 里用 `package:flutter/widgets.dart` 自建 `*View`，不得为了凑组件去引 Material。

## 2. 密度

### UI-02 间距只有四档

间距尺度固定为 `4 / 8 / 12 / 16`，定义在 `lib/core/theme/app_spacing.dart`，界面里引用常量，不写字面量。

| 档位 | 名称 | 用在哪 |
|---|---|---|
| 4 | `space1` | 图标与文字之间、徽标内边距 |
| 8 | `space2` | 行内元素、按钮组、面板内边距 |
| 12 | `space3` | 面板内边距上限 |
| 16 | `space4` | 区域内容与分隔线之间 |

- 任意 `EdgeInsets`、`SizedBox`、`gap` 不得超过 16。
- 禁止用留白表达分组：分组用分隔线或底色，见 UI-04。

### UI-03 行高与字号

| 元素 | 值 |
|---|---|
| 树节点 / 表格行 / 工具按钮 | 高度 28 |
| 顶部工具栏 | 高度 36 |
| 底部状态栏 | 高度 24 |
| 正文 | 12 |
| 次要文本（路径、类型、计数） | 11 |
| 区域标题 | 12，`FontWeight.w600` |

- 字号、行高同样只在 `lib/core/theme/app_density.dart` 定义，界面引用常量。

## 3. 区域划分

### UI-04 线条切区域，底色分层级

三层结构固定，不得混用手段：

| 层级 | 划分手段 | 说明 |
|---|---|---|
| 区域（region） | 1px 分隔线 | 如 树 / 详情 / 工具栏 / 状态栏 之间 |
| 面板（panel） | 底色差一档 | 画布 `surface` → 面板 `surfaceMuted` |
| 行（row） | 选中态色块 | 选中行用 `accent` 底色，不靠加粗或缩进 |

- 分隔线一律 1px，颜色取主题 `border`；不得用 2px“粗线”补层次感。
- 一块区域最多一条分隔线与相邻区域接壤，禁止“线 + 空隙 + 线”的双重分隔。

### UI-05 禁止装饰性视觉

- 禁止阴影（`BoxShadow`、`elevation`）。
- 圆角上限 6；工具型界面按钮、输入框、卡片统一 4。
- 禁止渐变、毛玻璃、大图背景、动画超过 150ms 的过渡。

## 4. 页面骨架

### UI-06 固定骨架

`BrowserPage` 用 `Column` + `Row` 拼装，区域位置固定：

```text
+----------------------------------------------+
| toolbar   h=36   connection / refresh        |
+--------------+-------------------------------+
| tree  w=240  | detail  Expanded              |
|  database    |   columns       (n)           |
|   +- schema  |   constraints   (n)           |
|     +- table |   foreign keys  (n)           |
|              |                               |
+--------------+-------------------------------+
| status bar  h=24  error code / rows          |
+----------------------------------------------+
```

- 左栏固定 240 宽，右栏 `Expanded`；不使用可拖拽分栏（Demo 不做）。
- 右栏三段之间用 1px 分隔线，段标题 28 高且左对齐。
- 空态不用插图：一行 11 号次要文本 + 错误码。

## 5. 颜色

### UI-07 颜色只来自主题 token

- 语义 token 固定为：`canvas`、`surface`、`surfaceMuted`、`border`、`text`、`textMuted`、`accent`、`error`，定义在 `lib/core/theme/app_theme.dart`。
- 界面代码不得出现 `Color(0x...)`、`Colors.*`、内联十六进制。
- 深浅主题都要能跑；新增颜色先进 token，再谈用在哪。

## 6. 可访问性下限

### UI-08 键盘与对比度

- 树支持上下方向键移动选中项，Enter 展开/收起。
- 正文与背景对比度不低于 4.5:1；`textMuted` 只用于 11 号次要文本，不承载唯一信息（错误必须同时有文字和错误码）。

## 7. 怎么验

每条规则对应一个动作，跑完把输出记进 `review.md`。

| 规则 | 动作 | 通过标准 |
|---|---|---|
| UI-01 | `grep -rnE 'package:flutter/(material\|cupertino)\|MaterialApp\|CupertinoApp' lib` | 无输出 |
| UI-01 | `grep -rn 'shadcn_flutter' pubspec.yaml lib` | `pubspec.yaml` 与主题根各至少一处命中 |
| UI-02 | `grep -rnE 'EdgeInsets\.(all\|symmetric\|only)\([^)]*(1[7-9]\|[2-9][0-9])\|SizedBox\((height\|width): *(1[7-9]\|[2-9][0-9])' lib/ui` | 无输出 |
| UI-03 | 打开 `lib/core/theme/app_density.dart`，确认六项值齐全 | 值与 §2 表格一致 |
| UI-04 | 截图 1200×800 与 900×600 各一张，标注区域边界 | 遮挡留白后边界仍可辨；分隔线均为 1px |
| UI-05 | `grep -rnE 'BoxShadow\|elevation:\|LinearGradient\|BackdropFilter' lib/ui` | 无输出 |
| UI-05 | `grep -rnE 'BorderRadius\.circular\((7\|8\|9\|[1-9][0-9])' lib/ui` | 无输出（>6 违反） |
| UI-06 | `flutter run -d macos` 后按骨架图逐块对照 | 四块区域、两栏宽度与三处高度符合 |
| UI-07 | `grep -rnE 'Color\(0x\|Colors\.' lib` | 无输出 |
| UI-08 | widget test：`sendKeyEvent(LogicalKeyboardKey.arrowDown)` 后选中项变化 | 测试通过 |

说明：

- 用 `grep -rnE` 而不是 `rg`，因为本机未安装 ripgrep；命令可直接复制执行。
- `grep` 退出码 1 表示无命中（即通过），退出码 2 表示路径不存在。`lib/ui/` 尚未创建时，UI-02、UI-05 记为“不适用”，不算通过也不算失败。
- 表内 `\|` 是 Markdown 表格转义，复制到终端时还原成 `|`。

补充两条通用闸门（沿用 coding.md FSD-11）：

```bash
flutter analyze
flutter test
```

两条都退出码 0 才算界面改动完成。截图类证据无法自动化，必须在 `review.md` 里贴出路径或尺寸说明，不能只写“已检查”。

## 8. 豁免

- 平台目录（`macos/`、`windows/`）不受本规范约束。
- 窗口级根布局允许一处 0 外边距，不算“间距超 16”。
- 其它豁免必须写进当前 spec 第 6 节并经人确认，不得在代码里静默绕过。

## 9. 变更

- 改本文件递增顶部版本，并同步 `steering.md` 索引行的版本标注。
- 与 [coding.md](coding.md) 冲突时，代码写法听 coding.md，视觉表现听本文件。
