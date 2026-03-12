"""Environment for JSE execution.

Follows the design in docs/regular.md:
- env has nullable parent field for scope chain lookup
- env provides register() method for def/defn
- env provides load() method for functor modules
- env.eval() delegates to ast.apply() (following jisp pattern)
"""

from typing import Optional, Any, TYPE_CHECKING
from pyjse.types import JseValue

if TYPE_CHECKING:
    from pyjse.ast.base import AstNode


class Env:
    """Environment for JSE execution with scope chaining.

    Attributes:
        _parent: Parent environment for scope chain (nullable)
        _bindings: Local symbol bindings
        _current_meta: Current metadata context for functor calls
    """

    def __init__(self, parent: Optional['Env'] = None) -> None:
        """Initialize environment with optional parent.

        Args:
            parent: Parent environment for scope chain lookup.
                    None means no parent (e.g., for isolated closures).
        """
        self._parent: Optional[Env] = parent
        self._bindings: dict[str, JseValue] = {}
        self._current_meta: dict[str, JseValue] = {}

    def get_parent(self) -> Optional['Env']:
        """Get parent environment."""
        return self._parent

    def get_meta(self) -> dict[str, JseValue]:
        """Get current metadata context.

        Returns:
            Current metadata dictionary
        """
        return self._current_meta

    def set_meta(self, meta: dict[str, JseValue] | None) -> None:
        """Set current metadata context (before functor call).

        Args:
            meta: Metadata dictionary to set
        """
        self._current_meta = meta if meta is not None else {}

    def clear_meta(self) -> None:
        """Clear current metadata context (after functor call)."""
        self._current_meta = {}

    def resolve(self, symbol: str) -> JseValue | None:
        """Resolve symbol to value by searching up the scope chain.

        If symbol is not found in current environment, searches parent.
        Returns None if symbol is not found anywhere in the chain.

        Args:
            symbol: The symbol name to resolve (e.g., "$x")

        Returns:
            The bound value, or None if not found.
        """
        if symbol in self._bindings:
            return self._bindings[symbol]
        if self._parent:
            return self._parent.resolve(symbol)
        return None

    def register(self, name: str, value: JseValue) -> None:
        """Register a new symbol binding in the current environment.

        Throws if symbol already exists in current scope.
        Used by $def and $defn operators.

        Args:
            name: Symbol name to register
            value: Value to bind to the symbol

        Raises:
            ValueError: If symbol already exists in current scope
        """
        if name in self._bindings:
            raise ValueError(f"Symbol '{name}' already exists in current scope")
        self._bindings[name] = value

    def set(self, name: str, value: JseValue) -> None:
        """Set a symbol binding, overwriting if exists.

        Unlike register(), this allows overwriting existing bindings.

        Args:
            name: Symbol name to set
            value: Value to bind to the symbol
        """
        self._bindings[name] = value

    def exists(self, name: str) -> bool:
        """Check if symbol exists in current or parent scopes.

        Args:
            name: Symbol name to check

        Returns:
            True if symbol exists in scope chain, False otherwise
        """
        if name in self._bindings:
            return True
        if self._parent:
            return self._parent.exists(name)
        return False

    def eval(self, expr: JseValue) -> JseValue:
        """Evaluate an expression in this environment.

        If expr is an AstNode, delegates to expr.apply(self).
        Otherwise returns expr as-is (for primitive values).

        This follows the jisp pattern where env.eval() delegates to ast.apply().

        Args:
            expr: Expression to evaluate

        Returns:
            Evaluated result
        """
        # Avoid circular import by checking type
        if hasattr(expr, 'apply') and callable(getattr(expr, 'apply', None)):
            # This is an AstNode - delegate to its apply method
            return expr.apply(self)  # type: ignore
        # Primitive value - return as-is
        return expr

    def load(self, module: dict) -> None:
        """Load a functor module into this environment.

        Args:
            module: A dictionary of functor names and their implementations

        Raises:
            ValueError: If module name is unknown
        """
        for name, functor in module.items():
            self.register(name, functor)


class ExpressionEnv(Env):
    """Expression-only environment for basic and logic evaluation.

    Can be extended to mount knowledge/statement data.
    """

    pass
