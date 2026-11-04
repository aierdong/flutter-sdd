// spec: p00-001
// layer: test
// covers: p00-001/R1, p00-001/R3, p00-001/R4, p00-001/R5, p00-001/R6, p00-001/R7, p00-001/R11

import 'package:flutter/material.dart';
import 'package:flutter_sdd/app.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('[p00-001/R1] 首屏直接是表列表页，没有计数器', (WidgetTester tester) async {
    await tester.pumpWidget(const SchemaTablesApp());
    await tester.pumpAndSettle();

    expect(find.text('Local dev · myapp'), findsOneWidget);
    expect(find.text('public'), findsOneWidget);
    expect(find.text('新建连接'), findsOneWidget);
    expect(find.byIcon(Icons.add), findsNothing);
    expect(find.textContaining('You have pushed the button'), findsNothing);
  });

  test('[p00-001/R3] 演示数据为六张表且覆盖空描述与长文本', () {
    expect(demoPgTables.length, 6);
    expect(
      demoPgTables.where((table) => table.description == null),
      isNotEmpty,
    );
    expect(demoPgTables.any((table) => table.name.length > 30), isTrue);
    expect(
      demoPgTables.any((table) => (table.description ?? '').length > 20),
      isTrue,
    );
    expect(
      demoPgTables.map((table) => table.columnCount).toSet().length,
      greaterThan(1),
    );
  });

  test('[p00-001/R11] 未设置或未知的 DEMO_STATE 回退 data', () {
    expect(demoStateFrom(null), SchemaTablesDemoState.data);
    expect(demoStateFrom(''), SchemaTablesDemoState.data);
    expect(demoStateFrom('unknown'), SchemaTablesDemoState.data);
    expect(demoStateFrom('data'), SchemaTablesDemoState.data);
    expect(demoStateFrom('empty'), SchemaTablesDemoState.empty);
    expect(demoStateFrom('loading'), SchemaTablesDemoState.loading);
    expect(demoStateFrom('error'), SchemaTablesDemoState.error);
  });

  testWidgets('[p00-001/R7] 默认六行数据与数量统计', (WidgetTester tester) async {
    await tester.pumpWidget(const SchemaTablesApp());
    await tester.pumpAndSettle();

    expect(find.text('6 张表'), findsOneWidget);
    expect(find.text('customers'), findsOneWidget);
  });

  testWidgets('[p00-001/R4] 空态下页头仍在且没有数量统计', (WidgetTester tester) async {
    await tester.pumpWidget(
      const SchemaTablesApp(state: SchemaTablesDemoState.empty),
    );
    await tester.pumpAndSettle();

    expect(find.text('Local dev · myapp'), findsOneWidget);
    expect(find.text('该 schema 下暂无表。'), findsOneWidget);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R5] 加载态只在表格区显示进度指示', (WidgetTester tester) async {
    await tester.pumpWidget(
      const SchemaTablesApp(state: SchemaTablesDemoState.loading),
    );
    await tester.pump();

    expect(find.text('Local dev · myapp'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R6] 失败态显示演示消息与集中错误码', (WidgetTester tester) async {
    await tester.pumpWidget(
      const SchemaTablesApp(state: SchemaTablesDemoState.error),
    );
    await tester.pumpAndSettle();

    expect(find.text('加载表失败（错误码：FSD-TABLE-001）'), findsOneWidget);
    expect(find.textContaining('张表'), findsNothing);
  });
}
