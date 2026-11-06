// spec: p00-001, p00-007
// layer: test
// covers: p00-001/R2, p00-001/R4, p00-001/R5, p00-001/R6, p00-001/R7, p00-001/R8, p00-001/R11, p00-007/R1, p00-007/R4

import 'package:flutter_sdd/core/errors/app_failure.dart';
import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_sdd/ui/schema_tables/schema_tables_page.dart';
import 'package:flutter_sdd/ui/schema_tables/widgets/schema_tables_view.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shadcn_flutter/shadcn_flutter.dart';

import '../../support/schema_tables_harness.dart';

void main() {
  testWidgets('[p00-001/R2] 页头显示连接名、数据库名与 schema 名，按钮禁用且无敏感字段', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      wrapInApp(
        schemaTablesPage(
          connectionName: 'Staging',
          databaseName: 'analytics',
          schemaName: 'reporting',
        ),
      ),
    );

    expect(find.text('Staging · analytics'), findsOneWidget);
    expect(find.text('reporting'), findsOneWidget);

    final Button button = tester.widget<Button>(
      find.widgetWithText(Button, '新建连接'),
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
      wrapInApp(schemaTablesPage(state: const SchemaTablesLoaded(<PgTable>[]))),
    );

    expect(find.text('Local dev · myapp'), findsOneWidget);
    expect(find.text('public'), findsOneWidget);
    expect(find.text('新建连接'), findsOneWidget);
    for (final String label in <String>['表名', '类型', '描述', '列数', '估算行数', '大小']) {
      expect(find.textContaining(label), findsOneWidget);
    }
    expect(find.text(SchemaTablesView.emptyMessage), findsOneWidget);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R5] 加载中只在表格区显示进度指示', (WidgetTester tester) async {
    await tester.pumpWidget(
      wrapInApp(schemaTablesPage(state: const SchemaTablesLoading())),
    );
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
      wrapInApp(schemaTablesPage(state: const SchemaTablesFailed(failure))),
    );

    expect(find.text('加载表失败（错误码：FSD-TABLE-001）'), findsOneWidget);
    expect(find.textContaining('password'), findsNothing);
    expect(find.textContaining('SocketException'), findsNothing);
    expect(find.textContaining('表名'), findsNothing);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R7] 数量统计等于实际渲染的行数', (WidgetTester tester) async {
    await tester.pumpWidget(wrapInApp(schemaTablesPage()));
    expect(find.text('3 张表'), findsOneWidget);

    await tester.pumpWidget(
      wrapInApp(schemaTablesPage(state: const SchemaTablesLoaded(<PgTable>[]))),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R8] 五列按字典序、数值与原始字节排序，描述不可排序', (
    WidgetTester tester,
  ) async {
    useViewSize(tester, const Size(1200, 800));
    await tester.pumpWidget(wrapInApp(schemaTablesPage()));
    await tester.pumpAndSettle();

    expect(find.textContaining('表名 ▲'), findsOneWidget);
    expectRowOrder(tester, <String>['alpha', 'bravo', 'delta']);

    for (final (String label, List<String> order) in <(String, List<String>)>[
      ('类型', <String>['delta', 'bravo', 'alpha']),
      ('列数', <String>['delta', 'alpha', 'bravo']),
      ('估算行数', <String>['bravo', 'alpha', 'delta']),
      ('大小', <String>['bravo', 'delta', 'alpha']),
    ]) {
      await tester.tap(find.textContaining(label));
      await tester.pumpAndSettle();
      expect(find.textContaining('$label ▲'), findsOneWidget);
      expectRowOrder(tester, order);
    }

    // 大小按原始字节比较：显示文字的升序是 40 KB、5 MB、900 B，与字节升序不同。
    expect(find.text('40 KB'), findsOneWidget);
    expect(find.text('5 MB'), findsOneWidget);
    expect(find.text('900 B'), findsOneWidget);
    await tester.tap(find.textContaining('大小'));
    await tester.pumpAndSettle();
    expect(find.textContaining('大小 ▼'), findsOneWidget);
    expectRowOrder(tester, <String>['alpha', 'delta', 'bravo']);

    expect(
      find.ancestor(of: find.text('描述'), matching: find.byType(Button)),
      findsNothing,
    );
    await tester.tap(find.text('描述'));
    await tester.pumpAndSettle();
    expect(find.textContaining('大小 ▼'), findsOneWidget);
    expectRowOrder(tester, <String>['alpha', 'delta', 'bravo']);
  });

  testWidgets('[p00-001/R11] 替换连接信息与表记录后页面随之更新', (WidgetTester tester) async {
    await tester.pumpWidget(wrapInApp(schemaTablesPage()));
    expect(find.text('Local dev · myapp'), findsOneWidget);
    expect(find.text('3 张表'), findsOneWidget);

    await tester.pumpWidget(
      wrapInApp(
        schemaTablesPage(
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
    useViewSize(tester, const Size(800, 600));
    await tester.pumpWidget(wrapInApp(schemaTablesPage()));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('3 张表'), findsOneWidget);
  });

  testWidgets('[p00-007/R1] 页头按钮与加载指示来自 shadcn_flutter，页面没有主题开关', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(wrapInApp(schemaTablesPage()));
    await tester.pumpAndSettle();
    expect(find.widgetWithText(Button, '新建连接'), findsOneWidget);
    expect(find.text('新建连接'), findsOneWidget);

    await tester.pumpWidget(
      wrapInApp(schemaTablesPage(state: const SchemaTablesLoading())),
    );
    await tester.pump();
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    expect(find.byType(Switch), findsNothing);
    expect(find.textContaining('主题'), findsNothing);
  });

  testWidgets('[p00-007/R4] 系统模式变化只换外观，排序方向与横向滚动位置保持', (
    WidgetTester tester,
  ) async {
    useViewSize(tester, const Size(800, 600));
    addTearDown(tester.platformDispatcher.clearPlatformBrightnessTestValue);
    await tester.pumpWidget(wrapInApp(schemaTablesPage()));
    await tester.pumpAndSettle();

    await tester.tap(find.textContaining('列数'));
    await tester.pumpAndSettle();
    expect(find.textContaining('列数 ▲'), findsOneWidget);
    expectRowOrder(tester, <String>['delta', 'alpha', 'bravo']);

    await tester.drag(find.byType(SchemaTablesView), const Offset(-80, 0));
    await tester.pumpAndSettle();
    final double offset = horizontalPosition(tester).pixels;
    expect(offset, greaterThan(0));

    await setSystemBrightness(tester, Brightness.dark);

    expect(find.textContaining('列数 ▲'), findsOneWidget);
    expectRowOrder(tester, <String>['delta', 'alpha', 'bravo']);
    expect(horizontalPosition(tester).pixels, offset);
    expect(find.text('3 张表'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
