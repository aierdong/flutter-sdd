// spec: p00-001
// layer: ui
// covers: p00-001/R3, p00-001/R4, p00-001/R9, p00-001/R10

import 'package:flutter/material.dart';
import 'package:flutter_sdd/core/theme/app_density.dart';
import 'package:flutter_sdd/core/theme/app_spacing.dart';
import 'package:flutter_sdd/core/theme/app_theme.dart';
import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_sdd/ui/schema_tables/schema_tables_controller.dart';

/// 一列的表头文案、固定宽度与对应的排序列。`sortColumn` 为 `null` 表示不可排序。
final class _Column {
  const _Column(this.label, this.width, this.sortColumn);

  final String label;
  final double width;
  final SchemaSortColumn? sortColumn;
}

const List<_Column> _columns = <_Column>[
  _Column('表名', 220, SchemaSortColumn.name),
  _Column('类型', 80, SchemaSortColumn.relationKind),
  _Column('描述', 300, null),
  _Column('列数', 70, SchemaSortColumn.columnCount),
  _Column('估算行数', 110, SchemaSortColumn.estimatedRows),
  _Column('大小', 100, SchemaSortColumn.size),
];

final double _totalWidth = _columns.fold<double>(
  0,
  (sum, column) => sum + column.width,
);

/// 表格区域：六列表头、数据行或空态表体，并提供横向与纵向滚动。
final class SchemaTablesView extends StatelessWidget {
  const SchemaTablesView({
    super.key,
    required this.rows,
    required this.sortColumn,
    required this.ascending,
    required this.onSort,
  });

  /// 横向滚动容器，供滚动行为检查定位。
  static const Key horizontalScrollKey = Key('schema-tables-horizontal');

  /// 数据行纵向滚动容器，供滚动行为检查定位。
  static const Key verticalScrollKey = Key('schema-tables-vertical');

  /// 空态提示文案。
  static const String emptyMessage = '该 schema 下暂无表。';

  /// 已排好序的行。
  final List<PgTable> rows;

  /// 当前排序列。
  final SchemaSortColumn sortColumn;

  /// 当前是否升序。
  final bool ascending;

  /// 表头排序动作。
  final ValueChanged<SchemaSortColumn> onSort;

  // [p00-001/R9] 表格区提供横向与纵向滚动：列宽固定，长文本换行不截断，全部行都构建。
  @override
  Widget build(BuildContext context) {
    final colors = AppPalette.of(context);
    return SingleChildScrollView(
      key: horizontalScrollKey,
      scrollDirection: Axis.horizontal,
      child: SizedBox(
        width: _totalWidth,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            _headerRow(colors),
            Container(height: 1, color: colors.border),
            if (rows.isEmpty)
              _emptyBody(colors)
            else
              Expanded(
                child: SingleChildScrollView(
                  key: verticalScrollKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      for (final row in rows) _dataRow(row, colors),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  // [p00-001/R4] 没有表时保留六列表头，只在表体显示空态提示。
  Widget _emptyBody(AppPalette colors) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.space3),
      child: Text(
        emptyMessage,
        style: TextStyle(
          fontSize: AppDensity.bodyFontSize,
          color: colors.textMuted,
        ),
      ),
    );
  }

  Widget _headerRow(AppPalette colors) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.space1),
      child: Row(
        children: <Widget>[
          for (final column in _columns) _headerCell(column, colors),
        ],
      ),
    );
  }

  Widget _headerCell(_Column column, AppPalette colors) {
    final sortColumnOfCell = column.sortColumn;
    final cell = SizedBox(
      width: column.width,
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.space2,
          vertical: AppSpacing.space1,
        ),
        child: Text(
          _headerLabel(column, sortColumnOfCell),
          style: TextStyle(
            fontSize: AppDensity.regionTitleFontSize,
            fontWeight: AppDensity.regionTitleWeight,
            color: colors.text,
          ),
        ),
      ),
    );
    if (sortColumnOfCell == null) {
      return cell;
    }
    return InkWell(onTap: () => onSort(sortColumnOfCell), child: cell);
  }

  String _headerLabel(_Column column, SchemaSortColumn? sortable) {
    if (sortable == null || sortable != sortColumn) {
      return column.label;
    }
    return '${column.label} ${ascending ? '▲' : '▼'}';
  }

  // [p00-001/R3] 每行逐格取自传入记录：空描述显示 —，大小按 1024 进位的人类可读单位。
  // [p00-001/R10] 数据行不挂点击、悬停或导航处理，保持只读展示。
  Widget _dataRow(PgTable table, AppPalette colors) {
    final style = TextStyle(
      fontSize: AppDensity.bodyFontSize,
      color: colors.text,
    );
    return Container(
      constraints: const BoxConstraints(minHeight: AppDensity.rowHeight),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: colors.border)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          for (final (index, column) in _columns.indexed)
            _dataCell(_cellText(table, index), column.width, style),
        ],
      ),
    );
  }

  Widget _dataCell(String text, double width, TextStyle style) {
    return SizedBox(
      width: width,
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.space2,
          vertical: AppSpacing.space1,
        ),
        child: Text(text, style: style),
      ),
    );
  }

  String _cellText(PgTable table, int index) {
    return switch (index) {
      0 => table.name,
      1 => table.relationKind,
      2 => _descriptionText(table.description),
      3 => '${table.columnCount}',
      4 => '${table.estimatedRows}',
      5 => formatByteSize(table.sizeBytes),
      _ => '',
    };
  }

  String _descriptionText(String? description) {
    final text = description?.trim() ?? '';
    return text.isEmpty ? '—' : text;
  }
}

/// 把原始字节数换算成 B/KB/MB/GB/TB。按 1024 进位，B 之外最多一位小数，去掉末尾 `.0`。
String formatByteSize(int bytes) {
  if (bytes < 1024) {
    return '$bytes B';
  }
  const List<String> units = <String>['KB', 'MB', 'GB', 'TB'];
  var value = bytes / 1024;
  var unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  final fixed = value.toStringAsFixed(1);
  final trimmed = fixed.endsWith('.0')
      ? fixed.substring(0, fixed.length - 2)
      : fixed;
  return '$trimmed ${units[unitIndex]}';
}
