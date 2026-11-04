// spec: support
// layer: core
// covers: none

/// 唯一失败类型（FSD-08）。消息与错误码用于界面文案，cause 不进入界面。
final class AppFailure implements Exception {
  const AppFailure({required this.code, required this.message, this.cause});

  /// 集中码表里的错误码，格式 `FSD-<AREA>-<NNN>`。
  final String code;

  /// 面向用户的中文消息，不含错误码本身。
  final String message;

  /// 驱动异常等原始原因。只供日志与排查使用，不得进入界面文案。
  final Object? cause;

  @override
  String toString() => 'AppFailure($code)';
}
