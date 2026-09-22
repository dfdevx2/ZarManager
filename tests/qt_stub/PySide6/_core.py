class _AnyMeta(type):
    def __getattr__(cls, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return Any(name)


class Any(metaclass=_AnyMeta):
    def __init__(self, *args, **kwargs):
        object.__setattr__(self, "_name", args[0] if args and isinstance(args[0], str) else "")

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _typed_method(name)

    def __call__(self, *args, **kwargs):
        return Any("call")

    def __or__(self, other):  return self
    def __ror__(self, other): return self
    def __and__(self, other): return self
    def __rand__(self, other): return self
    def __invert__(self):     return self
    def __eq__(self, other):  return self is other
    def __ne__(self, other):  return self is not other
    def __hash__(self):       return id(self)
    def __bool__(self):       return True
    def __int__(self):        return 0
    def __index__(self):      return 0
    def __len__(self):        return 0
    def __float__(self):      return 0.0
    def __str__(self):        return f"<stub {object.__getattribute__(self, '_name')}>"
    def __iter__(self):       return iter(())
    def __contains__(self, item): return False
    def __sub__(self, other): return self
    def __add__(self, other): return self
    def __mul__(self, other): return self
    def __truediv__(self, other): return self
    def __lt__(self, other):  return False
    def __gt__(self, other):  return False


def make(name):
    return type(name, (Any,), {})


def __getattr__(name):
    return make(name)


# Métodos do Qt cujo tipo de retorno importa para o código chamador.
_STR = {"text", "toPlainText", "currentText", "objectName", "styleSheet",
        "windowTitle", "toolTip", "placeholderText", "decode"}
_INT = {"count", "currentIndex", "findText", "findData", "value", "elapsed",
        "blockCount", "exec", "maximum", "minimum", "checkedId", "width",
        "height", "horizontalAdvance", "pointSizeF", "result"}
_BOOL_PREFIX = ("is", "has", "can")


class _Member(Any):
    """Serve como enum (suporta +, |, ==) e como método (suporta chamada)."""

    def __call__(self, *args, **kwargs):
        name = object.__getattribute__(self, "_name")
        if name in _STR:
            return ""
        if name in _INT:
            return 0
        if name.startswith(_BOOL_PREFIX):
            return False
        return Any(name)


def _typed_method(name):
    return _Member(name)
