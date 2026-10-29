# flutter-sdd

只读浏览 PostgreSQL 库结构的 Flutter 桌面应用，支持 macOS 与 Windows。

- 显示名称：`flutter-sdd`
- Dart 包名：`flutter_sdd`（Dart 包名不允许连字符）
- 项目目标与范围见 [project.md](project.md)，开发流程见 [AGENTS.md](AGENTS.md)。

## 开发命令

```bash
flutter pub get
flutter analyze
flutter test
flutter run -d macos      # 或 -d windows（需在 Windows 上执行）
```

## 构建

```bash
flutter build macos
flutter build windows     # 需在 Windows 上执行
```
