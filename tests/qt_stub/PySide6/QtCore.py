from PySide6._core import Any, make


def __getattr__(name):
    return make(name)


def Signal(*args, **kwargs):
    return Any("signal")


def Slot(*args, **kwargs):
    def decorator(func):
        return func
    return decorator


def Property(*args, **kwargs):
    return Any("property")
