"""Basic builtin functors for JSE.

Following docs/regular.md basic operators section:
- $quote: Quote unevaluated expression
- $eq: Equality comparison
- $cond: Multi-branch conditional
- $head/$tail: List car/cdr operations
- $atom?: Check if value is JSON atom type
- $cons: Construct list (Clojure-style)
"""

from typing import Callable, TYPE_CHECKING
from pyjse.types import JseValue

if TYPE_CHECKING:
    from pyjse.env import Env


# Type alias for functors
Functor = Callable[['Env', ...], JseValue]


def _quote(env: 'Env', *args: JseValue) -> JseValue:
    """Return argument without evaluation.

    Args:
        env: Environment
        *args: Arguments (returns first or None)

    Returns:
        First argument or None
    """
    return args[0] if args else None


def _eq(env: 'Env', *args: JseValue) -> JseValue:
    """Compare two values for equality.

    Args:
        env: Environment
        *args: Exactly 2 arguments to compare

    Returns:
        True if equal, False otherwise

    Raises:
        ValueError: If not exactly 2 arguments
    """
    if len(args) != 2:
        raise ValueError("$eq requires exactly 2 arguments")
    return args[0] == args[1]


def _cond(env: 'Env', *args: JseValue) -> JseValue:
    """Multi-branch conditional evaluation.

    Forms:
    - [$cond, test1, result1, test2, result2, ...]
    - [$cond, test1, result1, test2, result2, ..., default]

    Args:
        env: Environment for evaluating tests and results
        *args: Alternating test/result pairs, optional default

    Returns:
        First result whose test is truthy, or default, or None
    """
    if not args:
        return None

    if len(args) % 2 == 0:
        # Pairs only: [test1, result1, test2, result2, ...]
        pairs = list(zip(args[::2], args[1::2]))
        default = None
    else:
        # With default: [test1, result1, ..., default]
        pairs = list(zip(args[:-1:2], args[1:-1:2]))
        default = args[-1]

    for test, result in pairs:
        if env.eval(test):
            return env.eval(result)

    return env.eval(default) if default is not None else None


def _head(env: 'Env', *args: JseValue) -> JseValue:
    """Get first element of list (car).

    Args:
        env: Environment
        *args: One argument - the list

    Returns:
        First element of list

    Raises:
        ValueError: If no argument or not a list
    """
    if not args:
        raise ValueError("$head requires a list argument")

    lst = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    if not isinstance(lst, list):
        raise ValueError("$head requires a list argument")
    if not lst:
        raise ValueError("$head requires non-empty list")

    return lst[0]


def _tail(env: 'Env', *args: JseValue) -> JseValue:
    """Get rest of list (cdr).

    Args:
        env: Environment
        *args: One argument - the list

    Returns:
        List without first element (empty list if single element)

    Raises:
        ValueError: If no argument or not a list
    """
    if not args:
        raise ValueError("$tail requires a list argument")

    lst = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    if not isinstance(lst, list):
        raise ValueError("$tail requires a list argument")

    return lst[1:] if len(lst) > 1 else []


def _atomp(env: 'Env', *args: JseValue) -> JseValue:
    """Check if value is a JSON atom type.

    Atoms are: number, string, boolean, null

    Args:
        env: Environment
        *args: One argument to check

    Returns:
        True if atom, False otherwise

    Raises:
        ValueError: If no argument
    """
    if not args:
        raise ValueError("$atom? requires an argument")

    value = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    return value is None or isinstance(value, (int, float, bool, str))


def _cons(env: 'Env', *args: JseValue) -> JseValue:
    """Conjoin element and list (Clojure-style).

    First argument: any element
    Second argument: must be a list
    Returns: new list with element prepended

    Args:
        env: Environment
        *args: Exactly 2 arguments (element, list)

    Returns:
        New list [element, ...list]

    Raises:
        ValueError: If not exactly 2 arguments or second not a list
    """
    if len(args) != 2:
        raise ValueError("$cons requires exactly 2 arguments")

    elem = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    lst = env.eval(args[1]) if hasattr(env, 'eval') else args[1]

    if not isinstance(lst, list):
        raise ValueError("$cons second argument must be a list")

    return [elem] + lst


# Dict of all builtin functors for registration
BUILTIN_FUNCTORS: dict[str, Functor] = {
    "$quote": _quote,
    "$eq": _eq,
    "$cond": _cond,
    "$head": _head,
    "$tail": _tail,
    "$atom?": _atomp,
    "$cons": _cons,
}
