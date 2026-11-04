// spec: p00-001
// layer: ui
// covers: p00-001/R2, p00-001/R4, p00-001/R5, p00-001/R6, p00-001/R7, p00-001/R8, p00-001/R11

import 'package:flutter/material.dart';
import 'package:flutter_sdd/core/errors/app_failure.dart';
import 'package:flutter_sdd/core/theme/app_density.dart';
import 'package:flutter_sdd/core/theme/app_spacing.dart';
import 'package:flutter_sdd/core/theme/app_theme.dart';
import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_sdd/ui/schema_tables/schema_tables_controller.dart';
import 'package:flutter_sdd/ui/schema_tables/widgets/schema_tables_view.dart';

/// 页面状态。加载中、失败与已加载记录三者互斥。
sealed class SchemaTablesState {
  const SchemaTablesState();
}

/// 数据还没到。
final class SchemaTablesLoading extends SchemaTablesState {
  const SchemaTablesLoading();
}

/// 加载失败。
final class SchemaTablesFailed extends SchemaTablesState {
  const SchemaTablesFailed(this.failure);

  /// 展示用的失败对象。
  final AppFailure failure;
}

/// 已加载记录。列表为空时页面显示空态。
final class SchemaTablesLoaded extends SchemaTablesState {
  const SchemaTablesLoaded(this.tables);

  /// 调用方传入的表记录。
  final List<PgTable> tables;
}

/// 单 schema 表列表页。页头与表格区两段结构。
final class SchemaTablesPage extends StatefulWidget {
  // [p00-001/R11] 连接信息、schema、表数据与页面状态全部由调用方传入，页面不读数据库也不发网络请求。
  const SchemaTablesPage({
    super.key,
    required this.connectionName,
    required this.databaseName,
    required this.schemaName,
    required this.state,
  });

  /// 连接名。
  final String connectionName;

  /// 数据库名。
  final String databaseName;

  /// 当前 schema 名。
  final String schemaName;

  /// 页面状态。
  final SchemaTablesState state;

  @override
  State<SchemaTablesPage> createState() => _SchemaTablesPageState();
}

class _SchemaTablesPageState extends State<SchemaTablesPage> {
  // [p00-001/R8] 五列比较依据由页面提供：文本按字典序，列数与行数按数值，大小按原始字节。
  late final SchemaTablesController<PgTable> _controller =
      SchemaTablesController<PgTable>(
        comparatorByColumn: <SchemaSortColumn, Comparator<PgTable>>{
          SchemaSortColumn.name: (a, b) => a.name.compareTo(b.name),
          SchemaSortColumn.relationKind: (a, b) =>
              a.relationKind.compareTo(b.relationKind),
          SchemaSortColumn.columnCount: (a, b) =>
              a.columnCount.compareTo(b.columnCount),
          SchemaSortColumn.estimatedRows: (a, b) =>
              a.estimatedRows.compareTo(b.estimatedRows),
          SchemaSortColumn.size: (a, b) => a.sizeBytes.compareTo(b.sizeBytes),
        },
      );

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = AppPalette.of(context);
    return Material(
      color: colors.canvas,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          _header(colors),
          Container(height: 1, color: colors.border),
          Expanded(child: _body(colors)),
        ],
      ),
    );
  }

  Widget _body(AppPalette colors) {
    return switch (widget.state) {
      SchemaTablesLoading() => _loading(colors),
      SchemaTablesFailed(:final failure) => _failed(colors, failure),
      SchemaTablesLoaded(:final tables) => ListenableBuilder(
        listenable: _controller,
        builder: (BuildContext context, Widget? child) =>
            _loaded(colors, tables),
      ),
    };
  }

  // [p00-001/R2] 页头两行显示连接名与数据库名、schema 名；右侧按钮禁用，页头不含主机、端口与用户名。
  Widget _header(AppPalette colors) {
    return SizedBox(
      height: AppDensity.pageHeaderHeight,
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.space4,
          vertical: AppSpacing.space2,
        ),
        child: Row(
          children: <Widget>[
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    '${widget.connectionName} · ${widget.databaseName}',
                    style: TextStyle(
                      fontSize: AppDensity.bodyFontSize,
                      fontWeight: AppDensity.regionTitleWeight,
                      color: colors.text,
                    ),
                  ),
                  Text(
                    widget.schemaName,
                    style: TextStyle(
                      fontSize: AppDensity.secondaryFontSize,
                      color: colors.textMuted,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.space2),
            const OutlinedButton(onPressed: null, child: Text('新建连接')),
          ],
        ),
      ),
    );
  }

  // [p00-001/R5] 加载中只在表格区显示进度指示，不显示表格、数据行与数量统计。
  Widget _loading(AppPalette colors) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.space4),
        child: CircularProgressIndicator(color: colors.accent, strokeWidth: 2),
      ),
    );
  }

  // [p00-001/R6] 失败文案把消息与集中错误码拼成同一段，不展示 cause 或驱动异常原文。
  Widget _failed(AppPalette colors, AppFailure failure) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.space4),
        child: Text(
          '${failure.message}（错误码：${failure.code}）',
          style: TextStyle(
            fontSize: AppDensity.bodyFontSize,
            color: colors.error,
          ),
        ),
      ),
    );
  }

  // [p00-001/R4] 已加载但无记录时不显示数量统计，六列表头与空态提示交给表格区。
  // [p00-001/R7] 有数据时显示 N 张表，N 取自实际渲染的行数；空、加载与失败态都不显示。
  Widget _loaded(AppPalette colors, List<PgTable> tables) {
    final ordered = _controller.sorted(tables);
    final hasRows = ordered.isNotEmpty;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        if (hasRows)
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.space4,
              vertical: AppSpacing.space1,
            ),
            child: Text(
              '${ordered.length} 张表',
              style: TextStyle(
                fontSize: AppDensity.secondaryFontSize,
                color: colors.textMuted,
              ),
            ),
          ),
        if (hasRows) Container(height: 1, color: colors.border),
        Expanded(
          child: SchemaTablesView(
            rows: ordered,
            sortColumn: _controller.column,
            ascending: _controller.ascending,
            onSort: _controller.sortBy,
          ),
        ),
      ],
    );
  }
}
