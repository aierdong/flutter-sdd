// spec: p00-001
// layer: test
// covers: p00-001/R2, p00-001/R4, p00-001/R5, p00-001/R6, p00-001/R7, p00-001/R8, p00-001/R11

import 'package:flutter/material.dart';
import 'package:flutter_sdd/core/errors/app_failure.dart';
import 'package:flutter_sdd/core/theme/app_theme.dart';
import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_sdd/ui/schema_tables/schema_tables_page.dart';
import 'package:flutter_test/flutter_test.dart';

/// 故意乱序的输入：类型、列数、估算行数与大小都不随表名递增，大小为跨单位取值。
const List<PgTable> _rows = <PgTable>[
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

Widget _wrap(Widget page) {
  return MaterialApp(theme: AppTheme.light(), home: page);
}

Widget _page({
  String connectionName = 'Local dev',
  String databaseName = 'myapp',
  String schemaName = 'public',
  SchemaTablesState state = const SchemaTablesLoaded(_rows),
}) {
  return SchemaTablesPage(
    connectionName: connectionName,
    databaseName: databaseName,
    schemaName: schemaName,
    state: state,
  );
}

/// 桌面窗口尺寸，用于需要点中右侧列的交互检查。
void _useDesktopView(WidgetTester tester) {
  tester.view.physicalSize = const Size(1200, 800);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

/// 按从上到下的顺序核对数据行。
void _expectRowOrder(WidgetTester tester, List<String> names) {
  for (var index = 0; index < names.length - 1; index += 1) {
    expect(
      tester.getTopLeft(find.text(names[index])).dy,
      lessThan(tester.getTopLeft(find.text(names[index + 1])).dy),
    );
  }
}

void main() {
  testWidgets('[p00-001/R2] 页头显示连接名、数据库名与 schema 名，按钮禁用且无敏感字段', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      _wrap(
        _page(
          connectionName: 'Staging',
          databaseName: 'analytics',
          schemaName: 'reporting',
        ),
      ),
    );

    expect(find.text('Staging · analytics'), findsOneWidget);
    expect(find.text('reporting'), findsOneWidget);

    final OutlinedButton button = tester.widget<OutlinedButton>(
      find.widgetWithText(OutlinedButton, '新建连接'),
    );
    expect(button.onPressed, isNull);

    await tester.tap(find.text('新建连接'));
    await tester.pumpAndSettle();
    expect(find.text('Staging · analytics'), findsOneWidget);
    expect(find.byType(AlertDialog), findsNothing);

    expect(find.textContaining(':5432'), findsNothing);
    expect(find.textContaining('password'), findsNothing);
    expect(find.textContaining('postgres'), findsNothing);
  });

  testWidgets('[p00-001/R4] 空列表保留页头与六列表头，且不显示数量统计', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      _wrap(_page(state: const SchemaTablesLoaded(<PgTable>[]))),
    );

    expect(find.text('Local dev · myapp'), findsOneWidget);
    expect(find.text('public'), findsOneWidget);
    expect(find.text('新建连接'), findsOneWidget);
    for (final String label in <String>['表名', '类型', '描述', '列数', '估算行数', '大小']) {
      expect(find.textContaining(label), findsOneWidget);
    }
    expect(find.text('该 schema 下暂无表。'), findsOneWidget);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R5] 加载中只在表格区显示进度指示', (WidgetTester tester) async {
    await tester.pumpWidget(_wrap(_page(state: const SchemaTablesLoading())));
    await tester.pump();

    expect(find.text('Local dev · myapp'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.textContaining('表名'), findsNothing);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R6] 失败文案把消息与错误码放在同一段，且不泄露 cause', (
    WidgetTester tester,
  ) async {
    const AppFailure failure = AppFailure(
      code: 'FSD-TABLE-001',
      message: '加载表失败',
      cause: 'SocketException: password=secret@localhost:5432',
    );
    await tester.pumpWidget(
      _wrap(_page(state: const SchemaTablesFailed(failure))),
    );

    expect(find.text('加载表失败（错误码：FSD-TABLE-001）'), findsOneWidget);
    expect(find.textContaining('password'), findsNothing);
    expect(find.textContaining('SocketException'), findsNothing);
    expect(find.textContaining('表名'), findsNothing);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R7] 数量统计等于实际渲染的行数', (WidgetTester tester) async {
    await tester.pumpWidget(_wrap(_page()));
    expect(find.text('3 张表'), findsOneWidget);

    await tester.pumpWidget(
      _wrap(_page(state: const SchemaTablesLoaded(<PgTable>[]))),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R8] 五列按字典序、数值与原始字节排序，描述不可排序', (
    WidgetTester tester,
  ) async {
    _useDesktopView(tester);
    await tester.pumpWidget(_wrap(_page()));
    await tester.pumpAndSettle();

    expect(find.textContaining('表名 ▲'), findsOneWidget);
    _expectRowOrder(tester, <String>['alpha', 'bravo', 'delta']);

    for (final (String label, List<String> order) in <(String, List<String>)>[
      ('类型', <String>['delta', 'bravo', 'alpha']),
      ('列数', <String>['delta', 'alpha', 'bravo']),
      ('估算行数', <String>['bravo', 'alpha', 'delta']),
      ('大小', <String>['bravo', 'delta', 'alpha']),
    ]) {
      await tester.tap(find.textContaining(label));
      await tester.pumpAndSettle();
      expect(find.textContaining('$label ▲'), findsOneWidget);
      _expectRowOrder(tester, order);
    }

    // 大小按原始字节比较：显示文字的升序是 40 KB、5 MB、900 B，与字节升序不同。
    expect(find.text('40 KB'), findsOneWidget);
    expect(find.text('5 MB'), findsOneWidget);
    expect(find.text('900 B'), findsOneWidget);
    await tester.tap(find.textContaining('大小'));
    await tester.pumpAndSettle();
    expect(find.textContaining('大小 ▼'), findsOneWidget);
    _expectRowOrder(tester, <String>['alpha', 'delta', 'bravo']);

    expect(
      find.ancestor(of: find.text('描述'), matching: find.byType(InkWell)),
      findsNothing,
    );
    await tester.tap(find.text('描述'));
    await tester.pumpAndSettle();
    expect(find.textContaining('大小 ▼'), findsOneWidget);
    _expectRowOrder(tester, <String>['alpha', 'delta', 'bravo']);
  });

  testWidgets('[p00-001/R11] 替换连接信息与表记录后页面随之更新', (WidgetTester tester) async {
    await tester.pumpWidget(_wrap(_page()));
    expect(find.text('Local dev · myapp'), findsOneWidget);
    expect(find.text('3 张表'), findsOneWidget);

    await tester.pumpWidget(
      _wrap(
        _page(
          connectionName: 'Prod',
          databaseName: 'warehouse',
          schemaName: 'sales',
          state: const SchemaTablesLoaded(<PgTable>[
            PgTable(
              name: 'orders',
              relationKind: 'Table',
              columnCount: 4,
              estimatedRows: 5,
              sizeBytes: 2048,
            ),
          ]),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Prod · warehouse'), findsOneWidget);
    expect(find.text('sales'), findsOneWidget);
    expect(find.text('1 张表'), findsOneWidget);
    expect(find.text('orders'), findsOneWidget);
    expect(find.text('alpha'), findsNothing);
  });

  testWidgets('[p00-001/R11] 800×600 视口下页面无布局溢出', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(800, 600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(_wrap(_page()));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('3 张表'), findsOneWidget);
  });
}
