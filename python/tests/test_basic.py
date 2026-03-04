import pytest
from pyjse import Engine, ExpressionEnv


@pytest.fixture
def engine():
    env = ExpressionEnv()
    return Engine(env)


def test_number_expr(engine):
    assert engine.execute(42) == 42


def test_float_expr(engine):
    assert engine.execute(3.14) == 3.14


def test_string_expr(engine):
    assert engine.execute("hello") == "hello"


def test_boolean_expr(engine):
    assert engine.execute(True) is True
    assert engine.execute(False) is False


def test_null_expr(engine):
    assert engine.execute(None) is None


def test_array_expr(engine):
    result = engine.execute([1, 2, 3])
    assert isinstance(result, list)
    assert result == [1, 2, 3]


def test_dict_expr(engine):
    result = engine.execute({"a": 1, "b": "x"})
    assert isinstance(result, dict)
    assert result == {"a": 1, "b": "x"}
