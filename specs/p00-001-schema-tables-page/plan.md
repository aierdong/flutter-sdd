# Plan: 单 schema 表列表页（纯 UI）

| 字段 | 值 |
|---|---|
| Spec | `p00-001-schema-tables-page`（spec v3 / approved） |
| Status | `approved` |

## 1. 方案摘要

**用户会看到的变化**：
- 启动即进入单 schema 表列表，不再看到计数器；测试套件中没有计数器冒烟测试；页面只有页头和表格区，不出现左侧树、详情面板或底部状态栏。
- 页头比规范工具栏更高，左侧两行显示 `Local dev · myapp` 与 `public`，右侧显示禁用的 `新建连接`；按钮点击不改变界面，页头不展示主机、端口、用户名或密码。连接名、数据库名和 schema 名均随传入值变化；点击禁用按钮不会改变页面。使用 Material 根只改变应用框架，不改变本页交互。
- 默认显示 `表名`、`类型`、`描述`、`列数`、`估算行数`、`大小` 六列及 6 行演示数据和 `6 张表`；各行取值来自传入数据，空描述显示 `—`，类型显示 `Table`，大小按 B/KB/MB/GB 等人类可读单位展示；演示数据覆盖空描述、长表名、不同列数、行数与大小。换入连接名、数据库名、schema 或表数据后，对应文本、字段值与数量随之变化。
- 表名、类型、列数、估算行数、大小可排序，默认表名升序；点击一列先升序，再点同列切为降序；文本按字典序、数值列按数值、大小按字节比较；描述不可排序，当前方向显示 `▲` 或 `▼`。
- 空态保留六列表头并显示 `该 schema 下暂无表。`；加载态只在表格区显示进度指示。
- 失败态在表格区按 `<消息>（错误码：FSD-<AREA>-<NNN>）` 格式同段显示消息与错误码；三种状态都保留页头且不显示数量。
- 窗口缩到 800×600 不溢出；长文本不截断，表格可双向滚动，500 行可滚到最后一行；不分页、不启用虚拟滚动；点击或悬停数据行不选中、不导航、不打开详情。
- 无数据库或网络时，仍可用启动参数选择数据、空、加载、失败四态；每种状态都能渲染，连接信息、schema、表数据和状态均由外部传入，替换这些输入会更新页面；页面不连接、不读写数据库，UI 不引用 PostgreSQL 驱动且运行时不发起网络请求。

**怎么做到**：启动入口读取 `DEMO_STATE` 并装配固定演示连接信息、schema、表数据和页面状态；纯 Dart 表模型承载输入；页面控制器只维护排序列和方向，并对输入副本排序；Flutter 内置组件负责页面与滚动，不加第三方依赖。

**为什么这么切**：不采用通用树形浏览器骨架，避免引入本期明确不做的树、详情和底栏；不把排序塞入页面构建逻辑，便于独立验证比较规则与输入不变；不用真实数据库，四态可脱网评审。

**代价**：需要自行拼装可排序表头、状态区与双向滚动，且 500 行会全部构建；自动测试能覆盖数据、状态、排序与布局行为，但桌面字体观感、禁用按钮样式及真实窗口滚动仍需人工截图核对。UI-01 的组件差异只影响实现方式，不改变界面行为；延期的 FSD-11 严格配置无用户可见差异，因为现有格式、分析与测试命令仍执行。

**需要用户决定的事项**：见 2.1 的 7 条。

**覆盖核对**：

| R | 落点（照抄原文，6–20 字） |
|---|---|
| R1 | 测试套件中没有计数器冒烟测试 |
| R2 | 右侧显示禁用的 `新建连接` |
| R3 | 空描述显示 `—` |
| R4 | `该 schema 下暂无表。` |
| R5 | 加载态只在表格区显示进度指示 |
| R6 | 同段显示消息与错误码 |
| R7 | `6 张表` |
| R8 | 文本按字典序、数值列按数值 |
| R9 | 500 行可滚到最后一行 |
| R10 | 点击或悬停数据行不选中 |
| R11 | 运行时不发起网络请求 |

