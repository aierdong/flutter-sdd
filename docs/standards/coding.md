# Flutter 代码规范（可审计版）

| 字段 | 值 |
|---|---|
| 版本 | v1 |
| 状态 | 生效 |
| 适用 | `lib/**`、`test/**`、`pubspec.yaml`、`analysis_options.yaml` |
| 目的 | 约束写法，并让“是否遵守”能用命令、diff 和测试结果判定 |

## 为什么是“可审计”的

普通代码规范只能靠读代码判断，容易退化成“看起来还行”。本规范要求每条需求在代码里留下痕迹，把“遵守”变成一条可以逐环检查的链路：

```text
spec 第 4 节 R1
  → 代码锚点 // [p00-001/R1]
  → 测试名   test('[p00-001/R1] ...')
  → 提交正文 R: p00-001/R1
```

任一环缺失，审计都能定位到具体文件和规则。因此每条规则都必须留下**唯一、可检索、难以碰巧满足**的产物，而不是“注意命名”“保持简洁”这类无法判定的要求。

本规范没有建议项。下列条款全部强制，任一不通过即判不合规。唯一例外是文中明确写出的“条件适用”和“豁免”。

## 0. 术语

- **追踪令牌**：`pNN-NNN/Rn`，例如 `p00-001/R3`。它是需求到实现的唯一关联键。
- **需求锚点**：独占一行、以 `// [追踪令牌]` 开头的注释，紧贴实现该需求的声明。
- **支持代码**：不直接实现某条 R 的基础设施，包括入口、组合根、错误定义、日志、配置、主题、测试夹具。
- **生成代码**：`*.g.dart`、`*.freezed.dart`、`lib/generated/**`。

## 1. 规则

### FSD-01 文件头

`lib/`、`test/` 下每个手写 `.dart` 文件，从第一行起固定三行：

```dart
// spec: p00-001
// layer: data
// covers: p00-001/R1, p00-001/R3
```

| 字段 | 规则 |
|---|---|
| `spec` | 该文件涉及的全部 spec，按编号升序，用 `", "` 分隔；支持代码写 `support` |
| `layer` | `core` / `domain` / `data` / `ui` / `test`；`main.dart`、`app.dart` 记 `core` |
| `covers` | 该文件实现或测试的追踪令牌，升序；支持代码写 `none` |

- 三行顺序固定，字段名小写，冒号后一个空格。第三行之后空一行，再写 `import` 或声明。
- `spec` 与 `covers` 必须成对：`support` 只能配 `none`，普通文件不能写 `none`。
- 文件被后续 spec 改动时，把新 spec 和新令牌追加进去，不得留下已不存在于 spec 的令牌。
- 生成代码豁免。

反例：

```dart
// spec:p00-001          // 冒号后缺空格
// layer: data
// covers: R1            // 令牌缺 spec 前缀
```

### FSD-02 需求锚点与代码归属

实现一条 R 的位置必须留下锚点：

```dart
// [p00-001/R1] 用只读事务连接目标库，不执行任何写语句。
Future<List<PgSchema>> loadSchemas(ConnectionConfig config) async {
  // ...
}
```

- 锚点独占一行：`//` + 一个空格 + `[令牌]` + 一个空格 + 中文说明 + `。`
- 紧贴实现该需求的声明或其文档注释上方，锚点到声明之间不得有空行；若中间有文档注释，必须连续无空行。多条 R 可以叠放，一行一条。
- 锚点只能指向具体声明（类、方法、字段、顶层常量），不得挂在文件头或 import 区。
- 每条 R 至少一个锚点；同一个令牌可以出现多次，但每一处都必须真的实现对应行为。
- 令牌中的 spec id 必须存在于 `specs/`，R 编号必须存在于该 spec 第 4 节。
- 令牌只允许出现在四处：文件头 `covers`、需求锚点、测试名、提交正文 `R:` 行。不得写进普通说明注释、文档注释或字符串。
- 文件头 `covers` 集合必须等于该文件内锚点令牌的集合；测试文件则等于测试名令牌的集合。`[support]` 不是追踪令牌，不参与集合比较。

**代码归属**：

- 除支持代码外，每个文件至少覆盖一条 R。
- `spec: support` 只允许用于 `lib/main.dart`、`lib/app.dart`、`lib/core/**`、`test/core/**`、`test/support/**`、`test/fixtures/**`。
- 支持代码不得包含业务功能：数据库查询、业务模型、页面与组件、用例编排只能出现在带 R 锚点的文件里。

