// spec: p00-001
// layer: test
// covers: p00-001/R3, p00-001/R4, p00-001/R9, p00-001/R10

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_sdd/core/theme/app_theme.dart';
import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_sdd/ui/schema_tables/schema_tables_controller.dart';
import 'package:flutter_sdd/ui/schema_tables/widgets/schema_tables_view.dart';
import 'package:flutter_test/flutter_test.dart';

const List<PgTable> _rows = <PgTable>[
  PgTable(
    name: 'customers',
    relationKind: 'Table',
    description: '客户主数据',
    columnCount: 9,
    estimatedRows: 8210,
    sizeBytes: 3407872,
  ),
  PgTable(
    name: 'invoices',
    relationKind: 'Table',
    columnCount: 12,
    estimatedRows: 152300,
    sizeBytes: 44040192,
  ),
  PgTable(
    name: 'sessions',
    relationKind: 'Table',
    description: '   ',
    columnCount: 6,
    estimatedRows: 41200,
    sizeBytes: 65536,
  ),
];

List<PgTable> _manyRows() {
  return List<PgTable>.generate(
    500,
    (int index) => PgTable(
      name: 'table_${index.toString().padLeft(3, '0')}_with_a_long_name',
      relationKind: 'Table',
      description: '第 $index 行的长描述，用来验证换行与横向滚动都不会截断文本内容',
      columnCount: index,
      estimatedRows: index * 1000,
      sizeBytes: index * 1024 * 1024,
    ),
  );
}

Widget _host(Widget child) {
  return MaterialApp(
    theme: AppTheme.light(),
    home: Material(child: child),
  );
}

Widget _view(List<PgTable> rows) {
  return SchemaTablesView(
    rows: rows,
    sortColumn: SchemaSortColumn.name,
    ascending: true,
    onSort: (SchemaSortColumn column) {},
  );
}

ScrollableState _scrollableOf(WidgetTester tester, Key key) {
  return tester.state<ScrollableState>(
    find
        .descendant(of: find.byKey(key), matching: find.byType(Scrollable))
        .first,
  );
}