## 2. 约束

### 2.1 需要用户确认的例外

| 这次要打破什么 | 为什么 | 什么时候回到标准 |
|---|---|---|
| 覆盖 `docs/standards/ui.md` UI-01：本次仅用 Flutter 内置组件，应用根与按钮等允许使用 Material，不引入 shadcn_flutter。 | 需求已限定仅使用 Flutter 内置组件。 | 下一个涉及界面的 spec 重新采用标准，或先单独修订标准。 |
| 覆盖 `docs/standards/ui.md` UI-06：只做页头与单 schema 表格，不做树、详情分栏和底部状态栏。 | 需求只定义单 schema 表列表且排除详情。 | 引入树形浏览器的 spec 启动时恢复并重新评估布局。 |
| 覆盖 `docs/standards/ui.md` UI-06：空态只显示规定提示，不额外附加错误码。 | 没有表不是加载失败，需遵守已批准的空态文案。 | 本 spec 结束后其他页面仍按标准处理。 |
| 覆盖 `docs/standards/ui.md` UI-03：仅本页页头由 36 增高至 56，容纳两行文字。 | 已选择增加页头余量以避免两行文字拥挤。 | 本 spec 结束后其他工具栏仍为 36，引入新骨架时重评。 |
| 覆盖 `docs/standards/coding.md` FSD-11：仅延期严格分析器配置和额外 lint，不改变现有配置。 | 需求已明确延期，避免夹带配置和告警修复。 | 下一个代码交付 spec 或专门的规范配置 spec 启动时。 |
| 仅本次：排序使用独立页面控制器，不引入全局状态库或数据访问层。 | 已选择独立验证排序，避免比较逻辑与页面耦合。 | 下一个需要共享排序或接入真实数据的 spec 重评，不推广为通用件。 |
| 仅本次：大小按 1024 进位，除 B 外最多一位小数，去掉末尾 .0。 | 已选择常见数据库工具的读数方式。 | 需要精确大小或另行统一单位规范时重评，不约束其他页面。 |

### 2.2 Agent 遵循的既有规范

| 主题 | 出处与沿用范围 |
|---|---|
| 追踪与测试 | `docs/standards/coding.md` FSD-01–FSD-03：手写 Dart 文件使用三行文件头、实现锚点和带需求令牌的镜像测试，每条需求至少有一个非跳过测试。 |
| 分层与命名 | `docs/standards/coding.md` FSD-05–FSD-07：入口只调用 `runApp`，`app.dart` 装配依赖，模型保持纯 Dart，UI 页面与控制器归 `lib/ui/`，控制器仅依赖 foundation，项目内使用绝对导入。 |
| 错误与敏感信息 | `docs/standards/coding.md` FSD-08–FSD-09：失败使用 `AppFailure` 与集中错误码，UI 不展示 cause、密码或完整连接串。 |
| 禁止项与规模 | `docs/standards/coding.md` FSD-10、FSD-12：不使用 `dynamic`、`part`、无归属待办或未引用公共类；手写 Dart 文件不超过 250 行。 |
| 静态验证 | `docs/standards/coding.md` FSD-11：仅沿用 `dart format --output=none --set-exit-if-changed lib test`、`flutter analyze`、`flutter test` 及其通过判据；严格配置和额外 lint 按 2.1 延期。 |
| 密度与颜色 | `docs/standards/ui.md` UI-02、UI-03（除本页页头高度外）、UI-07–UI-08：沿用间距与字号 token、主题颜色 token、深浅主题与正文对比度要求；正文对比度至少 4.5:1；树键盘条款不适用。 |
| 分区与装饰 | `docs/standards/ui.md` UI-04–UI-05：用 1px 边界与底色分区，不加阴影、渐变或毛玻璃，按钮圆角为 4；本页不设置选中行。 |
| UI 截图验证 | `docs/standards/ui.md` 第 7 节：保留 1200×800、900×600 两张带区域边界标注的截图；遮挡留白后边界仍清晰，分隔线均为 1px，并按本页布局例外核对。 |

## 3. 设计

