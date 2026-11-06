// spec: p00-001, p00-007
// layer: ui
// covers: p00-001/R2, p00-001/R4, p00-001/R5, p00-001/R6, p00-001/R7, p00-001/R8, p00-001/R11, p00-007/R1, p00-007/R3, p00-007/R4, p00-007/R5

import 'package:flutter_sdd/core/errors/app_failure.dart';
import 'package:flutter_sdd/core/theme/app_density.dart';
import 'package:flutter_sdd/core/theme/app_spacing.dart';
import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_sdd/ui/schema_tables/schema_tables_controller.dart';
import 'package:flutter_sdd/ui/schema_tables/widgets/schema_tables_view.dart';
import 'package:shadcn_flutter/shadcn_flutter.dart';

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
          SchemaSortColumn.name: (PgTable a, PgTable b) =>
              a.name.compareTo(b.name),
          SchemaSortColumn.relationKind: (PgTable a, PgTable b) =>
              a.relationKind.compareTo(b.relationKind),
          SchemaSortColumn.columnCount: (PgTable a, PgTable b) =>
              a.columnCount.compareTo(b.columnCount),
          SchemaSortColumn.estimatedRows: (PgTable a, PgTable b) =>
              a.estimatedRows.compareTo(b.estimatedRows),
          SchemaSortColumn.size: (PgTable a, PgTable b) =>
              a.sizeBytes.compareTo(b.sizeBytes),
        },
      );

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  // [p00-007/R3] 页面底色与文字色取自当前 shadcn 主题，系统切换浅色、深色时整页随动。
  // [p00-007/R4] 排序控制器与表格滚动状态都在本页面生命周期内，主题变化不重建它们。
  // [p00-007/R5] 页头内容、数量统计、四态文案与互斥关系保持迁移前的行为。
  @override
  Widget build(BuildContext context) {
    final ColorScheme scheme = Theme.of(context).colorScheme;
    return ColoredBox(
      color: scheme.background,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          _header(scheme),
          Container(height: 1, color: scheme.border),
          Expanded(child: _body(scheme)),
        ],
      ),
    );
  }

  Widget _body(ColorScheme scheme) {
    return switch (widget.state) {
      SchemaTablesLoading() => _loading(),
      SchemaTablesFailed(:final AppFailure failure) => _failed(scheme, failure),
      SchemaTablesLoaded(:final List<PgTable> tables) => ListenableBuilder(
        listenable: _controller,
        builder: (BuildContext context, Widget? child) =>
            _loaded(scheme, tables),
      ),
    };
  }

  // [p00-001/R2] 页头两行显示连接名与数据库名、schema 名；右侧按钮禁用，页头不含主机、端口与用户名。
  // [p00-007/R1] 禁用按钮改用 shadcn_flutter 的 Button.outline，页头不再使用 Material 组件。
  Widget _header(ColorScheme scheme) {
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
                      color: scheme.foreground,
                    ),
                  ),
                  Text(
                    widget.schemaName,
                    style: TextStyle(
                      fontSize: AppDensity.secondaryFontSize,
                      color: scheme.mutedForeground,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.space2),
            const Button.outline(onPressed: null, child: Text('新建连接')),
          ],
        ),
      ),
    );
  }

  // [p00-001/R5] 加载中只在表格区显示进度指示，不显示表格、数据行与数量统计。
  // [p00-007/R1] 加载指示改用 shadcn_flutter 的 CircularProgressIndicator。
  Widget _loading() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(AppSpacing.space4),
        child: CircularProgressIndicator(),
      ),
    );
  }

  // [p00-001/R6] 失败文案把消息与集中错误码拼成同一段，不展示 cause 或驱动异常原文。
  Widget _failed(ColorScheme scheme, AppFailure failure) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.space4),
        child: Text(
          '${failure.message}（错误码：${failure.code}）',
          style: TextStyle(
            fontSize: AppDensity.bodyFontSize,
            color: scheme.destructive,
          ),
        ),
      ),
    );
  }

  // [p00-001/R4] 已加载但无记录时不显示数量统计，六列表头与空态提示交给表格区。
  // [p00-001/R7] 有数据时显示 N 张表，N 取自实际渲染的行数；空、加载与失败态都不显示。
  Widget _loaded(ColorScheme scheme, List<PgTable> tables) {
    final List<PgTable> ordered = _controller.sorted(tables);
    final bool hasRows = ordered.isNotEmpty;
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
                color: scheme.mutedForeground,
              ),
            ),
          ),
        if (hasRows) Container(height: 1, color: scheme.border),
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
