"""Environment for JSE execution."""

from pyjse.types import JseValue


class Env:
    """Base environment for JSE execution. Can be extended to mount knowledge/statement data."""

    def resolve(self, symbol: str) -> JseValue | None:
        """Resolve symbol to value. Override to provide bindings."""
        return None


class ExpressionEnv(Env):
    """Expression-only environment for basic and logic evaluation."""

    pass