### 3.1 结构与数据流

- `lib/main.dart` 只启动组合根。`lib/app.dart` 读取编译时 `DEMO_STATE`，组装固定连接名、数据库名、schema 名、演示表记录和页面状态，再传入页面；未设置或未知值回退 `data`。默认输入为 `Local dev`、`myapp`、`public` 及六张普通表。六张表覆盖空描述、长表名、长描述、不同列数、估算行数和字节大小；演示失败为消息 `加载表失败` 与集中码表中的 `FSD-TABLE-001`。演示输入不在页面内部创建。
- `lib/domain/pg_table.dart` 用纯 Dart 保存表名、关系类型、可空描述、列数、估算行数和原始字节大小。页面从调用方接收连接名、数据库名、schema 名及互斥的页面状态：加载中、失败对象或已加载记录集合。已加载记录为空时显示空态，否则显示数据态；状态改变后不保留旧行或旧数量。
- `lib/core/errors/app_failure.dart` 提供现行规范规定的失败对象，其中消息和错误码供页面展示，cause 不进入显示文案；`lib/core/errors/failure_codes.dart` 集中定义演示错误码。页面只读取消息与错误码并按要求拼接一段中文文案，不展示驱动异常原文。
- `lib/ui/schema_tables/schema_tables_controller.dart` 只维护单列排序状态和方向，并使用调用方提供的比较依据对传入记录副本排序，不导入领域模型。默认显示表名升序；点击新列先升序、再点同列降序；默认已显示表名升序不计作一次点击，所以表名第一次被点击仍为升序。控制器依比较结果切换方向，不修改调用方数据；输入更新后由页面传入新记录与比较依据重新取得有序行。
- `lib/ui/schema_tables/schema_tables_page.dart` 从领域记录为五个可排序列提供比较依据：文本按字典序，列数与估算行数按数值，大小按原始字节数比较；描述不提供排序入口。页面四态始终保留两行页头与禁用按钮。数据态从与表体相同的有序行集合计算 `N 张表`；空态保留六列表头、只替换表体；加载与失败态替换整个表格区且隐藏数量。`lib/ui/schema_tables/widgets/schema_tables_view.dart` 接收有序行、排序状态和表头排序动作，绘制六列、完整文本与空态表体，不配置点击、悬停选中、导航或详情。
- 三个 `lib/core/theme/` 文件分别提供间距、密度和颜色 token。页面只在本页使用已确认的 56 高页头，其余适用尺寸与深浅主题沿用第 2.2 节。表格在页头以下约束可用高度，并对超宽列和多行内容提供双向滚动；不截断长文本，不分页或虚拟滚动。默认桌面入口只供应六行演示数据；替换输入与 500 行的情况由测试注入验证，不冒充桌面启动参数可提供这些数据。

### 3.2 决策

本节只落实方案确认（A）已经接受的决定，不重新选择方案。内置 Flutter 组件、两区页面、空态不附加错误码及本页 56 高页头沿用第 2.1 节的 UI-01、UI-06、UI-03 覆盖；`lib/core/theme/app_density.dart` 向本页提供已确认高度，其余工具栏仍沿用 36。严格分析器配置与额外 lint 按第 2.1 节延期，不修改 `analysis_options.yaml`。排序控制器只保存列与方向；页面提供基于领域字段的比较依据，控制器不导入领域文件。大小按 1024 进位，B 外最多一位小数并去掉末尾 `.0`。这些仅本次做法不推广至其他页面。其余适用规范按第 2.2 节执行。

### 3.3 影响文件

#### 启动入口
- 文件：`lib/main.dart`
- 操作：替换
- 职责：移除计数器模板，只启动组合根。

#### 演示输入与组合根
- 文件：`lib/app.dart`
- 操作：新建
- 职责：读取状态启动参数，装配固定演示输入、应用根及主题。

#### 表记录
- 文件：`lib/domain/pg_table.dart`
- 操作：新建
- 职责：以纯 Dart 表示外部传入的普通表记录与原始数值。

