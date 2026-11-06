// spec: p00-001, p00-007
// layer: ui
// covers: p00-001/R3, p00-001/R4, p00-001/R9, p00-001/R10, p00-007/R2, p00-007/R4

import 'package:flutter_sdd/core/theme/app_density.dart';
import 'package:flutter_sdd/core/theme/app_spacing.dart';
import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_sdd/ui/schema_tables/schema_tables_controller.dart';
import 'package:shadcn_flutter/shadcn_flutter.dart';

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

/// 表格区域：六列表头、数据行或空态表体，并提供横向与纵向滚动。
final class SchemaTablesView extends StatefulWidget {
  const SchemaTablesView({
    super.key,
    required this.rows,
    required this.sortColumn,
    required this.ascending,
    required this.onSort,
  });

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

  @override
  State<SchemaTablesView> createState() => _SchemaTablesViewState();
}

class _SchemaTablesViewState extends State<SchemaTablesView> {
  // [p00-007/R4] 双向滚动位置由本视图持有的控制器维护；主题变化只重建外观，偏移不重置。
  final ScrollController _verticalScroll = ScrollController();
  final ScrollController _horizontalScroll = ScrollController();

  @override
  void dispose() {
    _verticalScroll.dispose();
    _horizontalScroll.dispose();
    super.dispose();
  }

  // [p00-007/R2] 六列表格由 shadcn_flutter 的 Table 绘制，组件自带的行悬停与视口裁剪保持默认。
  // [p00-001/R9] 六列定宽、单元格文本换行不截断，超出窗口时横向滚动，行多时纵向滚动。
  @override
  Widget build(BuildContext context) {
    final ColorScheme scheme = Theme.of(context).colorScheme;
    return Table(
      verticalController: _verticalScroll,
      horizontalController: _horizontalScroll,
      columnWidths: <int, TableSize>{
        for (final (int index, _Column column) in _columns.indexed)
          index: FixedTableSize(column.width),
      },
      rows: <TableRow>[
        TableHeader(cells: _headerCells(scheme)),
        if (widget.rows.isEmpty)
          TableRow(cells: <TableCell>[_emptyCell(scheme)])
        else
          for (final PgTable table in widget.rows) _dataRow(table, scheme),
      ],
    );
  }

  // [p00-001/R4] 没有表时保留六列表头，只在表体显示空态提示。
  TableCell _emptyCell(ColorScheme scheme) {
    return TableCell(
      columnSpan: _columns.length,
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.space3),
        child: Text(
          SchemaTablesView.emptyMessage,
          style: TextStyle(
            fontSize: AppDensity.bodyFontSize,
            color: scheme.mutedForeground,
          ),
        ),
      ),
    );
  }

  List<TableCell> _headerCells(ColorScheme scheme) {
    return <TableCell>[
      for (final _Column column in _columns)
        TableCell(child: _headerCell(column, scheme)),
    ];
  }

  Widget _headerCell(_Column column, ColorScheme scheme) {
    final Text label = Text(
      _headerLabel(column),
      style: TextStyle(
        fontSize: AppDensity.regionTitleFontSize,
        fontWeight: AppDensity.regionTitleWeight,
        color: scheme.foreground,
      ),
    );
    final SchemaSortColumn? sortColumn = column.sortColumn;
    if (sortColumn == null) {
      return Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.space2,
          vertical: AppSpacing.space1,
        ),
        child: label,
      );
    }
    return Button.ghost(
      onPressed: () => widget.onSort(sortColumn),
      alignment: Alignment.centerLeft,
      child: label,
    );
  }

  String _headerLabel(_Column column) {
    final SchemaSortColumn? sortColumn = column.sortColumn;
    if (sortColumn == null || sortColumn != widget.sortColumn) {
      return column.label;
    }
    return '${column.label} ${widget.ascending ? '▲' : '▼'}';
  }

  // [p00-001/R3] 每行逐格取自传入记录：空描述显示 —，大小按 1024 进位的人类可读单位。
  // [p00-001/R10] 数据行不挂点击、导航或详情处理，只保留组件自带的行悬停外观。
  TableRow _dataRow(PgTable table, ColorScheme scheme) {
    final TextStyle style = TextStyle(
      fontSize: AppDensity.bodyFontSize,
      color: scheme.foreground,
    );
    return TableRow(
      cells: <TableCell>[
        for (int index = 0; index < _columns.length; index += 1)
          TableCell(
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.space2,
                vertical: AppSpacing.space1,
              ),
              child: Text(_cellText(table, index), style: style),
            ),
          ),
      ],
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
    final String text = description?.trim() ?? '';
    return text.isEmpty ? '—' : text;
  }
}

/// 把原始字节数换算成 B/KB/MB/GB/TB。按 1024 进位，B 之外最多一位小数，去掉末尾 `.0`。
String formatByteSize(int bytes) {
  if (bytes < 1024) {
    return '$bytes B';
  }
  const List<String> units = <String>['KB', 'MB', 'GB', 'TB'];
  double value = bytes / 1024;
  int unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  final String fixed = value.toStringAsFixed(1);
  final String trimmed = fixed.endsWith('.0')
      ? fixed.substring(0, fixed.length - 2)
      : fixed;
  return '$trimmed ${units[unitIndex]}';
}
