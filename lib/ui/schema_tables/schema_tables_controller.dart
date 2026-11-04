// spec: p00-001
// layer: ui
// covers: p00-001/R8

import 'package:flutter/foundation.dart';

/// 可排序列。描述列不参与排序，因此不在其中。
enum SchemaSortColumn { name, relationKind, columnCount, estimatedRows, size }

/// 单列排序状态。只保存当前列与方向，不持有数据源。
///
/// 比较依据由调用方传入，控制器不导入领域模型。
final class SchemaTablesController<T> extends ChangeNotifier {
  SchemaTablesController({
    required Map<SchemaSortColumn, Comparator<T>> comparatorByColumn,
    SchemaSortColumn initialColumn = SchemaSortColumn.name,
    bool initialAscending = true,
  }) : _comparators = comparatorByColumn,
       _column = initialColumn,
       _ascending = initialAscending;

  final Map<SchemaSortColumn, Comparator<T>> _comparators;

  SchemaSortColumn _column;
  bool _ascending;
  bool _explicitSort = false;

  /// 当前排序列。
  SchemaSortColumn get column => _column;

  /// 当前是否升序。
  bool get ascending => _ascending;

  // [p00-001/R8] 首列默认升序；点击新列回到升序，再次点击同一列切为降序。
  // 默认的表名升序不计作一次点击，所以表名第一次被点击仍为升序。
  void sortBy(SchemaSortColumn next) {
    if (next != _column) {
      _column = next;
      _ascending = true;
    } else if (!_explicitSort) {
      _ascending = true;
    } else {
      _ascending = !_ascending;
    }
    _explicitSort = true;
    notifyListeners();
  }

  // [p00-001/R8] 用调用方给出的比较依据对传入记录的副本排序，不改动调用方列表。
  List<T> sorted(List<T> rows) {
    final comparator = _comparators[_column];
    assert(comparator != null, '排序列 $_column 缺少比较依据');
    final ordered = List<T>.of(rows);
    if (comparator != null) {
      ordered.sort(comparator);
    }
    if (!_ascending) {
      return ordered.reversed.toList();
    }
    return ordered;
  }
}
