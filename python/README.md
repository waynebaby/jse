# PyJSE

JSE (JSON Structural Expression) 的 Python 实现，可发布至 PyPI。

## 安装

```bash
pip install pyjse
```

开发模式：

```bash
cd python && pip install -e ".[dev]"
```

## 使用

```python
from pyjse import Engine, ExpressionEnv

engine = Engine(ExpressionEnv())

engine.execute(42)                          # 42
engine.execute(["$and", True, True, False])  # False
engine.execute({"$expr": ["$pattern", "$*", "author of", "$*"]})  # SQL 字符串
```

## 开发

```bash
cd python
pip install -e ".[dev]"
pytest
```

## 发布到 PyPI

```bash
cd python
pip install build
python -m build
twine upload dist/*
```
