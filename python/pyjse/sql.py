"""SQL generation for JSE query patterns."""

QUERY_FIELDS = "subject, predicate, object, meta"


def pattern_to_triple(subject: str, predicate: str, object_: str) -> list:
    """Convert $pattern args to triple for PostgreSQL jsonb containment."""
    if subject == "$*" and object_ == "$*":
        return [predicate]
    return [subject, predicate, object_]


def triple_to_sql_condition(triple: list) -> str:
    """Build SQL WHERE clause for a triple pattern."""
    import json

    doc = json.dumps({"triple": triple})
    escaped = doc.replace("'", "''")
    return f"meta @> '{escaped}'"
