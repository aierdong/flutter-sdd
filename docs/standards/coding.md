# Flutter 代码规范

| 字段 | 值 |
|---|---|
| 版本 | v4 |
| 状态 | 生效 |
| 适用 | `lib/**`、`test/**`、`analysis_options.yaml` |
| 目的 | 约束代码本身写成什么样：文件与目录、命名、依赖方向、失败模型、日志与禁止用法 |

## 范围

本文件只规定代码本身长什么样。代码怎么产生、要不要验证、按什么顺序交付，属于执行计划与实现阶段的职责，本文件不涉及。

## 为什么要求留追踪令牌

需求与代码只靠一个键关联：`pNN-NNN/Rn`。同一个键必须出现在四个位置：

```text
spec 第 4 节 R1
  → 代码锚点 // [p00-001/R1]
  → 测试名   test('[p00-001/R1] ...')
  → 提交正文 R: p00-001/R1
```

任一位置缺失，需求与代码就对不上。因此每条规则都要求留下**唯一、可检索、难以碰巧满足**的代码痕迹，而不是“注意命名”“保持简洁”这类无法判定的要求。

本规范没有建议项。下列条款全部强制。唯一例外是文中明确写出的“条件适用”和“豁免”。

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

- 令牌必须与 `test(` / `testWidgets(` 写在同一行的第一个参数里，便于检索；`group()` 名称不得带令牌。
- `[support]` 只能出现在 `spec: support` 的测试文件里。
- 禁止 `skip:`、`tags: 'skip'` 和被注释掉的测试。
- 测试替身手写，命名 `FakeXxx` 或 `StubXxx`。

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
- 仓库里不得保留脚手架生成的计数器页面，也不得保留与之配套的 `test/widget_test.dart`。

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

- 数据库元数据类必须带 `Pg` 前缀：Flutter 自带 `Table`、`Column` 等同名组件，不加前缀会混淆，读代码时无法一眼区分领域模型和 UI 组件。
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
- 面向用户的失败文案必须包含错误码，格式固定：`<消息>（错误码：FSD-CONN-001）`。

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
- `ConnectionConfig.toString()` 必须遮蔽密码，输出中固定包含 `password: <redacted>`。
- 连接信息只存在于内存：不得写入文件、`SharedPreferences`、数据库或剪贴板。
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

### FSD-11 静态检查配置

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
- 分析器告警不得用 `ignore` 压掉。

### FSD-12 规模与豁免

- 单个手写 Dart 文件不超过 250 行（`test/fixtures/**` 除外）。
- 固定豁免只有：`*.g.dart`、`*.freezed.dart`、`lib/generated/**`、Flutter 平台目录（`android/`、`ios/`、`linux/`、`macos/`、`windows/`、`web/`）。其它豁免必须写进当前 spec 第 6 节并经人批准，不得在代码里静默绕过。

## 2. 最小示例

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
