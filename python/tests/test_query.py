from pyjse import Engine, Env, QUERY_FIELDS


def test_basic_query():
    query = {"$expr": ["$pattern", "$*", "author of", "$*"]}

    env = Env()
    engine = Engine(env)
    result = engine.execute(query)

    assert "select" in result
    assert "subject, predicate, object, meta" in result
    assert "from statement as s" in result
    assert "author of" in result
    assert "triple" in result
    assert "offset 0" in result
    assert "limit 100" in result


def test_combined_query():
    query = {
        "$query": [
            "$and",
            [
                ["$pattern", "Liu Xin", "author of", "$*"],
                ["$pattern", "$*", "author of", "$*"],
            ],
        ]
    }

    env = Env()
    engine = Engine(env)
    result = engine.execute(query)

    assert f"select {QUERY_FIELDS}" in result
    assert "from statement" in result
    assert "Liu Xin" in result
    assert "author of" in result
    assert " and " in result
    assert "offset 0" in result
    assert "limit 100" in result
