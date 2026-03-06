"""Base AST node class for JSE.

Following the design in docs/regular.md:
- AST nodes contain env (passed during construction)
- AST nodes have get_env() method
- AST nodes have apply() method (execution)
- The two-env pattern (construct-time vs call-time) enables static scoping
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from pyjse.types import JseValue

from pyjse.env import Env

class AstNode(ABC):
    """Base class for all JSE AST nodes.

    Each AST node stores its construct-time environment (_env), which is
    used for implementing closures with static scoping. When the node is
    executed via apply(), a call-time environment is passed in.

    This two-env pattern is key to achieving lexical scoping:
    - Construct-time env: Captured when node is created (for closures)
    - Call-time env: Passed during execution (for parameters, etc.)
    """

    def __init__(self, env: Optional[Env] = None) -> None:
        """Initialize AST node with construct-time environment.

        Args:
            env: The environment in which this node was constructed.
                This is captured for closures (static scoping).
        """
        self._env = env

    def get_env(self) -> 'Env':
        """Get the construct-time environment of this node.

        For closures, this returns the captured environment.

        Returns:
            The environment this node was constructed with.
        """
        return self._env

    @abstractmethod
    def apply(self, env: 'Env', *args: JseValue) -> JseValue:
        """Execute this AST node with the given call-time environment.

        Args:
            env: The environment during execution (call-time scope).
                This may be different from get_env() for closures.

        Returns:
            The result of executing this node.
        """
        pass