#### 失败对象
- 文件：`lib/core/errors/app_failure.dart`
- 操作：新建
- 职责：承载传入消息、错误码和不向界面展示的 cause。

#### 集中码表
- 文件：`lib/core/errors/failure_codes.dart`
- 操作：新建
- 职责：保存演示失败使用的表级错误码。

#### 主题间距
- 文件：`lib/core/theme/app_spacing.dart`
- 操作：新建
- 职责：提供界面使用的四档间距 token。

#### 主题密度
- 文件：`lib/core/theme/app_density.dart`
- 操作：新建
- 职责：提供行高、字号及本页已确认的页头高度 token。

#### 主题颜色
- 文件：`lib/core/theme/app_theme.dart`
- 操作：新建
- 职责：提供深浅主题语义色及应用根需要的主题输入。

#### 排序控制器
- 文件：`lib/ui/schema_tables/schema_tables_controller.dart`
- 操作：新建
- 职责：维护单列排序状态，对传入记录的副本排序。

#### 列表页面
- 文件：`lib/ui/schema_tables/schema_tables_page.dart`
- 操作：新建
- 职责：接收外部输入，组织页头、四态区域与数据态统计。

#### 表格区域
- 文件：`lib/ui/schema_tables/widgets/schema_tables_view.dart`
- 操作：新建
- 职责：展示六列表头、数据行或空态表体及双向滚动。

#### 移除模板测试
- 文件：`test/widget_test.dart`
- 操作：删除
- 职责：移除计数器专用冒烟测试。

#### 应用装配测试
- 文件：`test/app_test.dart`
- 操作：新建
- 职责：检查默认输入及启动状态选择规则。

#### 表记录测试
- 文件：`test/domain/pg_table_test.dart`
- 操作：新建
- 职责：检查表字段及可空描述和数值输入。

#### 排序测试
- 文件：`test/ui/schema_tables/schema_tables_controller_test.dart`
- 操作：新建
- 职责：检查比较规则、方向和调用方输入不变。

#### 页面测试
- 文件：`test/ui/schema_tables/schema_tables_page_test.dart`
- 操作：新建
- 职责：检查页头、四态、列值、统计与输入替换后的界面。

#### 表格测试
- 文件：`test/ui/schema_tables/widgets/schema_tables_view_test.dart`
- 操作：新建
- 职责：检查表头、空态表体、行交互边界、滚动与长文本。

### 3.4 边界

- 实现阶段只修改 3.3 清单内的文件。不改已批准的 `spec.md`、`grill.md`、计划第 1–2 节、`analysis_options.yaml`、`pubspec.yaml`、平台工程或规范；不添加依赖。
- 不建立数据访问层、数据库连接、网络请求、持久化、连接管理、树和详情、底栏或页面内的状态切换控件。既定的截图检查只核对第 2.2 节已确认的 UI 规范，不建立额外页面或验证系统。

## 4. 任务

- [x] **T1** 建立表输入、失败边界和主题 token
  - 改动：新建 `lib/domain/pg_table.dart`、`lib/core/errors/app_failure.dart`、`lib/core/errors/failure_codes.dart`、`lib/core/theme/app_spacing.dart`、`lib/core/theme/app_density.dart`、`lib/core/theme/app_theme.dart`、`test/domain/pg_table_test.dart` 及所需目录；记录保留原始数值，错误码集中定义，主题提供第 2.2 节适用 token。
  - 验证：运行 `flutter test test/domain/pg_table_test.dart`，不同记录值和空描述均保持原值；检查表级演示码以及间距、密度、深浅语义色符合已确认规范，本页页头高度为 56。
  - 覆盖：R3、R6、R9、R11
  - 依赖：—

- [x] **T2** 建立单列排序
  - 改动：新建 `lib/ui/schema_tables/schema_tables_controller.dart`、`test/ui/schema_tables/schema_tables_controller_test.dart`；接收待排记录与调用方给出的比较依据，对副本排序而不导入 T1 的模型或保留另一份数据源。
  - 验证：运行 `flutter test test/ui/schema_tables/schema_tables_controller_test.dart`，以测试构造的记录和比较依据检查控制器五列的方向与顺序：先升序后降序、切列回到升序、默认表名升序且首次点击表名仍升序，原输入不变；检查控制器仅导入 foundation。领域字段的字典序、数值及原始字节比较由 T3 页面接入测试验证。
  - 覆盖：R3、R8、R11
  - 依赖：T1

