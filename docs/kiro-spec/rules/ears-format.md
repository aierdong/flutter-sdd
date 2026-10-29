---
translated: true
source: .claude/skills/kiro-spec-requirements/rules/ears-format.md
generated: 2026-10-29
---

# EARS 格式规范

> 本文件是英文原文的中文译本。事实以 `.claude/skills/kiro-spec-requirements/rules/ears-format.md` 为准。

## 概述

EARS（Easy Approach to Requirements Syntax）是规格驱动开发中验收条件的标准写法。

EARS 描述的是需求的逻辑结构（条件 + 主语 + 响应），本身不绑定任何自然语言。所有验收条件都应该用规格配置的目标语言书写（例如 `spec.json.language` / `en`）。

EARS 的触发词和固定短语保留英文（`When`、`If`、`While`、`Where`、`The system shall`、`The [system] shall`），只把变量部分（`[event]`、`[precondition]`、`[trigger]`、`[feature is included]`、`[response/action]`）本地化。**不要把目标语言塞进触发词或固定英文短语内部。**

## 五种基本句式

### 1. 事件驱动型

- **句式**：When [event], the [system] shall [response/action]
- **用途**：对特定事件或触发的响应
- **示例**：When user clicks checkout button, the Checkout Service shall validate cart contents

### 2. 状态驱动型

- **句式**：While [precondition], the [system] shall [response/action]
- **用途**：依赖系统状态或前置条件的行为
- **示例**：While payment is processing, the Checkout Service shall display loading indicator

### 3. 非期望行为型

- **句式**：If [trigger], the [system] shall [response/action]
- **用途**：系统对错误、失败或非期望情况的响应
- **示例**：If invalid credit card number is entered, then the website shall display error message

### 4. 可选特性型

- **句式**：Where [feature is included], the [system] shall [response/action]
- **用途**：可选特性或条件特性
- **示例**：Where the car has a sunroof, the car shall have a sunroof control panel

### 5. 通用型

- **句式**：The [system] shall [response/action]
- **用途**：始终生效的需求和系统基本属性
- **示例**：The mobile phone shall have a mass of less than 100 grams

## 组合句式

- While [precondition], when [event], the [system] shall [response/action]
- When [event] and [additional condition], the [system] shall [response/action]

## 主语选择

- **软件项目**：用具体的系统或服务名（例如 "Checkout Service"、"User Auth Module"）。
- **流程/工作流**：用负责的团队或角色（例如 "Support Team"、"Review Process"）。
- **非软件项目**：用合适的主语（例如 "Marketing Campaign"、"Documentation"）。

## 质量要求

- 需求必须可测试、可验证，且只描述单一行为。
- 用客观措辞：强制行为用 "shall"，建议用 "should"；避免含糊表述。
- 遵循 EARS 句法：`[condition], the [system] shall [response/action]`。
