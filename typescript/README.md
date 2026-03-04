# JSE 解释环境 - TypeScript 版

JSE（JSON 结构化表达式）的 TypeScript 实现，与 Python 子目录中的实现相对应。

## 功能

- **基础表达式**：字面量（数字、字符串、布尔、null、数组、对象）
- **逻辑运算**：`$and`、`$or`、`$not`
- **引用**：`$quote` 不做求值直接返回
- **转义**：`$$` 表示字面量 `$`
- **查询**：`$expr`、`$pattern`、`$query` 生成 SQL

## 安装

```bash
npm install
```

## 构建与测试

```bash
npm run build
npm test
```

## 使用示例

```typescript
import { Engine, ExpressionEnv } from "jse-engine";

const engine = new Engine(new ExpressionEnv());

// 基础表达式
engine.execute(42);           // 42
engine.execute([1, 2, 3]);   // [1, 2, 3]

// 逻辑运算
engine.execute(["$and", true, true, false]);  // false
engine.execute(["$or", false, true]);        // true

// $quote 引用
engine.execute(["$quote", { foo: "bar" }]);   // { foo: "bar" }

// 查询模式
engine.execute({
  $expr: ["$pattern", "$*", "author of", "$*"]
});  // 返回 SQL 字符串
```

## 项目结构

```
typescript/
├── src/
│   ├── engine.ts    # 核心解释器
│   ├── env.ts       # 环境抽象
│   ├── sql.ts       # SQL 生成
│   ├── types.ts     # 类型定义
│   ├── index.ts     # 导出
│   └── __tests__/   # 单元测试
├── package.json
├── tsconfig.json
└── vitest.config.ts
```
