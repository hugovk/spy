"""
This is NOT the spy "builtins" module.

This contains the basic machinery to build builtin functions and types, for
ALL builtin module. The builtin module whose name is "builtins" reside in
vm/modules/builtins.py.
"""

import inspect
import typing
from typing import TYPE_CHECKING, Any, Callable, Type
from spy.fqn import QN
from spy.ast import Color
from spy.vm.primitive import W_Void
from spy.vm.object import W_Object, W_Type, W_Dynamic, _get_member_maybe, make_metaclass, w_DynamicType
from spy.vm.function import FuncParam, W_FuncType, W_BuiltinFunc
if TYPE_CHECKING:
    from spy.vm.vm import SPyVM


def is_W_class(x: Any) -> bool:
    return isinstance(x, type) and issubclass(x, W_Object)


def to_spy_FuncParam(p: Any) -> FuncParam:
    # we cannot import spy.vm.b due to circular imports, fake it
    B_w_dynamic = w_DynamicType
    if p.name.startswith('w_'):
        name = p.name[2:]
    else:
        name = p.name
    #
    pyclass = p.annotation
    if pyclass is W_Dynamic:
        return FuncParam(name, B_w_dynamic)
    elif issubclass(pyclass, W_Object):
        return FuncParam(name, pyclass._w)
    else:
        raise ValueError(f"Invalid param: '{p}'")


def functype_from_sig(fn: Callable, color: Color) -> W_FuncType:
    # we cannot import spy.vm.b due to circular imports, fake it
    B_w_Void = W_Void._w
    B_w_dynamic = w_DynamicType

    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    if len(params) == 0:
        msg = (f"The first param should be 'vm: SPyVM'. Got nothing")
        raise ValueError(msg)
    if (params[0].name != 'vm' or
        params[0].annotation != 'SPyVM'):
        msg = (f"The first param should be 'vm: SPyVM'. Got '{params[0]}'")
        raise ValueError(msg)

    func_params = [to_spy_FuncParam(p) for p in params[1:]]
    ret = sig.return_annotation
    if ret is None:
        w_restype = B_w_Void
    elif ret is W_Dynamic:
        w_restype = B_w_dynamic
    elif is_W_class(ret):
        w_restype = ret._w
    else:
        raise ValueError(f"Invalid return type: '{sig.return_annotation}'")

    return W_FuncType(func_params, w_restype, color=color)


def builtin_func(qn: QN, color: Color = 'red') -> Callable:
    """
    Decorator to make an interp-level function wrappable by the VM.

    Example of usage:

        @builtin_func(QN("foo::hello"))
        def w_hello(vm: 'SPyVM', w_x: W_I32) -> W_Str:
            ...

        assert isinstance(w_hello, W_BuiltinFunc)
        assert w_hello.qn == QN("foo::hello")

    The w_functype of the wrapped function is automatically computed by
    inspectng the signature of the interp-level function. The first parameter
    MUST be 'vm'.

    Note that the decorator returns a W_BuiltinFunc, which means that you
    cannot call it directly, but you need to use vm.call.
    """
    def decorator(fn: Callable) -> W_BuiltinFunc:
        assert fn.__name__.startswith('w_')
        w_functype = functype_from_sig(fn, color)
        return W_BuiltinFunc(w_functype, qn, fn)
    return decorator


def builtin_type(qn: QN) -> Any:
    """
    Class decorator to simplify the creation of SPy types.

    Given a W_* class, it automatically creates the corresponding instance of
    W_Type and attaches it to the W_* class.
    """
    def decorator(pyclass: Type[W_Object]) -> Type[W_Object]:
        W_MetaClass = make_metaclass(qn, pyclass)
        pyclass._w = W_MetaClass(qn, pyclass)
        # setup __spy_members__
        pyclass.__spy_members__ = {}
        for field, t in pyclass.__annotations__.items():
            member = _get_member_maybe(t)
            if member is not None:
                member.field = field
                member.w_type = typing.get_args(t)[0]._w
                pyclass.__spy_members__[member.name] = member

        return pyclass
    return decorator