反例：`// TODO: 以后补 R1`、`// 这里对应 R1`、`const spec = 'p00-001/R1';`。

### FSD-03 测试与追踪

- 路径镜像：`lib/ui/browser/browser_page.dart` 对应 `test/ui/browser/browser_page_test.dart`。
- 测试文件名以 `_test.dart` 结尾；`test/support/**`、`test/fixtures/**` 例外，且这两处不得出现 `_test.dart`。
- 每个叶子 `test()` / `testWidgets()` 的第一个参数必须以下列之一开头，后接一个空格和中文描述：

```dart
test('[p00-001/R1] 连接成功时返回全部 schema', () async {
  // ...
});

testWidgets('[p00-001/R4] 刷新失败时显示错误码', (tester) async {
  // ...
});
```

- 令牌必须与 `test(` / `testWidgets(` 写在同一行的第一个参数里，便于机械检查；`group()` 名称不得带令牌。
- 每条 R 至少有一个通过的测试；`[support]` 只能出现在 `spec: support` 的测试文件里。
- 禁止 `skip:`、`tags: 'skip'` 和被注释掉的测试。
- 测试替身手写，命名 `FakeXxx` 或 `StubXxx`；不引入 mockito 等代码生成。

反例：`test('连接测试', ...)`、`group('R1', ...)`、`test('R1 ...')`（缺方括号和 spec 前缀）。

### FSD-04 提交追踪（条件适用）

当实现阶段产生 git 提交且 diff 含 `lib/` 或 `test/` 时：

```text
p00-001: 连接数据库并列出 schema

R: p00-001/R1, p00-001/R2
```

- 标题正则：`^p\d{2}-\d{3}: .+`；一个提交只属于一个 spec。
- 正文必须有一行以 `R: ` 开头，列出本提交触及的令牌，升序、用 `", "` 分隔。
- 纯文档、流程、脚手架提交使用 `docs:`、`chore:`、`ci:`、`build:` 前缀，不受本节约束；这类提交不得改动 `lib/` 或 `test/`。

未产生提交时，审计记为“不适用”，并写明原因。

### FSD-05 目录与文件命名

```text
lib/
  main.dart            # 只调用 runApp
  app.dart             # 唯一组合根：依赖装配、路由、主题
  core/
    errors/
    logging/
    config/
    theme/
  domain/
  data/
  ui/
    <feature>/
      <feature>_page.dart
      <feature>_controller.dart
      widgets/<name>_view.dart
test/
  <与 lib 镜像的目录>/
  support/
  fixtures/
```

| 路径 | 文件名规则 |
|---|---|
| `lib/domain/**` | snake_case，与主类同名，如 `pg_schema.dart` → `PgSchema` |
| `lib/data/**` | 必须以 `_repository.dart`、`_client.dart`、`_dto.dart`、`_mapper.dart` 之一结尾 |
| `lib/ui/**` | 必须以 `_page.dart`、`_view.dart`、`_controller.dart` 之一结尾 |
| `test/**` | 以 `_test.dart` 结尾；`support/`、`fixtures/` 内不得用此后缀 |

- `lib/core/**` 只允许 `errors/`、`logging/`、`config/`、`theme/` 四个子目录；不得新增 `utils/`、`helpers/`、`common/`。
- 根目录除 `main.dart`、`app.dart` 外不得出现其它 `.dart` 文件。
- 文件名与目录名统一 snake_case；不使用 `lib/features/`、`lib/screens/`、`lib/widgets/` 这类第二套分层。
- 脚手架生成的计数器页面和 `test/widget_test.dart` 必须在首个 spec 交付前删除或替换。

### FSD-06 依赖方向

允许的依赖是单向的：

```text
ui → data → domain → core
```