- [x] **T3** 建立表格和四态页面
  - 改动：新建 `lib/ui/schema_tables/schema_tables_page.dart`、`lib/ui/schema_tables/widgets/schema_tables_view.dart`、`test/ui/schema_tables/schema_tables_page_test.dart`、`test/ui/schema_tables/widgets/schema_tables_view_test.dart`；接入 T1 的输入与主题；页面从表记录提供五列比较依据给 T2 的控制器，表格使用有序行；完成页头、六列、四态和滚动。
  - 验证：运行 `flutter test test/ui/schema_tables/schema_tables_page_test.dart test/ui/schema_tables/widgets/schema_tables_view_test.dart`，替换输入后页头、列值、统计和四态正确互斥；对故意乱序且大小跨单位的表记录检查文本字典序、列数与行数的数值顺序和大小的字节顺序；空态保留表头，失败码与消息同段，点击表头更新方向，行点击/悬停无变化；在 800×600 测试视口注入 500 行和长文本，纵向到末行且横向可读完整文本，无布局溢出。
  - 覆盖：R2、R3、R4、R5、R6、R7、R8、R9、R10、R11
  - 依赖：T1、T2

- [x] **T4** 接通首屏演示并移除计数器
  - 改动：替换 `lib/main.dart`，新建 `lib/app.dart`、`test/app_test.dart`，删除 `test/widget_test.dart`；入口只启动组合根，组合根装配演示记录、错误与四态参数。
  - 验证：运行 `flutter test test/app_test.dart`，默认输入为六行表，状态选择规则对 `data`、`empty`、`loading`、`error`、未设置及未知值返回既定状态，应用根首页无计数器；确认演示记录含空描述、长表名与长描述及不同数值，旧计数器测试已删除。各编译期参数的真实启动由 T5 单独验证，不以单次测试代替。
  - 覆盖：R1、R3、R4、R5、R6、R7、R11
  - 依赖：T1、T2、T3

- [x] **T5** 人工核对静态闸门与桌面四态
  - 改动：—
  - 验证：手工：用户按下列六步操作，全部符合预期才算通过。任一步不符时，用户把实际输出或截图交给 Agent，由 Agent 在 3.3 文件范围内修复，用户再重跑该步。
    1 静态命令：在仓库根运行 `dart format --output=none --set-exit-if-changed lib test`，退出码为 0；运行 `flutter analyze`，输出 `No issues found!`；运行 `flutter test`，输出 `All tests passed!` 且没有跳过用例。
    2 默认首屏：运行 `flutter run -d windows`（macOS 用 `flutter run -d macos`），首屏直接是两行页头、禁用的 `新建连接`、六列表头、六行数据和 `6 张表`，找不到计数器和加号按钮。
    3 四态：先退出应用，再依次以 `--dart-define=DEMO_STATE=empty`、`loading`、`error`、`data` 重新启动，分别看到保留六列表头的 `该 schema 下暂无表。`、只在表格区的进度指示、`加载表失败（错误码：FSD-TABLE-001）`、六行数据；四态页头都在，前三种找不到 `张表`。
    4 交互与窄窗：点 `大小` 两次，行顺序先按字节升序再降序，方向标记从 `▲` 变为 `▼`；点 `描述` 顺序不变；悬停和点击数据行没有选中、跳转或详情；把窗口缩到 800×600，没有黄黑溢出条，横向滚动能读到完整的长表名与描述。
    5 窗格与视觉：在 1200×800 与 900×600 各留一张截图，用矩形框圈出页头与表格区边界；截图放在用户指定位置即可，不必提交进仓库，用户只需在验收反馈里给出两张图的路径与像素尺寸。核对分隔线为 1px、本页页头 56 高、按钮 4 圆角、无阴影或渐变；核对间距与行高字号 token、深浅主题八个语义色、正文对比度至少 4.5:1，UI 与应用根没有内联颜色。
    6 代码核对：按第 2.2 节适用条款逐项检查三行文件头、需求锚点与镜像测试、错误码与敏感信息、分层与绝对导入、禁用项、单文件不超过 250 行；只按第 2.1 节覆盖范围处理组件、骨架、空态和页头高度。
  - 执行者：用户
  - 覆盖：R1、R2、R3、R4、R5、R6、R7、R8、R9、R10、R11
  - 依赖：T1、T2、T3、T4