void main() {
  test('[p00-001/R3] 字节大小按 1024 进位换算为人类可读单位', () {
    expect(formatByteSize(0), '0 B');
    expect(formatByteSize(512), '512 B');
    expect(formatByteSize(1024), '1 KB');
    expect(formatByteSize(1536), '1.5 KB');
    expect(formatByteSize(1048576), '1 MB');
    expect(formatByteSize(44040192), '42 MB');
    expect(formatByteSize(268435456), '256 MB');
    expect(formatByteSize(5265334272), '4.9 GB');
  });

  testWidgets('[p00-001/R3] 六列表头与每行取值来自传入记录', (WidgetTester tester) async {
    await tester.pumpWidget(_host(_view(_rows)));

    for (final String label in <String>['表名', '类型', '描述', '列数', '估算行数', '大小']) {
      expect(find.textContaining(label), findsOneWidget);
    }

    expect(find.text('customers'), findsOneWidget);
    expect(find.text('invoices'), findsOneWidget);
    expect(find.text('sessions'), findsOneWidget);
    expect(find.text('Table'), findsNWidgets(3));
    expect(find.text('客户主数据'), findsOneWidget);
    expect(find.text('—'), findsNWidgets(2));
    expect(find.text('9'), findsOneWidget);
    expect(find.text('8210'), findsOneWidget);
    expect(find.text('3.3 MB'), findsOneWidget);
    expect(find.text('42 MB'), findsOneWidget);
  });

  testWidgets('[p00-001/R4] 无表时保留六列表头，只在表体显示空态提示', (WidgetTester tester) async {
    await tester.pumpWidget(_host(_view(const <PgTable>[])));

    for (final String label in <String>['表名', '类型', '描述', '列数', '估算行数', '大小']) {
      expect(find.textContaining(label), findsOneWidget);
    }
    expect(find.text(SchemaTablesView.emptyMessage), findsOneWidget);
    expect(find.byKey(SchemaTablesView.verticalScrollKey), findsNothing);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R9] 800×600 下 500 行可双向滚动且长文本不截断', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(800, 600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(_host(_view(_manyRows())));
    expect(tester.takeException(), isNull);

    // 长文本按单元格宽度换行，没有省略或裁剪设置，渲染高度超过单行。
    final Finder longName = find.text('table_000_with_a_long_name');
    final Text longNameText = tester.widget<Text>(longName);
    expect(longNameText.maxLines, isNull);
    expect(longNameText.overflow, isNull);
    final Finder longDescription = find.text('第 0 行的长描述，用来验证换行与横向滚动都不会截断文本内容');
    expect(
      tester.getSize(longDescription).height,
      greaterThan(tester.getSize(find.text('0').first).height),
    );

    final ScrollableState horizontal = _scrollableOf(
      tester,
      SchemaTablesView.horizontalScrollKey,
    );
    final ScrollableState vertical = _scrollableOf(
      tester,
      SchemaTablesView.verticalScrollKey,
    );
    expect(horizontal.position.maxScrollExtent, greaterThan(0));
    expect(vertical.position.maxScrollExtent, greaterThan(0));

    // 横向滚到最右，最右列完整可读，左侧长表名仍在原位。
    await tester.drag(
      find.byKey(SchemaTablesView.horizontalScrollKey),
      const Offset(-2000, 0),
    );
    await tester.pumpAndSettle();
    expect(
      horizontal.position.pixels,
      closeTo(horizontal.position.maxScrollExtent, 1),
    );
    final Rect lastSizeCell = tester.getRect(
      find.text(formatByteSize(499 * 1024 * 1024)),
    );
    expect(lastSizeCell.left, greaterThanOrEqualTo(0));
    expect(lastSizeCell.right, lessThanOrEqualTo(800));
    expect(longName, findsOneWidget);

    final Finder lastRow = find.text('table_499_with_a_long_name');
    expect(lastRow, findsOneWidget);

    await tester.drag(
      find.byKey(SchemaTablesView.verticalScrollKey),
      const Offset(0, -30000),
    );
    await tester.pumpAndSettle();
    expect(
      vertical.position.pixels,
      closeTo(vertical.position.maxScrollExtent, 1),
    );
    expect(tester.getBottomLeft(lastRow).dy, lessThanOrEqualTo(600));
    expect(tester.takeException(), isNull);
  });

  testWidgets('[p00-001/R10] 数据行不挂点击或悬停交互', (WidgetTester tester) async {
    await tester.pumpWidget(_host(_view(_rows)));

    expect(
      find.ancestor(of: find.text('customers'), matching: find.byType(InkWell)),
      findsNothing,
    );

    await tester.tap(find.text('customers'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('customers'), findsOneWidget);
    expect(find.text('invoices'), findsOneWidget);
  });

  testWidgets('[p00-001/R10] 悬停数据行不产生选中、导航或详情', (WidgetTester tester) async {
    await tester.pumpWidget(_host(_view(_rows)));
    final Rect before = tester.getRect(find.text('customers'));

    final TestGesture mouse = await tester.createGesture(
      kind: PointerDeviceKind.mouse,
    );
    addTearDown(mouse.removePointer);
    await mouse.addPointer(location: Offset.zero);

    final Offset rowCenter = tester.getCenter(find.text('customers'));
    for (final Offset point in <Offset>[
      rowCenter,
      rowCenter + const Offset(-60, 0),
      rowCenter + const Offset(60, 0),
    ]) {
      await mouse.moveTo(point);
      await tester.pumpAndSettle();
      expect(
        find.ancestor(
          of: find.text('customers'),
          matching: find.byType(InkWell),
        ),
        findsNothing,
      );
      expect(tester.takeException(), isNull);
    }

    expect(tester.getRect(find.text('customers')), before);
    expect(find.text('customers'), findsOneWidget);
    expect(find.text('invoices'), findsOneWidget);
    expect(find.text('客户主数据'), findsOneWidget);
    expect(find.text('sessions'), findsOneWidget);
  });
}
