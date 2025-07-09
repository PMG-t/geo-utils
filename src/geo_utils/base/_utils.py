import os

_USE_EXCEPTIONS: bool = True

def try_default(f: callable, args: tuple = (), kwargs: dict = {}, default: any = None) -> any:
    """
    Attempts to call a function and returns a default value if it fails.

    Args:
        f (callable): The function to call.
        default (any): The value to return if the function call fails.

    Returns:
        any: The result of the function call or the default value.
    """
    try:
        return f(*args, **kwargs)
    except Exception:
        return default