## 5. R → 验证

本节自动命令和桌面步骤均留待实现完成后执行，最终由用户在 T5 逐项核对；编写计划不等于检查已通过。桌面入口为在仓库根运行 `flutter run -d windows`，macOS 改用 `flutter run -d macos`；运行前确认目标 Flutter 桌面设备可用，不启动 PostgreSQL，必要时断开网络。变更 `--dart-define=DEMO_STATE=<状态>` 后先退出应用再重新启动。桌面默认入口只有六行演示数据；替换输入及 500 行用 widget 测试构造，不将测试夹具当成桌面入口。

#### R1 启动首屏
- R：R1
- 任务：T4、T5
- 自动验证：运行 `flutter test test/app_test.dart`，首页即页头与表格，找不到计数器按钮和文案；检查 `lib/main.dart` 不再有模板页，`test/widget_test.dart` 已删除，套件没有计数器冒烟测试。
- 手工步骤：默认桌面入口不传 define，首屏可见连接名、schema 和表格，无加号计数按钮，也不必导航。

#### R2 页头
- R：R2
- 任务：T3、T5
- 自动验证：运行 `flutter test test/ui/schema_tables/schema_tables_page_test.dart`，注入另一组连接名、数据库名和 schema 名，核对两行文字变化、按钮禁用且触发点击后无界面变化；核对页头不显示主机、端口、用户名或密码，四态均保留页头。
- 手工步骤：默认桌面入口查看 `Local dev · myapp`、`public` 与右侧禁用的 `新建连接`；尝试点击后没有弹窗或路由变化，页头不显示敏感连接字段。非默认输入由上述测试注入。

#### R3 表格数据
- R：R3
- 任务：T1、T2、T3、T4、T5
- 自动验证：运行 `flutter test test/domain/pg_table_test.dart test/ui/schema_tables/schema_tables_page_test.dart test/ui/schema_tables/widgets/schema_tables_view_test.dart test/app_test.dart`，用不同 N 的记录核对六列与 N 行、各字段随输入变化、空描述为 `—`、类型取传入值；按已确认 1024 进位规则核对 B/KB/MB/GB 格式，默认六行包含长文本及不同数值。
- 手工步骤：默认桌面入口核对六列六行、空描述 `—`、类型 `Table` 与大小单位；长表名和描述按 R9 的步骤滚动查看。替换数据仅由上述测试验证。

#### R4 空态
- R：R4
- 任务：T3、T4、T5
- 自动验证：运行 `flutter test test/ui/schema_tables/schema_tables_page_test.dart test/app_test.dart`，空列表下六列表头保留，提示在表体，不显示数据行或数量，页头仍在。
- 手工步骤：运行 `flutter run -d windows --dart-define=DEMO_STATE=empty`（macOS 改 `-d macos`），看到表体 `该 schema 下暂无表。`、六列表头与页头；没有 `0 张表` 或数据行。

#### R5 加载态
- R：R5
- 任务：T3、T4、T5
- 自动验证：运行 `flutter test test/ui/schema_tables/schema_tables_page_test.dart test/app_test.dart`，进度指示只在表格区，表头、旧行和数量不可见，页头仍在。
- 手工步骤：运行 `flutter run -d windows --dart-define=DEMO_STATE=loading`（macOS 改 `-d macos`），页头不变，表格区出现进度指示而不见表格和数量。

