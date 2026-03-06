"""Utility functors for JSE.

Following docs/regular.md utils section:
- $not: Logical negation
- $list?/$map?/$null?: Type predicates
- $get/$set/$del: Container operations
- $conj: Append to list (Clojure-style)
"""

from typing import Callable, TYPE_CHECKING
from pyjse.types import JseValue

if TYPE_CHECKING:
    from pyjse.env import Env


# Type alias for functors
Functor = Callable[['Env', ...], JseValue]


def _not(env: 'Env', *args: JseValue) -> JseValue:
    """Logical negation.

    Args:
        env: Environment
        *args: Optional argument to negate

    Returns:
        Negation of argument (True if no argument or falsy)
    """
    if not args:
        return True
    value = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    return not bool(value)


def _listp(env: 'Env', *args: JseValue) -> JseValue:
    """Check if value is a list.

    Args:
        env: Environment
        *args: One argument to check

    Returns:
        True if value is a list, False otherwise
    """
    if not args:
        return False
    value = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    return isinstance(value, list)


def _mapp(env: 'Env', *args: JseValue) -> JseValue:
    """Check if value is a map (dict).

    Args:
        env: Environment
        *args: One argument to check

    Returns:
        True if value is a dict, False otherwise
    """
    if not args:
        return False
    value = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    return isinstance(value, dict)


def _nullp(env: 'Env', *args: JseValue) -> JseValue:
    """Check if value is null.

    Distinguishes null from false (unlike classic Lisp).

    Args:
        env: Environment
        *args: One argument to check

    Returns:
        True if value is None, False otherwise
    """
    if not args:
        return True
    value = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    return value is None


def _get(env: 'Env', *args: JseValue) -> JseValue:
    """Get value from map or list by key/index.

    Args:
        env: Environment
        *args: (collection, key) arguments

    Returns:
        Value at key/index, or None if not found (for maps)

    Raises:
        ValueError: If wrong number of args or wrong types
    """
    if len(args) < 2:
        raise ValueError("$get requires (collection, key) arguments")

    collection = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    key = env.eval(args[1]) if hasattr(env, 'eval') else args[1]

    if isinstance(collection, dict):
        return collection.get(key)
    if isinstance(collection, list):
        if not isinstance(key, int):
            raise ValueError("$get on list requires integer index")
        if key < 0 or key >= len(collection):
            raise IndexError(f"Index {key} out of range for list of length {len(collection)}")
        return collection[key]

    raise ValueError("$get first argument must be map or list")


def _set(env: 'Env', *args: JseValue) -> JseValue:
    """Set value in map or list (mutates).

    Args:
        env: Environment
        *args: (collection, key, value) arguments

    Returns:
        The modified collection

    Raises:
        ValueError: If wrong number of args or wrong types
    """
    if len(args) < 3:
        raise ValueError("$set requires (collection, key, value) arguments")

    collection = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    key = env.eval(args[1]) if hasattr(env, 'eval') else args[1]
    value = env.eval(args[2]) if hasattr(env, 'eval') else args[2]

    if isinstance(collection, dict):
        collection[key] = value
        return collection
    if isinstance(collection, list):
        if not isinstance(key, int):
            raise ValueError("$set on list requires integer index")
        if key < 0 or key >= len(collection):
            raise IndexError(f"Index {key} out of range for list of length {len(collection)}")
        collection[key] = value
        return collection

    raise ValueError("$set first argument must be map or list")


def _del(env: 'Env', *args: JseValue) -> JseValue:
    """Delete key from map or index from list (mutates).

    Args:
        env: Environment
        *args: (collection, key) arguments

    Returns:
        The modified collection

    Raises:
        ValueError: If wrong number of args or wrong types
    """
    if len(args) < 2:
        raise ValueError("$del requires (collection, key) arguments")

    collection = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    key = env.eval(args[1]) if hasattr(env, 'eval') else args[1]

    if isinstance(collection, dict):
        if key not in collection:
            raise KeyError(f"Key '{key}' not found in map")
        del collection[key]
        return collection
    if isinstance(collection, list):
        if not isinstance(key, int):
            raise ValueError("$del on list requires integer index")
        if key < 0 or key >= len(collection):
            raise IndexError(f"Index {key} out of range for list of length {len(collection)}")
        del collection[key]
        return collection

    raise ValueError("$del first argument must be map or list")


def _conj(env: 'Env', *args: JseValue) -> JseValue:
    """Conjoin element to end of list (Clojure-style).

    Note: This appends (unlike $cons which prepends).

    Args:
        env: Environment
        *args: Exactly 2 arguments (element, list)

    Returns:
        New list with element appended

    Raises:
        ValueError: If not exactly 2 arguments or second not a list
    """
    if len(args) != 2:
        raise ValueError("$conj requires exactly 2 arguments")

    elem = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    lst = env.eval(args[1]) if hasattr(env, 'eval') else args[1]

    if not isinstance(lst, list):
        raise ValueError("$conj second argument must be a list")

    return lst + [elem]

def _and(env: 'Env', *args: JseValue) -> JseValue:
    """Logical AND.

    Args:
        env: Environment
        *args: Arguments to AND
    """
    return all(args)

def _or(env: 'Env', *args: JseValue) -> JseValue:
    """Logical OR.

    Args:
        env: Environment
        *args: Arguments to OR
    """
    return any(args)

def _eq(env: 'Env', *args: JseValue) -> JseValue:
    """Logical EQ.

    如果参数数量
    - 1个参数，返回 True
    - 2个参数，返回两个参数是否相等
    - 更多参数，执行全等比较
    
    Args:
        env: Environment
        *args: Arguments to EQ
    """
    if len(args) == 1:
        return True
    if len(args) == 2:
        return args[0] == args[1]
    return all(args[i] == args[i+1] for i in range(len(args)-1))

# Dict of all utility functors for registration
UTILS_FUNCTORS: dict[str, Functor] = {
    "$not": _not,
    "$list?": _listp,
    "$map?": _mapp,
    "$null?": _nullp,
    "$get": _get,
    "$set": _set,
    "$del": _del,
    "$conj": _conj,
    "$and": _and,
    "$or": _or,
}
