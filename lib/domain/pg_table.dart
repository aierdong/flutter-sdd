// spec: p00-001
// layer: domain
// covers: p00-001/R3

/// 外部传入的普通表记录。纯 Dart 对象：只保存传入值，不读取数据库或网络。
final class PgTable {
  // [p00-001/R3] 表记录逐项保存传入的名称、类型、描述、列数、估算行数与原始字节大小。
  const PgTable({
    required this.name,
    required this.relationKind,
    required this.columnCount,
    required this.estimatedRows,
    required this.sizeBytes,
    this.description,
  });

  /// 表名。
  final String name;

  /// 关系类型，本期演示数据固定为 `Table`。
  final String relationKind;

  /// 表注释；没有注释时为 `null`。
  final String? description;

  /// 列数。
  final int columnCount;

  /// 估算行数。
  final int estimatedRows;

  /// 原始字节大小。显示单位由界面换算，模型不做格式化。
  final int sizeBytes;
}
