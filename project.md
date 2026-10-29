# project.md

本文件描述项目本身。开发流程见 [AGENTS.md](AGENTS.md)，项目知识索引见 [steering.md](steering.md)。

## 目标

一个 Flutter 桌面应用，只读浏览 PostgreSQL 的库结构：

- 连接一个数据库，枚举其全部 schema，再取每个 schema 下的表。
- database / schema / table 组成一棵可展开的树。
- 选中表后可查看：表名、字段列表、约束、外键。
- 允许刷新某个表的详情信息（表可能在查看期间修改）。

它存在的目的是验证自定义的 SDD 流程，不是生产应用。取舍顺序：流程可验证 > 功能完整 > 健壮性与性能。

## 约束

- 对目标库只读，不写入、不修改。
- 连接串与密码不进入仓库、日志或错误信息。

## 技术栈

- Flutter / Dart（桌面端）
- PostgreSQL（只读元数据）

## 工程命令

应用创建后统一使用：

```bash
flutter analyze
flutter test
```

## 阶段

当前阶段：`p00`（流程验证与最小可用版本）。第一个 spec 建议：连接 → 树 → 表详情。
