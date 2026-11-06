// spec: p00-001, p00-007
// layer: test
// covers: p00-001/R1, p00-001/R3, p00-001/R4, p00-001/R5, p00-001/R6, p00-001/R7, p00-001/R11, p00-007/R1, p00-007/R3, p00-007/R5

import 'package:flutter_sdd/app.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shadcn_flutter/shadcn_flutter.dart';

import 'support/contrast.dart';

const String _header = 'Local dev · myapp';

/// 以指定演示状态启动应用。系统深浅模式由平台亮度决定。
Future<void> _pumpApp(
  WidgetTester tester, {
  SchemaTablesDemoState state = SchemaTablesDemoState.data,
  Brightness brightness = Brightness.light,
}) async {
  tester.platformDispatcher.platformBrightnessTestValue = brightness;
  await tester.pumpWidget(SchemaTablesApp(state: state));
  await _pumpFrames(tester, state);
}

/// 等待界面稳定。加载态的进度指示持续动画，只能推进固定时长。
Future<void> _pumpFrames(
  WidgetTester tester,
  SchemaTablesDemoState state,
) async {
  if (state == SchemaTablesDemoState.loading) {
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    return;
  }
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('[p00-001/R1] 首屏直接是表列表页，没有计数器', (WidgetTester tester) async {
    await _pumpApp(tester);

    expect(find.text(_header), findsOneWidget);
    expect(find.text('public'), findsOneWidget);
    expect(find.text('新建连接'), findsOneWidget);
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
    await _pumpApp(tester);

    expect(find.text('6 张表'), findsOneWidget);
    expect(find.text('customers'), findsOneWidget);
  });

  testWidgets('[p00-001/R4] 空态下页头仍在且没有数量统计', (WidgetTester tester) async {
    await _pumpApp(tester, state: SchemaTablesDemoState.empty);

    expect(find.text(_header), findsOneWidget);
    expect(find.text('该 schema 下暂无表。'), findsOneWidget);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R5] 加载态只在表格区显示进度指示', (WidgetTester tester) async {
    await _pumpApp(tester, state: SchemaTablesDemoState.loading);

    expect(find.text(_header), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-001/R6] 失败态显示演示消息与集中错误码', (WidgetTester tester) async {
    await _pumpApp(tester, state: SchemaTablesDemoState.error);

    expect(find.text('加载表失败（错误码：FSD-TABLE-001）'), findsOneWidget);
    expect(find.textContaining('张表'), findsNothing);
  });

  testWidgets('[p00-007/R1] 应用根是 shadcn_flutter 的 ShadcnApp', (
    WidgetTester tester,
  ) async {
    await _pumpApp(tester);

    expect(find.byType(ShadcnApp), findsOneWidget);
    expect(find.widgetWithText(Button, '新建连接'), findsOneWidget);
  });

  testWidgets('[p00-007/R3] 四种演示状态在系统浅色与深色下配色随动且正文达到 4.5:1', (
    WidgetTester tester,
  ) async {
    addTearDown(tester.platformDispatcher.clearPlatformBrightnessTestValue);
    const Map<SchemaTablesDemoState, List<String>> texts =
        <SchemaTablesDemoState, List<String>>{
          SchemaTablesDemoState.data: <String>[
            _header,
            'public',
            'customers',
            '6 张表',
          ],
          SchemaTablesDemoState.empty: <String>[_header, '该 schema 下暂无表。'],
          SchemaTablesDemoState.loading: <String>[_header],
          SchemaTablesDemoState.error: <String>[
            _header,
            '加载表失败（错误码：FSD-TABLE-001）',
          ],
        };

    for (final MapEntry<SchemaTablesDemoState, List<String>> entry
        in texts.entries) {
      await _pumpApp(tester, state: entry.key);
      final Color lightCanvas = renderedBackgroundColor(
        tester,
        find.text(_header),
      );
      final Map<String, Color> lightColors = <String, Color>{
        for (final String text in entry.value)
          text: renderedTextColor(tester, find.textContaining(text)),
      };
      for (final String text in entry.value) {
        expectTextContrast(
          tester,
          find.textContaining(text),
          label: '$text（浅色）',
        );
      }

      tester.platformDispatcher.platformBrightnessTestValue = Brightness.dark;
      await _pumpFrames(tester, entry.key);

      expect(
        renderedBackgroundColor(tester, find.text(_header)),
        isNot(lightCanvas),
      );
      for (final String text in entry.value) {
        expect(
          renderedTextColor(tester, find.textContaining(text)),
          isNot(lightColors[text]),
          reason: '$text 没有跟随系统模式换色',
        );
        expectTextContrast(
          tester,
          find.textContaining(text),
          label: '$text（深色）',
        );
      }
    }
    expect(tester.takeException(), isNull);
  });

  testWidgets('[p00-007/R5] 四态互斥且页头在每种状态下都可见', (WidgetTester tester) async {
    addTearDown(tester.platformDispatcher.clearPlatformBrightnessTestValue);
    const List<(SchemaTablesDemoState, String)> markers =
        <(SchemaTablesDemoState, String)>[
          (SchemaTablesDemoState.data, 'customers'),
          (SchemaTablesDemoState.empty, '该 schema 下暂无表。'),
          (SchemaTablesDemoState.loading, ''),
          (SchemaTablesDemoState.error, '加载表失败（错误码：FSD-TABLE-001）'),
        ];

    for (final (SchemaTablesDemoState state, _) in markers) {
      await _pumpApp(tester, state: state);

      expect(find.text(_header), findsOneWidget);
      expect(find.text('public'), findsOneWidget);
      expect(find.text('新建连接'), findsOneWidget);

      for (final (SchemaTablesDemoState other, String otherMarker) in markers) {
        if (otherMarker.isEmpty) {
          continue;
        }
        expect(
          find.textContaining(otherMarker),
          other == state ? findsOneWidget : findsNothing,
        );
      }
      expect(
        find.byType(CircularProgressIndicator),
        state == SchemaTablesDemoState.loading ? findsOneWidget : findsNothing,
      );
    }
  });
}
