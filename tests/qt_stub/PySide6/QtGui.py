from PySide6._core import Any, make


def __getattr__(name):
    return make(name)
