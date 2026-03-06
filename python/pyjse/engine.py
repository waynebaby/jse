"""JSE execution engine with AST-based architecture.

Following the design in docs/regular.md:
- Engine uses Parser to convert JSON to AST
- AST nodes are evaluated via env.eval() -> ast.apply()
- Supports static scoping through closure environments
"""

from pyjse.env import Env
from pyjse.ast.parser import Parser
from pyjse.types import JseValue


class Engine:
    """JSE expression interpreter with AST-based execution.

    The engine parses JSON expressions into AST nodes, then evaluates
    them using the environment's eval() method (which delegates to
    each AST node's apply() method).

    This architecture enables:
    - Static scoping (closures capture construct-time environment)
    - Proper separation of parsing and evaluation
    - Modular functor loading via env.load()
    """

    def __init__(self, env: Env) -> None:
        """Initialize engine with environment.

        Args:
            env: Environment for execution. Should have functors loaded
                 via env.load() before executing expressions.
        """
        self.env = env
        self._parser = Parser(env)

    def execute(self, expr: JseValue) -> JseValue:
        """Execute a JSE expression.

        Parses the expression into an AST, then evaluates it using
        the environment's eval() method.

        Args:
            expr: JSON expression to execute

        Returns:
            Result of evaluation
        """
        # Parse into AST
        ast = self._parser.parse(expr)

        # Evaluate using environment (delegates to ast.apply())
        return self.env.eval(ast)
