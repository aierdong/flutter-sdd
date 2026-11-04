// spec: support
// layer: core
// covers: none

/// 界面间距 token（UI-02）。只有四档，界面引用常量，不写字面量。
final class AppSpacing {
  const AppSpacing._();

  /// 图标与文字之间、徽标内边距。
  static const double space1 = 4;

  /// 行内元素、按钮组、面板内边距。
  static const double space2 = 8;

  /// 面板内边距上限。
  static const double space3 = 12;

  /// 区域内容与分隔线之间。
  static const double space4 = 16;
}