- `lib/core/**` 不得 import `domain/`、`data/`、`ui/`。唯一例外是 `lib/app.dart`（组合根）。
- `lib/domain/**` 只能 import `dart:*` 和 `core/errors/`；不得 import `package:flutter/`、`package:postgres/`、`data/`、`ui/`。
- `lib/data/**` 可以 import `core/errors/`、`core/config/`、`core/logging/`、`domain/` 和 PostgreSQL 驱动；不得 import `package:flutter/`、`ui/`。
- `lib/ui/**` 可以 import 任意本地层；不得 import `package:postgres/`。
- 项目内 import 一律写成 `package:<app>/...` 绝对导入；禁止用 `../`、`./` 跨目录相对导入。
- `*_controller.dart` 只能 import `package:flutter/foundation.dart`，不得 import `material.dart`、`widgets.dart`、`cupertino.dart`。
- PostgreSQL 驱动只允许出现在 `lib/data/**`。

反例：

```dart
// lib/domain/pg_table.dart
import 'package:flutter/material.dart'; // 违反：domain 必须能在纯 Dart 下编译

// lib/ui/browser/browser_controller.dart
import 'package:flutter/material.dart'; // 违反：controller 只使用 foundation
```

### FSD-07 命名

| 类别 | 规则 | 示例 |
|---|---|---|
| PostgreSQL 元数据模型 | 以 `Pg` 开头；至少覆盖 schema、table、column、constraint、foreign key、index | `PgSchema`、`PgTable`、`PgColumn`、`PgConstraint`、`PgForeignKey`、`PgIndex` |
| 路由级页面 | `*Page` | `BrowserPage` |
| 可复用组件 | `*View` | `SchemaTreeView` |
| 状态对象 | `*Controller`，继承 `ChangeNotifier` | `BrowserController` |
| 数据访问 | `*Repository`、`*Client`、`*Dto`、`*Mapper` | `SchemaRepository` |
| 失败 | 只用 `AppFailure`，不派生其它异常类型 | `AppFailure` |
| 测试替身 | `Fake*` 或 `Stub*` | `FakeSchemaRepository` |

- 数据库元数据类必须带 `Pg` 前缀：Flutter 自带 `Table`、`Column` 等同名组件，不加前缀会混淆，审计时也无法一眼区分领域模型和 UI 组件。
- 领域词与 PostgreSQL 文档一致，不使用 `Dataset`、`ResultSet` 替代 `PgSchema`、`PgTable`。
- 文件名与主类名一致：`browser_page.dart` → `BrowserPage`。

### FSD-08 失败模型与错误码

唯一失败类型定义在 `lib/core/errors/app_failure.dart`：

```dart
final class AppFailure implements Exception {
  const AppFailure({required this.code, required this.message, this.cause});

  final String code;
  final String message;
  final Object? cause;
}
```

- 错误码集中定义在 `lib/core/errors/failure_codes.dart`。格式 `FSD-<AREA>-<NNN>`，`AREA` 只能是 `CONN`、`SCHEMA`、`TABLE`、`UI`、`INTERNAL`；编号三位，按区域递增，不得复用。
- `FSD-` 字面量只允许出现在 `failure_codes.dart` 和 `test/**` 的断言里；业务代码必须引用常量。
- 业务代码只抛 `AppFailure`；禁止 `throw Exception(...)`、`throw StateError(...)`、`throw ArgumentError(...)`。编程错误用 `assert`。
- 禁止无类型的 `catch (e)`；禁止空 catch。每个 catch 必须映射成带错误码的 `AppFailure` 并记录日志，或重新抛出 `AppFailure`。
- 数据层负责把驱动异常翻译成 `AppFailure`；驱动异常不得越过 `lib/data/`。
- 面向用户的失败文案必须包含错误码，格式固定：`<消息>（错误码：FSD-CONN-001）`；至少有 widget test 断言 `find.textContaining('错误码：')`。

反例：

```dart
try {
  await client.connect();
} catch (e) {
  throw Exception('连接失败'); // 违反：无错误码、非 AppFailure、catch 无类型
}
```

### FSD-09 日志与敏感信息

- 日志统一走 `lib/core/logging/app_log.dart` 的 `AppLog.info/warn/error`；`lib/` 和 `test/` 中禁止 `print(`、`debugPrint(`。
- `AppLog.error` 必须接收 `AppFailure`；日志只写 host、port、database 等非敏感字段，密码、完整连接串、驱动异常原文不得进入日志。
- `ConnectionConfig.toString()` 必须遮蔽密码，输出中固定包含 `password: <redacted>`；必须有测试覆盖。
- 连接信息只存在于内存：不得写入文件、`SharedPreferences`、数据库或剪贴板；不得为保存连接新增依赖。
- `lib/**` 中不得出现 `postgres://`、`postgresql://` 字面量；连接串由结构化字段拼装。测试夹具只能使用 `localhost` 和明显的假密码，并放在 `test/fixtures/**`。
- 错误文案与日志都不得包含密码或完整连接串。

