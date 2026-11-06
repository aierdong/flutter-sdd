// spec: support
// layer: test
// covers: none

import 'package:flutter_sdd/core/theme/app_theme.dart';
import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_sdd/ui/schema_tables/schema_tables_page.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shadcn_flutter/shadcn_flutter.dart';

/// 故意乱序的表记录：类型、列数、估算行数与大小都不随表名递增，大小为跨单位取值。
const List<PgTable> sampleTables = <PgTable>[
  PgTable(
    name: 'alpha',
    relationKind: 'View',
    description: '第一条记录',
    columnCount: 3,
    estimatedRows: 200,
    sizeBytes: 5242880,
  ),
  PgTable(
    name: 'bravo',
    relationKind: 'Table',
    description: '第二条记录',
    columnCount: 5,
    estimatedRows: 10,
    sizeBytes: 900,
  ),
  PgTable(
    name: 'delta',
    relationKind: 'Partitioned table',
    description: '第三条记录',
    columnCount: 1,
    estimatedRows: 3000,
    sizeBytes: 40960,
  ),
];

/// 用 shadcn 应用根承载被测组件，浅色、深色主题都交给它按系统模式选择。
Widget wrapInApp(Widget child) {
  return ShadcnApp(
    theme: AppTheme.light(),
    darkTheme: AppTheme.dark(),
    themeMode: ThemeMode.system,
    home: child,
  );
}

/// 构造单 schema 表列表页，未指定的连接信息与状态用演示值。
Widget schemaTablesPage({
  String connectionName = 'Local dev',
  String databaseName = 'myapp',
  String schemaName = 'public',
  SchemaTablesState state = const SchemaTablesLoaded(sampleTables),
}) {
  return SchemaTablesPage(
    connectionName: connectionName,
    databaseName: databaseName,
    schemaName: schemaName,
    state: state,
  );
}

/// 固定测试窗口尺寸。
void useViewSize(WidgetTester tester, Size size) {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

/// 模拟系统浅色、深色模式；应用运行中可直接切换。
Future<void> setSystemBrightness(
  WidgetTester tester,
  Brightness brightness,
) async {
  tester.platformDispatcher.platformBrightnessTestValue = brightness;
  await tester.pumpAndSettle();
}

/// 按从上到下的顺序核对数据行。
void expectRowOrder(WidgetTester tester, List<String> names) {
  for (int index = 0; index < names.length - 1; index += 1) {
    expect(
      tester.getTopLeft(find.text(names[index])).dy,
      lessThan(tester.getTopLeft(find.text(names[index + 1])).dy),
    );
  }
}

/// 表格内部由 shadcn_flutter 的二维滚动容器承载，横纵方向各有一个控制器。
TwoDimensionalScrollable tableScrollable(WidgetTester tester) {
  return tester.widget<TwoDimensionalScrollable>(
    find.byType(TwoDimensionalScrollable),
  );
}

/// 表格当前横向滚动位置。
ScrollPosition horizontalPosition(WidgetTester tester) {
  return tableScrollable(tester).horizontalDetails.controller!.position;
}

/// 表格当前纵向滚动位置。
ScrollPosition verticalPosition(WidgetTester tester) {
  return tableScrollable(tester).verticalDetails.controller!.position;
}
