"""Run mode: under an IDE debugger or in production.

Two things depend on it — whether the browser window is shown, and whether a page dump
is printed when a wait times out. Both are for a human at the keyboard and get in the
way of an ordinary run.
"""
import sys


def is_debug() -> bool:
    """A debugger sets a trace function, and PyCharm also loads pydevd."""
    return sys.gettrace() is not None or "pydevd" in sys.modules
