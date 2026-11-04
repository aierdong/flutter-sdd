// spec: support
// layer: core
// covers: none

/// 集中错误码表（FSD-08）。`FSD-` 字面量只允许出现在本文件与测试断言里。
final class FailureCodes {
  const FailureCodes._();

  /// 读取表列表失败。
  static const String tableLoadFailed = 'FSD-TABLE-001';
}
