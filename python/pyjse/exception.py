class JseException(Exception):
    """Base class for JSE exceptions."""
    pass

class JseSyntaxError(JseException):
    """Syntax error in JSE code."""
    pass

class JseRuntimeError(JseException):
    """Runtime error in JSE code."""
    pass

