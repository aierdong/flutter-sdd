// spec: p00-001
// layer: core
// covers: p00-001/R1

import 'package:flutter/material.dart';
import 'package:flutter_sdd/core/errors/app_failure.dart';
import 'package:flutter_sdd/core/errors/failure_codes.dart';
import 'package:flutter_sdd/core/theme/app_theme.dart';
import 'package:flutter_sdd/domain/pg_table.dart';
import 'package:flutter_sdd/ui/schema_tables/schema_tables_page.dart';

/// 演示状态。默认 `data`。
enum SchemaTablesDemoState { data, empty, loading, error }

/// 把编译期 `DEMO_STATE` 映射为演示状态；未设置或未知值回退 `data`。
SchemaTablesDemoState demoStateFrom(String? raw) {
  return switch (raw) {
    'empty' => SchemaTablesDemoState.empty,
    'loading' => SchemaTablesDemoState.loading,
    'error' => SchemaTablesDemoState.error,
    _ => SchemaTablesDemoState.data,
  };
}

/// 演示连接名。
const String demoConnectionName = 'Local dev';

/// 演示数据库名。
const String demoDatabaseName = 'myapp';

/// 演示 schema 名。
const String demoSchemaName = 'public';

/// 演示表记录。覆盖空描述、长表名、长描述、不同列数、行数与字节大小。
const List<PgTable> demoPgTables = <PgTable>[
  PgTable(
    name: 'audit_log_entries_for_compliance_export',
    relationKind: 'Table',
    description: '合规导出用的审计日志明细，保留最近 180 天并可按操作人追溯',
    columnCount: 14,
    estimatedRows: 2480000,
    sizeBytes: 5265334272,
  ),
  PgTable(
    name: 'customers',
    relationKind: 'Table',
    description: '客户主数据',
    columnCount: 9,
    estimatedRows: 8210,
    sizeBytes: 3407872,
  ),
  PgTable(
    name: 'invoices',
    relationKind: 'Table',
    columnCount: 12,
    estimatedRows: 152300,
    sizeBytes: 44040192,
  ),
  PgTable(
    name: 'order_items',
    relationKind: 'Table',
    description: '订单明细，含折扣与税率快照',
    columnCount: 7,
    estimatedRows: 982145,
    sizeBytes: 268435456,
  ),
  PgTable(
    name: 'products',
    relationKind: 'Table',
    description: '商品目录，含上下架状态',
    columnCount: 11,
    estimatedRows: 3420,
    sizeBytes: 1048576,
  ),
  PgTable(
    name: 'sessions',
    relationKind: 'Table',
    description: '登录会话，只保存令牌哈希',
    columnCount: 6,
    estimatedRows: 41200,
    sizeBytes: 65536,
  ),
];

/// 演示失败对象。消息与集中码表拼出界面文案。
const AppFailure demoFailure = AppFailure(
  code: FailureCodes.tableLoadFailed,
  message: '加载表失败',
);

/// 组合根：装配演示输入与主题。
final class SchemaTablesApp extends StatelessWidget {
  const SchemaTablesApp({super.key, this.state, this.tables});

  /// 指定的演示状态；为空时读取编译期 `DEMO_STATE`。
  final SchemaTablesDemoState? state;

  /// 指定的表记录；为空时使用演示数据。
  final List<PgTable>? tables;

  // [p00-001/R1] 首页固定为单 schema 表列表页，不再挂载模板计数器。
  @override
  Widget build(BuildContext context) {
    final resolvedState =
        state ?? demoStateFrom(const String.fromEnvironment('DEMO_STATE'));
    return MaterialApp(
      title: 'PostgreSQL 结构浏览器',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      home: SchemaTablesPage(
        connectionName: demoConnectionName,
        databaseName: demoDatabaseName,
        schemaName: demoSchemaName,
        state: _pageState(resolvedState),
      ),
    );
  }

  SchemaTablesState _pageState(SchemaTablesDemoState resolvedState) {
    return switch (resolvedState) {
      SchemaTablesDemoState.loading => const SchemaTablesLoading(),
      SchemaTablesDemoState.error => const SchemaTablesFailed(demoFailure),
      SchemaTablesDemoState.empty => const SchemaTablesLoaded(<PgTable>[]),
      SchemaTablesDemoState.data => SchemaTablesLoaded(tables ?? demoPgTables),
    };
  }
}
