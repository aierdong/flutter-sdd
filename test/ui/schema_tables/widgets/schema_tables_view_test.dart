// spec: p00-001, p00-007
// layer: test
// covers: p00-001/R3, p00-001/R4, p00-001/R9, p00-001/R10, p00-007/R2, p00-007/R4

import 'package:flutter/gestures.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_sdd/ui/schema_tables/schema_tables_controller.dart';
import 'package:flutter_sdd/ui/schema_tables/widgets/schema_tables_view.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shadcn_flutter/shadcn_flutter.dart';

import '../../../support/schema_tables_harness.dart';

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

const String _longName = 'table_000_with_a_long_name';
const String _longDescription = '第 0 行的长描述，用来验证换行与横向滚动都不会截断文本内容';

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

Widget _view(List<PgTable> rows) {
  return SchemaTablesView(
    rows: rows,
    sortColumn: SchemaSortColumn.name,
    ascending: true,
    onSort: (SchemaSortColumn column) {},
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

  testWidgets('[p00-007/R2] 表格由 shadcn_flutter 的 Table 绘制并保留原生行悬停', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(wrapInApp(_view(_rows)));

    expect(find.byType(Table), findsOneWidget);
    final List<TableRow> rows = tester.widget<Table>(find.byType(Table)).rows!;
    expect(rows.first, isA<TableHeader>());
    for (final TableRow row in rows.skip(1)) {
      for (final TableCell cell in row.cells) {
        expect(cell.rowHover, isTrue);
      }
    }
  });

  testWidgets('[p00-001/R3] 六列表头与每行取值来自传入记录', (WidgetTester tester) async {
    await tester.pumpWidget(wrapInApp(_view(_rows)));

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
    await tester.pumpWidget(wrapInApp(_view(const <PgTable>[])));

    for (final String label in <String>['表名', '类型', '描述', '列数', '估算行数', '大小']) {
      expect(find.textContaining(label), findsOneWidget);
    }
    expect(find.text(SchemaTablesView.emptyMessage), findsOneWidget);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R9] 800×600 下 500 行可双向滚动且长文本不截断', (
    WidgetTester tester,
  ) async {
    useViewSize(tester, const Size(800, 600));
    await tester.pumpWidget(wrapInApp(_view(_manyRows())));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);

    // 长文本按单元格宽度换行：单行放不下，渲染宽度不超出单元格，也没有省略或裁剪设置。
    final Text longNameText = tester.widget<Text>(find.text(_longName));
    expect(longNameText.maxLines, isNull);
    expect(longNameText.overflow, isNull);
    final RenderParagraph paragraph = tester.renderObject<RenderParagraph>(
      find.text(_longDescription),
    );
    expect(paragraph.size.width, lessThanOrEqualTo(300));
    expect(
      paragraph.getMaxIntrinsicWidth(double.infinity),
      greaterThan(paragraph.size.width),
    );

    final ScrollPosition horizontal = horizontalPosition(tester);
    final ScrollPosition vertical = verticalPosition(tester);
    expect(horizontal.maxScrollExtent, greaterThan(0));
    expect(vertical.maxScrollExtent, greaterThan(0));

    // 横向滚到最右，最右列完整可读。
    await tester.drag(find.byType(SchemaTablesView), const Offset(-2000, 0));
    await tester.pumpAndSettle();
    expect(horizontal.pixels, closeTo(horizontal.maxScrollExtent, 1));
    final Rect lastSizeCell = tester.getRect(
      find.text(formatByteSize(499 * 1024 * 1024)),
    );
    expect(lastSizeCell.left, greaterThanOrEqualTo(0));
    expect(lastSizeCell.right, lessThanOrEqualTo(800));

    // 纵向滚到最后一行。
    final Finder lastRow = find.text('table_499_with_a_long_name');
    await tester.drag(find.byType(SchemaTablesView), const Offset(0, -30000));
    await tester.pumpAndSettle();
    expect(vertical.pixels, closeTo(vertical.maxScrollExtent, 1));
    expect(tester.getBottomLeft(lastRow).dy, lessThanOrEqualTo(600));
    expect(tester.takeException(), isNull);
  });

  testWidgets('[p00-001/R10] 点击或悬停数据行不产生选中、导航与详情', (WidgetTester tester) async {
    await tester.pumpWidget(wrapInApp(_view(_rows)));
    final Rect before = tester.getRect(find.text('customers'));

    final TestGesture mouse = await tester.createGesture(
      kind: PointerDeviceKind.mouse,
    );
    addTearDown(mouse.removePointer);
    await mouse.addPointer(location: Offset.zero);
    await mouse.moveTo(tester.getCenter(find.text('customers')));
    await tester.pumpAndSettle();

    // 行上没有可点击组件，悬停只改变组件自带的底色。
    expect(
      find.ancestor(of: find.text('customers'), matching: find.byType(Button)),
      findsNothing,
    );
    expect(tester.takeException(), isNull);

    await tester.tap(find.text('customers'));
    await tester.pumpAndSettle();

    expect(tester.getRect(find.text('customers')), before);
    expect(find.text('customers'), findsOneWidget);
    expect(find.text('invoices'), findsOneWidget);
    expect(find.text('客户主数据'), findsOneWidget);
    expect(find.text('sessions'), findsOneWidget);
  });

  testWidgets('[p00-007/R4] 系统亮度变化后横纵滚动位置保持', (WidgetTester tester) async {
    useViewSize(tester, const Size(800, 600));
    await tester.pumpWidget(wrapInApp(_view(_manyRows())));
    await tester.pumpAndSettle();

    await tester.drag(find.byType(SchemaTablesView), const Offset(-40, 0));
    await tester.drag(find.byType(SchemaTablesView), const Offset(0, -600));
    await tester.pumpAndSettle();

    final double horizontalOffset = horizontalPosition(tester).pixels;
    final double verticalOffset = verticalPosition(tester).pixels;
    expect(horizontalOffset, greaterThan(0));
    expect(verticalOffset, greaterThan(0));

    tester.platformDispatcher.platformBrightnessTestValue = Brightness.dark;
    addTearDown(tester.platformDispatcher.clearPlatformBrightnessTestValue);
    await tester.pumpAndSettle();

    expect(horizontalPosition(tester).pixels, horizontalOffset);
    expect(verticalPosition(tester).pixels, verticalOffset);
    expect(tester.takeException(), isNull);
  });
}
