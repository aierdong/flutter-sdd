// spec: p00-001
// layer: test
// covers: p00-001/R8

import 'package:flutter_sdd/ui/schema_tables/schema_tables_controller.dart';
import 'package:flutter_test/flutter_test.dart';

final class _Record {
  const _Record(this.label, this.size);

  final String label;
  final int size;
}

SchemaTablesController<_Record> _buildController() {
  return SchemaTablesController<_Record>(
    comparatorByColumn: <SchemaSortColumn, Comparator<_Record>>{
      SchemaSortColumn.name: (a, b) => a.label.compareTo(b.label),
      SchemaSortColumn.size: (a, b) => a.size.compareTo(b.size),
    },
  );
}

List<_Record> _input() => <_Record>[
  const _Record('charlie', 300),
  const _Record('alpha', 900),
  const _Record('bravo', 100),
];

List<String> _labels(List<_Record> rows) =>
    rows.map((record) => record.label).toList();

void main() {
  test('[p00-001/R8] 默认按第一列升序，且首次点击该列仍为升序', () {
    final controller = _buildController();

    expect(controller.column, SchemaSortColumn.name);
    expect(controller.ascending, isTrue);

    controller.sortBy(SchemaSortColumn.name);

    expect(controller.column, SchemaSortColumn.name);
    expect(controller.ascending, isTrue);
    expect(_labels(controller.sorted(_input())), <String>[
      'alpha',
      'bravo',
      'charlie',
    ]);
  });

  test('[p00-001/R8] 再次点击同一列切换为降序', () {
    final controller = _buildController();

    controller.sortBy(SchemaSortColumn.name);
    controller.sortBy(SchemaSortColumn.name);

    expect(controller.ascending, isFalse);
    expect(_labels(controller.sorted(_input())), <String>[
      'charlie',
      'bravo',
      'alpha',
    ]);
  });

  test('[p00-001/R8] 切到另一列回到升序', () {
    final controller = _buildController();

    controller.sortBy(SchemaSortColumn.size);
    expect(controller.column, SchemaSortColumn.size);
    expect(controller.ascending, isTrue);
    expect(_labels(controller.sorted(_input())), <String>[
      'bravo',
      'charlie',
      'alpha',
    ]);

    controller.sortBy(SchemaSortColumn.size);
    expect(controller.ascending, isFalse);
    expect(_labels(controller.sorted(_input())), <String>[
      'alpha',
      'charlie',
      'bravo',
    ]);

    controller.sortBy(SchemaSortColumn.name);
    expect(controller.column, SchemaSortColumn.name);
    expect(controller.ascending, isTrue);
  });

  test('[p00-001/R8] 排序返回新列表，调用方输入顺序不变', () {
    final controller = _buildController();
    final input = _input();
    final before = _labels(input);

    final ordered = controller.sorted(input);

    expect(_labels(input), before);
    expect(identical(ordered, input), isFalse);
    expect(_labels(ordered), <String>['alpha', 'bravo', 'charlie']);
  });

  test('[p00-001/R8] 切换排序时通知监听者', () {
    final controller = _buildController();
    var notifications = 0;
    controller.addListener(() => notifications += 1);

    controller.sortBy(SchemaSortColumn.size);
    controller.sortBy(SchemaSortColumn.size);

    expect(notifications, 2);
  });
}