反例：

```dart
debugPrint('connecting postgres://reader:secret@localhost/db'); // 两处违反
```

### FSD-10 禁止清单

- `lib/**` 禁止 `dynamic` 和 `as dynamic`；JSON 边界用 `Object?` 加显式类型转换。
- 禁止 `part` / `part of`。
- 禁止 `// ignore:` 不带同行理由；确需忽略时必须写成 `// ignore: <rule> 理由：<具体原因>`。
- 禁止无归属的 `TODO` / `FIXME`。允许的格式是 `// TODO(p00-002): <内容>`，指向一个已规划但尚未开始的 spec；当前 spec 的未完成工作不得用 TODO 代替。
- 禁止在 `lib/` 留下模板计数器、示例代码，以及没有被任何文件引用的公共类。

### FSD-11 静态检查与格式

项目根 `analysis_options.yaml` 至少包含：

```yaml
include: package:flutter_lints/flutter.yaml

analyzer:
  language:
    strict-casts: true
    strict-inference: true
    strict-raw-types: true

linter:
  rules:
    always_declare_return_types: true
    avoid_dynamic_calls: true
    avoid_print: true
    directives_ordering: true
    prefer_const_constructors: true
    prefer_const_declarations: true
    unawaited_futures: true
    use_super_parameters: true
```

- 不得通过 `exclude` 排除 `lib/` 或 `test/` 下的手写文件。
- 每次交付必须跑：

```bash
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
```

- 通过标准：`dart format` 退出码 0；`flutter analyze` 输出 `No issues found!`；`flutter test` 输出 `All tests passed!` 且没有跳过用例。
- 分析器告警不得用 ignore 压掉；修代码，或回 spec 改需求。

### FSD-12 规模、依赖与豁免

- 单个手写 Dart 文件不超过 250 行（`test/fixtures/**` 除外）。
- 第三方依赖只允许：Flutter SDK 自带、模板默认的 `cupertino_icons`、PostgreSQL 驱动（`postgres` 或 spec 第 6 节选定的等价包）、`flutter_lints`。新增任何其它运行时或开发依赖，必须先在 spec 第 6 节记录决策。
- 不使用代码生成：不引入 `build_runner`、`freezed`、`json_serializable`、`mockito`；测试替身手写。
- 固定豁免只有：`*.g.dart`、`*.freezed.dart`、`lib/generated/**`、Flutter 平台目录（`android/`、`ios/`、`linux/`、`macos/`、`windows/`、`web/`）。其它豁免必须写进当前 spec 第 6 节并经人批准，不得在代码里静默绕过。
- 规范变更本身也要版本化：改动本文件时递增顶部版本，并同步 `steering.md`。

## 2. 最小合规样例

`lib/data/schema_repository.dart`（包名以 `pubspec.yaml` 的 `name` 为准，这里用 `flutter_sdd`）：

```dart
// spec: p00-001
// layer: data
// covers: p00-001/R1

import 'package:flutter_sdd/core/config/connection_config.dart';
import 'package:flutter_sdd/core/errors/app_failure.dart';
import 'package:flutter_sdd/domain/pg_schema.dart';
import 'package:postgres/postgres.dart';

final class SchemaRepository {
  SchemaRepository(this._config);

  final ConnectionConfig _config;

  // [p00-001/R1] 用只读连接枚举全部 schema。
  Future<List<PgSchema>> loadSchemas() async {
    // ...
  }
}
```

`test/data/schema_repository_test.dart`：

```dart
// spec: p00-001
// layer: test
// covers: p00-001/R1

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('[p00-001/R1] 连接成功时返回全部 schema', () async {
    // ...
  });
}
```

提交：

```text
p00-001: 连接数据库并列出 schema

R: p00-001/R1
```

## 3. 审计

审计顺序固定：先机械检查，再人工确认。A0–A5、A8 使用 bash + ripgrep；A6 使用 PowerShell；A7 在任意 shell 执行。把 `<base>` 换成上一个已验收提交，`<spec>` 换成当前 spec 目录，`<spec-id>` 换成当前 spec 编号。

### A0 建立基线

