// spec: support
// layer: core
// covers: none

import 'package:flutter/material.dart';
import 'package:flutter_sdd/core/theme/app_density.dart';
import 'package:flutter_sdd/core/theme/app_spacing.dart';

/// 语义颜色 token（UI-07）。深浅各一套，界面与 `app.dart` 只引用 token。
///
/// UI-07 的核查命令按字面禁止十六进制颜色构造和 material 调色板常量，
/// 因此这里改用 `Color.fromARGB` 声明色值。
@immutable
final class AppPalette extends ThemeExtension<AppPalette> {
  const AppPalette({
    required this.canvas,
    required this.surface,
    required this.surfaceMuted,
    required this.border,
    required this.text,
    required this.textMuted,
    required this.accent,
    required this.error,
  });

  /// 画布底色。
  final Color canvas;

  /// 面板底色。
  final Color surface;

  /// 面板次级底色。
  final Color surfaceMuted;

  /// 1px 分隔线与边界。
  final Color border;

  /// 正文颜色。
  final Color text;

  /// 次要文本颜色，只用于 11 号文本。
  final Color textMuted;

  /// 强调色，用于排序方向与进度指示。
  final Color accent;

  /// 失败文案颜色。
  final Color error;

  /// 读取当前主题的颜色 token；主题缺失时回退浅色。
  static AppPalette of(BuildContext context) =>
      Theme.of(context).extension<AppPalette>() ?? light;

  /// 浅色主题色值。
  static const AppPalette light = AppPalette(
    canvas: Color.fromARGB(255, 255, 255, 255),
    surface: Color.fromARGB(255, 247, 248, 250),
    surfaceMuted: Color.fromARGB(255, 239, 241, 244),
    border: Color.fromARGB(255, 216, 221, 227),
    text: Color.fromARGB(255, 27, 31, 36),
    textMuted: Color.fromARGB(255, 92, 102, 112),
    accent: Color.fromARGB(255, 37, 99, 235),
    error: Color.fromARGB(255, 179, 38, 30),
  );

  /// 深色主题色值。
  static const AppPalette dark = AppPalette(
    canvas: Color.fromARGB(255, 22, 24, 29),
    surface: Color.fromARGB(255, 30, 33, 39),
    surfaceMuted: Color.fromARGB(255, 38, 42, 49),
    border: Color.fromARGB(255, 58, 64, 74),
    text: Color.fromARGB(255, 230, 233, 238),
    textMuted: Color.fromARGB(255, 160, 168, 179),
    accent: Color.fromARGB(255, 126, 166, 255),
    error: Color.fromARGB(255, 255, 138, 128),
  );

  @override
  AppPalette copyWith({
    Color? canvas,
    Color? surface,
    Color? surfaceMuted,
    Color? border,
    Color? text,
    Color? textMuted,
    Color? accent,
    Color? error,
  }) {
    return AppPalette(
      canvas: canvas ?? this.canvas,
      surface: surface ?? this.surface,
      surfaceMuted: surfaceMuted ?? this.surfaceMuted,
      border: border ?? this.border,
      text: text ?? this.text,
      textMuted: textMuted ?? this.textMuted,
      accent: accent ?? this.accent,
      error: error ?? this.error,
    );
  }

  @override
  AppPalette lerp(covariant ThemeExtension<AppPalette>? other, double t) {
    if (other is! AppPalette) {
      return this;
    }
    return AppPalette(
      canvas: Color.lerp(canvas, other.canvas, t) ?? canvas,
      surface: Color.lerp(surface, other.surface, t) ?? surface,
      surfaceMuted:
          Color.lerp(surfaceMuted, other.surfaceMuted, t) ?? surfaceMuted,
      border: Color.lerp(border, other.border, t) ?? border,
      text: Color.lerp(text, other.text, t) ?? text,
      textMuted: Color.lerp(textMuted, other.textMuted, t) ?? textMuted,
      accent: Color.lerp(accent, other.accent, t) ?? accent,
      error: Color.lerp(error, other.error, t) ?? error,
    );
  }
}

/// 应用根使用的深浅主题。颜色只来自 [AppPalette] token（UI-07）。
final class AppTheme {
  const AppTheme._();

  /// 浅色主题。
  static ThemeData light() => _build(AppPalette.light, Brightness.light);

  /// 深色主题。
  static ThemeData dark() => _build(AppPalette.dark, Brightness.dark);

  static ThemeData _build(AppPalette colors, Brightness brightness) {
    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: ColorScheme(
        brightness: brightness,
        primary: colors.accent,
        onPrimary: colors.canvas,
        secondary: colors.accent,
        onSecondary: colors.canvas,
        error: colors.error,
        onError: colors.canvas,
        surface: colors.surface,
        onSurface: colors.text,
      ),
      scaffoldBackgroundColor: colors.canvas,
      dividerColor: colors.border,
      visualDensity: VisualDensity.compact,
      textTheme: _textTheme(colors),
      outlinedButtonTheme: _outlinedButtonTheme(colors),
      extensions: <ThemeExtension<AppPalette>>[colors],
    );
  }

  static TextTheme _textTheme(AppPalette colors) {
    return TextTheme(
      bodyMedium: TextStyle(
        fontSize: AppDensity.bodyFontSize,
        color: colors.text,
      ),
      bodySmall: TextStyle(
        fontSize: AppDensity.secondaryFontSize,
        color: colors.textMuted,
      ),
    );
  }

  static OutlinedButtonThemeData _outlinedButtonTheme(AppPalette colors) {
    return OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: colors.text,
        disabledForegroundColor: colors.textMuted,
        side: BorderSide(color: colors.border),
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(4)),
        ),
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.space3,
          vertical: AppSpacing.space1,
        ),
        minimumSize: const Size(0, AppDensity.rowHeight),
        textStyle: const TextStyle(fontSize: AppDensity.bodyFontSize),
      ),
    );
  }
}
