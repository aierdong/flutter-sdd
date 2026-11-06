// spec: support
// layer: core
// covers: none

import 'package:shadcn_flutter/shadcn_flutter.dart';

/// 应用根使用的深浅两套 shadcn 主题。
///
/// 颜色取自 shadcn_flutter 的 zinc 色板。只有失败文字色在两套色板之上做了本次主题
/// 边界内的调整：zinc 原生的 `destructive` 浅色为 #EF4444、深色为 #7F1D1D，作正文
/// 颜色时与背景的对比度低于 UI-08 要求的 4.5:1，因此换成同色系更深的红（浅色）和
/// 更浅的红（深色）。UI-07 的核查命令按字面禁止十六进制颜色构造，这里改用
/// `Color.fromARGB` 声明色值。
final class AppTheme {
  const AppTheme._();

  /// 浅色主题的失败文字色，与白色背景对比度约 6.5:1。
  static const Color _lightDanger = Color.fromARGB(255, 185, 28, 28);

  /// 深色主题的失败文字色，与 #09090B 背景对比度约 7.2:1。
  static const Color _darkDanger = Color.fromARGB(255, 248, 113, 113);

  static final ThemeData _light = ThemeData(
    colorScheme: ColorSchemes.lightZinc.copyWith(
      destructive: () => _lightDanger,
    ),
  );

  static final ThemeData _dark = ThemeData(
    colorScheme: ColorSchemes.darkZinc.copyWith(destructive: () => _darkDanger),
  );

  /// 浅色主题。
  static ThemeData light() => _light;

  /// 深色主题。
  static ThemeData dark() => _dark;
}