#### R6 失败态
- R：R6
- 任务：T1、T3、T4、T5
- 自动验证：运行 `flutter test test/ui/schema_tables/schema_tables_page_test.dart test/app_test.dart`，注入不同消息和码以及含敏感原文的 cause，核对完整中文全角括号格式与 `错误码：` 同段、cause 不出现、表格及数量不出现；演示对象的消息和集中码生成 `加载表失败（错误码：FSD-TABLE-001）`。
- 手工步骤：运行 `flutter run -d windows --dart-define=DEMO_STATE=error`（macOS 改 `-d macos`），表格区显示 `加载表失败（错误码：FSD-TABLE-001）`，页头仍在；无表格、数量、异常原文、密码或完整连接串。

#### R7 数量统计
- R：R7
- 任务：T3、T4、T5
- 自动验证：运行 `flutter test test/ui/schema_tables/schema_tables_page_test.dart test/app_test.dart`，不同非空输入的 `N 张表` 与实际渲染行数相同，空、加载及失败态均找不到 `张表`。
- 手工步骤：默认桌面入口核对六行与 `6 张表`；再按 R4–R6 的命令逐态重启，三态均没有数量。

#### R8 排序
- R：R8
- 任务：T2、T3、T5
- 自动验证：运行 `flutter test test/ui/schema_tables/schema_tables_controller_test.dart test/ui/schema_tables/schema_tables_page_test.dart`，控制器测试以测试记录和比较依据核对五列首次点击升序、再点降序、换列重置及输入不变；页面测试用故意乱序、显示大小文字顺序与字节顺序不同的领域记录核对文本字典序、数值和原始字节比较；默认表名升序且首次点击表名仍升序，只在当前列显示 `▲`/`▼`，描述无排序动作。
- 手工步骤：默认桌面入口先核对表名升序；点击 `大小` 两次，行顺序先按字节升序再降序，方向标记从 `▲` 变为 `▼`；点击 `描述` 不改变排序。

#### R9 滚动与长文本
- R：R9
- 任务：T1、T3、T5
- 自动验证：运行 `flutter test test/ui/schema_tables/widgets/schema_tables_view_test.dart test/ui/schema_tables/schema_tables_page_test.dart`，在 800×600 测试视口注入 500 行和长表名、长描述，核对没有布局异常或省略截断，纵向可抵末行、横向可读完整文本与右侧列，所有行而非仅可视行参与渲染，不出现分页控件。
- 手工步骤：默认六行演示数据中已备长表名与长描述；将桌面窗口调整为 800×600，横向滚动并读取完整长文本及右侧列，确认无黄黑溢出条。500 行末行用上述测试验证。另在 1200×800 与 900×600 按第 2.2 节既定 UI 截图要求核对区域边界、1px 分隔线与密度，并保留两张带边界标注的截图。

#### R10 行不交互
- R：R10
- 任务：T3、T5
- 自动验证：运行 `flutter test test/ui/schema_tables/widgets/schema_tables_view_test.dart test/ui/schema_tables/schema_tables_page_test.dart`，点击与悬停数据行后没有选中态、数据变化、导航或详情。
- 手工步骤：默认桌面入口悬停并点击任一数据行，界面、路由和数据不变，没有选中标记或详情面板。

#### R11 外部输入和脱网演示
- R：R11
- 任务：T1、T2、T3、T4、T5
- 自动验证：运行 `flutter test test/app_test.dart test/ui/schema_tables/schema_tables_page_test.dart` 核对状态选择映射（含未设置/未知值回退）和替换连接、schema、表记录、页面状态后的输出；检查 `lib/app.dart` 到页面的输入路径、UI 无 PostgreSQL 驱动导入、`pubspec.yaml` 不增数据库依赖，且本次代码无数据库读写或网络请求调用。这些测试和代码检查只支持已检查的输入及依赖边界，不声称已审计进程全部流量。
- 手工步骤：在 Windows 或 macOS 的无 PostgreSQL、可断网环境中，分别使用默认入口、`flutter run -d windows --dart-define=DEMO_STATE=data` 及 R4–R6 的三个命令启动（macOS 改 `-d macos`）；每次退出后重新运行，依次看到六行数据、六行数据、保留表头的空态、进度指示与规定错误文案，四态都无需数据库。替换输入由自动测试完成；未知值回退由状态选择测试核对。

