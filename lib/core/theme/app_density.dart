// spec: support
// layer: core
// covers: none

import 'package:flutter/painting.dart';

/// 行高与字号 token（UI-03），另加本页页头高度。
final class AppDensity {
  const AppDensity._();

  /// 树节点、表格行与工具按钮的高度。
  static const double rowHeight = 28;

  /// 顶部工具栏高度。本页页头按 plan 第 2.1 节覆盖为 [pageHeaderHeight]。
  static const double toolbarHeight = 36;

  /// 底部状态栏高度。
  static const double statusBarHeight = 24;

  /// 正文字号。
  static const double bodyFontSize = 12;

  /// 次要文本（路径、类型、计数）字号。
  static const double secondaryFontSize = 11;

  /// 区域标题字号。
  static const double regionTitleFontSize = 12;

  /// 区域标题字重。
  static const FontWeight regionTitleWeight = FontWeight.w600;

  /// 本页页头高度。仅本页生效，其余工具栏仍用 [toolbarHeight]。
  static const double pageHeaderHeight = 56;
}
