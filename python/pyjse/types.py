"""JSE (JSON Structural Expression) value types."""

from typing import Any

JseValue = dict[str, Any] | list[Any] | str | int | float | bool | None