## 6. 风险与回滚

#### 长表格在窄窗口出现溢出
- 风险：500 行全量构建与双向滚动叠加，使末行到不了或长文本被裁剪。
- 触发信号：800×600 测试或桌面检查出现布局异常、末行不可到达、横向无法读全或文本被省略。
- 应对：Agent 仅在 3.3 的页面、表格视图及相应测试内调整约束和滚动，重复 R9 检查；若必须改为分页、虚拟滚动或改变已接受的代价，停止交用户决定。整体撤回时先确认可取回原 `lib/main.dart` 与 `test/widget_test.dart` 内容，再移除 3.3 新建文件并恢复这两个原文件；保留需求、已确认方案及未改动配置，不误删用户其他改动。

#### 状态与错误信息错位
- 风险：状态或外部记录更新后仍显示旧行、旧数量，或者失败 cause 与连接敏感字段进入页面。
- 触发信号：替换输入测试、四态桌面核对发现残留行/数量、失败文案缺错误码或出现异常原文；默认/未知参数回退错误。
- 应对：Agent 只在 3.3 的演示装配、页面、控制器与对应测试内核对数据流并修复，复跑受影响的 T2–T4 检查；T5 由用户按原六步重跑，Agent 不自行判定 T5 通过。若必须引入数据库、调试入口或改变需求/已确认方案，停止交用户决定。撤回同上，恢复原入口与原计数器测试，删除本次新建文件，保留未改的配置与平台文件。

#### 规范例外和桌面环境无法核实
- 风险：实现误用 UI 覆盖范围、漏掉仍适用的主题/分析闸门，或桌面设备不可用导致人工验收无法进行。
- 触发信号：三条静态命令、主题核对、边界截图未达预期，或找不到可运行的 Windows/macOS 桌面设备。
- 应对：Agent 只修复 3.3 允许范围内的问题并重新检查；设备不可用或修复要求扩大文件范围、修改已批准上游时停止并报告未验证项目。撤回前核实两份原模板文件可取回；若不能取回，停止并报告未恢复状态，不假称已回到实施前；其他产物按前述整体撤回边界处理。

**对证**：开工确认（B）本轮已进行 3/3 次独立核查、正文修订 3 轮（前 2 轮在上限内，第 3 轮经用户明确追加）。首次完整核查 V1–V8：阻塞 0、一般问题 1（Q1：控制器受导入限制时缺少排序输入协作约定）、轻微问题 0。第二次仅定向复核 Q1 与 3.1、3.2、T2、T3、R8 验证及风险的连带影响：Q1 已修正并通过，新增问题 0；遗留阻塞 0、一般问题 0、轻微问题 0。第三次按用户要求把第 4 节 T5 改为由用户执行的人工检查、并同步第 5 节前言后定向复核 V6–V8 及连带影响：T1–T4 仍承接 3.3 全部文件，T5 的「改动」为「—」与 3.3、3.4、依赖和撤回办法一致，未新增功能或验收；遗留阻塞 0、一般问题 0、轻微问题 2（Q2：第 6 节风险应对仍写「复跑 T2–T5」，与 T5 改由用户执行不一致；Q3：T5 第 5 步未写明截图存放位置与标注方式），按轮次上限未在正文修改；用户随后明确要求直接修正这两处，遂追加 1 轮修订：Q2 改为「复跑受影响的 T2–T4 检查，T5 由用户按原六步重跑，Agent 不自行判定 T5 通过」，Q3 改为「用矩形框圈出页头与表格区边界，截图放在用户指定位置、不必提交进仓库，路径与像素尺寸在验收反馈中给出」。两处均为轻微问题，不再开启独立核查。核查后补 T5 验证首行的「手工：」标记以满足 lint 格式要求，六步内容未变。修订后 lint 11 项通过。项目构建、测试与桌面验收未运行，留待实现阶段。