```bash
git diff --name-only <base>..HEAD
sed -n '/## 4\. 必须做到/,/## 5\. 明确不做/p' specs/<spec>/spec.md
```

把第 4 节的 R 编号写成清单，作为 A2、A3 的对照。日常自检只看本次 diff 触及的 `lib/`、`test/` 文件；最终验收扩大到全部文件。

### A1 文件头

```bash
rg -U --files-without-match '\A// spec: [^\n]+\n// layer: (core|domain|data|ui|test)\n// covers: [^\n]+\n' --glob '*.dart' --glob '!**/*.g.dart' --glob '!**/*.freezed.dart' --glob '!lib/generated/**' lib test
```

无输出即通过。再抽查 `spec` 与 `covers` 是否成对（支持代码应为 `support` + `none`）。

### A2 锚点覆盖

```bash
rg -o --no-filename -r '$1' '^\s*// \[(p[0-9]{2}-[0-9]{3}/R[0-9]+)\]' lib | sort -u | rg '^<spec-id>/'
```

把 `<spec-id>` 换成当前 spec；输出与 A0 的 R 清单逐条对照：

- spec 清单中的每条 R 都必须出现。
- 输出中不得出现 spec 清单以外的令牌。
- 每个令牌都能在 `lib/` 找到锚点下方的实现声明。
- 每个文件的锚点集合与文件头 `covers` 一致。

常见违规：`// [p00-001/R9]` 而 spec 只有 R1–R5；锚点悬在 import 上方；锚点与声明之间夹着空行。

### A3 测试覆盖

```bash
rg -o --no-filename -r '$1' '^\s*(?:test|testWidgets)\(\x27\[(p[0-9]{2}-[0-9]{3}/R[0-9]+)\]' test | sort -u | rg '^<spec-id>/'
rg -n '^\s*(test|testWidgets)\(' test | rg -v '(test|testWidgets)\(\x27\[(p[0-9]{2}-[0-9]{3}/R[0-9]+|support)\]'
rg -n '^\s*group\(' test | rg 'p[0-9]{2}-[0-9]{3}/R[0-9]+'
rg -n '\bskip:' test
```

第一条输出必须等于“全部 R”，第二条必须为空，第三条必须为空（令牌不得出现在 group 名），第四条必须为空（或 `skip:` 只出现在夹具字符串里，需人工确认）。

### A4 错误码与异常

```bash
rg -n 'FSD-' lib --glob '!**/failure_codes.dart'
rg -n 'FSD-' lib/core/errors/failure_codes.dart
rg -o --no-filename 'FSD-[A-Z]+-[0-9]{3}' lib/core/errors/failure_codes.dart | sort | uniq -d
rg -o --no-filename 'FSD-[A-Z]+-[0-9]{3}' lib/core/errors/failure_codes.dart | rg -v '^FSD-(CONN|SCHEMA|TABLE|UI|INTERNAL)-[0-9]{3}$'
rg -n 'throw (Exception|StateError|ArgumentError|UnsupportedError)' lib
rg -n '\bcatch\s*\(' lib
rg -n '错误码：' lib/ui
```

前两条应确认：`failure_codes.dart` 之外的 `lib/` 没有 `FSD-` 字面量；码表本身使用规定的 `AREA`。第三条应无输出（无重复码）。第四条应无输出（无非法区域）。第五条应无输出（无裸异常）。第六条逐条确认都是 `on <Type> catch`。第七条至少命中每个展示失败的位置。

### A5 分层与禁止项

```bash
rg -n 'package:flutter/' lib/domain lib/data
rg -n 'package:postgres/' lib --glob '!lib/data/**'
rg -n 'package:[a-z0-9_]+/(domain|data|ui)/' lib/core --glob '!lib/app.dart'
rg -n 'package:[a-z0-9_]+/(data|ui)/' lib/domain
rg -n 'package:[a-z0-9_]+/ui/' lib/data
rg -n 'package:flutter/(material|widgets|cupertino)' lib/ui --glob '*_controller.dart'
rg -n "import '\.\.?/" lib test
rg -n '\bdynamic\b' lib --glob '*.dart'
rg -n '\b(print|debugPrint)\s*\(' lib test
rg -n '^\s*part( of)?\s' lib test
rg -n '// ignore:' lib test
rg -n 'TODO|FIXME' lib test
```

