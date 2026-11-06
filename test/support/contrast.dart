// spec: support
// layer: test
// covers: none

import 'dart:math' as math;

import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shadcn_flutter/shadcn_flutter.dart';

/// 读取一段文本渲染后的实际前景色。
Color renderedTextColor(WidgetTester tester, Finder text) {
  final RenderParagraph paragraph = tester.renderObject<RenderParagraph>(text);
  final Color? color = paragraph.text.style?.color;
  expect(color, isNotNull, reason: '文本没有使用显式前景色，无法核对对比度');
  return color!;
}

/// 读取一段文本所在单元格或页面区域的实际背景色（最近的、有实色的祖先容器）。
Color renderedBackgroundColor(WidgetTester tester, Finder text) {
  final Finder containers = find.ancestor(
    of: text,
    matching: find.byType(ColoredBox),
  );
  for (final Element element in containers.evaluate()) {
    final Color color = (element.widget as ColoredBox).color;
    if (color.a == 1) {
      return color;
    }
  }
  fail('找不到文本所在的不透明背景');
}

/// WCAG 2.x 相对亮度。
double relativeLuminance(Color color) {
  double channel(double value) {
    return value <= 0.03928
        ? value / 12.92
        : math.pow((value + 0.055) / 1.055, 2.4).toDouble();
  }

  return 0.2126 * channel(color.r) +
      0.7152 * channel(color.g) +
      0.0722 * channel(color.b);
}

/// 按 sRGB 相对亮度计算两色的对比度，结果在 1 到 21 之间。
double contrastRatio(Color foreground, Color background) {
  final double first = relativeLuminance(foreground);
  final double second = relativeLuminance(background);
  final double lighter = math.max(first, second);
  final double darker = math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

/// 核对一段文本与其所在背景的对比度不低于 [minimum]。
void expectTextContrast(
  WidgetTester tester,
  Finder text, {
  required String label,
  double minimum = 4.5,
}) {
  final Color foreground = renderedTextColor(tester, text);
  final Color background = renderedBackgroundColor(tester, text);
  final double ratio = contrastRatio(foreground, background);
  expect(
    ratio,
    greaterThanOrEqualTo(minimum),
    reason: '$label 的对比度只有 ${ratio.toStringAsFixed(2)}:1',
  );
}
