// spec: p00-001
// layer: test
// covers: p00-001/R3

import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('[p00-001/R3] 表记录逐项保留传入的名称、类型、列数、行数与字节大小', () {
    const table = PgTable(
      name: 'orders',
      relationKind: 'Table',
      description: '订单主表',
      columnCount: 12,
      estimatedRows: 4200,
      sizeBytes: 8192,
    );

    expect(table.name, 'orders');
    expect(table.relationKind, 'Table');
    expect(table.description, '订单主表');
    expect(table.columnCount, 12);
    expect(table.estimatedRows, 4200);
    expect(table.sizeBytes, 8192);
  });

  test('[p00-001/R3] 描述缺省时保持为空值', () {
    const table = PgTable(
      name: 'invoices',
      relationKind: 'Table',
      columnCount: 3,
      estimatedRows: 0,
      sizeBytes: 0,
    );

    expect(table.description, isNull);
    expect(table.estimatedRows, 0);
    expect(table.sizeBytes, 0);
  });
}