除 `dynamic`、`ignore`、`TODO` 的命中需要按 FSD-10 的允许格式逐条确认外，其余都应为空。

### A6 文件规模

```powershell
Get-ChildItem lib,test -Recurse -Filter *.dart |
  Where-Object { $_.FullName -notmatch '\\(fixtures|generated)\\' -and $_.Name -notmatch '\.(g|freezed)\.dart$' } |
  ForEach-Object {
    $n = (Get-Content -LiteralPath $_.FullName).Count
    if ($n -gt 250) { "$n`t$($_.FullName)" }
  }
```

无输出即通过。

### A7 静态闸门

```bash
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
```

三条命令退出码均为 0，且输出满足 FSD-11 的通过标准。

### A8 提交

```bash
git log --format='%h %s' <base>..HEAD
git log --format='%B' <base>..HEAD | rg '^R: '
```

逐个交付提交检查：标题符合 `pNN-NNN: ...`；正文 `R:` 行覆盖本次 diff 触及的全部令牌；没有跨 spec 混提交。纯文档提交按 FSD-04 判为不适用。

### A9 人工确认

以下条目无法只靠正则判断，必须打开文件看：

- 锚点下方的声明确实实现了对应 R，而不是“贴标签”。
- 支持代码里没有业务逻辑；`lib/core/` 只有错误、日志、配置、主题。
- 每条 R 的错误路径有 `AppFailure` 和错误码，UI 实际展示了错误码。
- 日志、错误文案、UI 中没有密码、完整连接串或驱动异常原文。
- 新增依赖、豁免与 spec 第 6 节的决策一致。

## 4. 判定与证据

- 通过 A1–A8，且 A9 无问题：**合规**。
- 任一机械检查不符合，或 A9 发现贴标签、越界、泄密：**不合规**。不合规必须列到文件与行号，并回到实现阶段修。
- 不允许用“大部分符合”“不影响功能”作为通过理由。

审查结论按下面格式记录到 `review.md`：

| 规则 | 证据 | 结论 |
|---|---|---|
| FSD-01 | A1 无输出 | 通过 |
| FSD-02 | A2 输出与 R1–R5 一致；抽查 3 处锚点 | 通过 |
| FSD-03 | A3 输出等于 R1–R5；未发现无令牌测试 | 通过 |
| FSD-04 | A8 提交标题与 `R:` 行符合 | 通过 |
| FSD-05 | A5 无越层；目录与后缀抽查 | 通过 |
| FSD-06 | A5 无驱动/Flutter 越层 import | 通过 |
| FSD-07 | 抽查类名与文件名 | 通过 |
| FSD-08 | A4 码表无重复、无裸异常、UI 含错误码 | 通过 |
| FSD-09 | 无 `print`；脱敏测试通过 | 通过 |
| FSD-10 | A5 禁止项无违规命中 | 通过 |
| FSD-11 | 三条命令全绿 | 通过 |
| FSD-12 | 无新增依赖；A6 无输出 | 通过 |

证据必须是命令输出、`file:line` 或测试结果；没有证据的项目按“未检查”处理，不能写“通过”。

## 5. 变更与解释

- 本文件版本在顶部；每次修改都递增版本，并在 `steering.md` 索引行标注新版本。
- 条款冲突时按更严格的一条执行；仍无法判断时停下来问人，不得自行豁免。
- 本规范约束“怎么做”，不定义“做什么”。需求仍以 `spec.md` 第 4 节为准；规范不能替代 spec。
- 新增或调整规则时，必须同步给出对应的审计动作（A1–A9）；没有审计动作的规则不得写进本文件。

## 6. 实现完成前自检

Agent 在宣布实现完成前，按顺序执行并保留输出：

1. A1 文件头无遗漏。
2. A2 每条 R 都有锚点，没有多余令牌，锚点与 `covers` 一致。
3. A3 每条 R 都有测试，所有测试名带令牌。
4. A4 错误码集中、无裸异常、UI 含错误码。
5. A5 分层与禁止项无违规命中。
6. A6 无超长文件。
7. A7 三条命令全绿。
8. A8 提交格式正确（有提交时）。

八项都通过才能进入 `sdd-review`；缺一项就是“未完成”，不是“基本完成”。宣布完成时，回复里必须附上 A1–A8 的命令输出摘要；只写“已遵守规范”不算证据。
