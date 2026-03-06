"""LISP-enhanced functors for JSE.

Following docs/regular.md lisp section:
- $apply: Apply functor to argument list
- $eval: Evaluate expression
- $lambda: Create lambda function with closure
- $def: Define symbol in current environment
- $defn: Define named function (def + lambda syntax sugar)
"""

from typing import Callable, TYPE_CHECKING
from pyjse.types import JseValue
from pyjse.ast.nodes import LambdaNode

if TYPE_CHECKING:
    from pyjse.env import Env


# Type alias for functors
Functor = Callable[['Env', ...], JseValue]


def _apply(env: 'Env', *args: JseValue) -> JseValue:
    """Apply functor to argument list.

    Args:
        env: Environment
        *args: (functor, arglist) arguments

    Returns:
        Result of applying functor to args

    Raises:
        ValueError: If wrong number or types of arguments
    """
    if len(args) < 2:
        raise ValueError("$apply requires (functor, arglist) arguments")

    functor = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    arglist = env.eval(args[1]) if hasattr(env, 'eval') else args[1]

    if not isinstance(arglist, list):
        raise ValueError("$apply second argument must be a list")

    if not callable(functor):
        raise ValueError("$apply first argument must be callable")

    return functor(env, *arglist)


def _eval_expr(env: 'Env', *args: JseValue) -> JseValue:
    """Evaluate an expression.

    Args:
        env: Environment
        *args: One expression to evaluate

    Returns:
        Result of evaluation

    Raises:
        ValueError: If no argument
    """
    if not args:
        raise ValueError("$eval requires an expression argument")

    return env.eval(args[0])


def _lambda(env: 'Env', *args: JseValue) -> JseValue:
    """Create a lambda function with closure.

    Captures current environment for static scoping.
    Form: [$lambda, params, body]
    where params is a list of parameter symbols (unevaluated).

    Args:
        env: Environment (captured as closure)
        *args: (params, body) arguments - unevaluated AST nodes

    Returns:
        LambdaNode that can be applied

    Raises:
        ValueError: If wrong arguments or invalid params
    """
    if len(args) < 2:
        raise ValueError("$lambda requires (params, body) arguments")

    params_expr = args[0]
    body = args[1] if len(args) > 1 else None

    # Extract parameter names from potentially unevaluated expression
    # params_expr could be: ArrayNode (list), SymbolNode (symbol), or already evaluated list
    if hasattr(params_expr, '_elements'):
        # ArrayNode - extract elements
        params = params_expr._elements
    elif hasattr(params_expr, '_name'):
        # SymbolNode - single parameter (rare but valid)
        params = [params_expr]
    elif isinstance(params_expr, list):
        # Already evaluated list
        params = params_expr
    else:
        raise ValueError("$lambda first argument must be a parameter list")

    param_names: list[str] = []
    for p in params:
        # p could be SymbolNode or string
        if hasattr(p, '_name'):
            # SymbolNode - extract name
            name = p._name
        elif isinstance(p, str):
            name = p
        else:
            raise ValueError(f"$lambda parameters must be symbols, got: {type(p)}")

        if not name.startswith("$"):
            raise ValueError(f"$lambda parameters must be symbols starting with $, got: {name}")
        param_names.append(name)

    # Create lambda with current environment as closure (static scoping!)
    return LambdaNode(param_names, body, env)


def _def(env: 'Env', *args: JseValue) -> JseValue:
    """Define a symbol in current environment.

    Form: [$def, name, value]
    where name can be a SymbolNode or a string symbol (unevaluated).

    Args:
        env: Environment to register in
        *args: (name, value) arguments - unevaluated AST nodes

    Returns:
        The defined value

    Raises:
        ValueError: If wrong arguments or invalid name
    """
    if len(args) != 2:
        raise ValueError("$def requires (name, value) arguments")

    name_expr = args[0]
    value_expr = args[1]

    # Extract name - can be SymbolNode or string
    if hasattr(name_expr, '_name'):
        # SymbolNode - extract name directly
        name = name_expr._name
    elif isinstance(name_expr, str):
        if not name_expr.startswith("$"):
            raise ValueError("$def first argument must be a symbol starting with $")
        name = name_expr
    else:
        raise ValueError("$def first argument must be a symbol or string")

    # Evaluate the value expression
    value = env.eval(value_expr) if hasattr(env, 'eval') else value_expr

    env.register(name, value)
    return value


def _defn(env: 'Env', *args: JseValue) -> JseValue:
    """Define a named function.

    Syntactic sugar for: [$def, name, [$lambda, params, body]]

    Form: [$defn, name, params, body]
    where name can be a SymbolNode or a string symbol (unevaluated).

    Args:
        env: Environment
        *args: (name, params, body) arguments - unevaluated AST nodes

    Returns:
        The defined lambda function

    Raises:
        ValueError: If wrong arguments or invalid name
    """
    if len(args) < 3:
        raise ValueError("$defn requires (name, params, body) arguments")

    name_expr = args[0]
    params_expr = args[1]
    body = args[2] if len(args) > 2 else None

    # Extract name - can be SymbolNode or string
    if hasattr(name_expr, '_name'):
        # SymbolNode - extract name directly
        name = name_expr._name
    elif isinstance(name_expr, str):
        if not name_expr.startswith("$"):
            raise ValueError("$defn first argument must be a symbol starting with $")
        name = name_expr
    else:
        raise ValueError("$defn first argument must be a symbol or string")

    # Create lambda using _lambda functor
    lambda_fn = _lambda(env, params_expr, body)

    # Register it
    env.register(name, lambda_fn)
    return lambda_fn


# Dict of all LISP functors for registration
LISP_FUNCTORS: dict[str, Functor] = {
    "$apply": _apply,
    "$eval": _eval_expr,
    "$lambda": _lambda,
    "$def": _def,
    "$defn": _defn,
}
