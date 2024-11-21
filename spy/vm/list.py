from typing import (TYPE_CHECKING, Any, Optional, Type, ClassVar,
                    TypeVar, Generic, Annotated)
from spy.fqn import FQN
from spy.vm.b import B
from spy.vm.primitive import W_I32, W_Bool, W_Dynamic, W_Void
from spy.vm.object import (W_Object, W_Type)
from spy.vm.builtin import builtin_func, builtin_type
if TYPE_CHECKING:
    from spy.vm.vm import SPyVM
    from spy.vm.opimpl import W_OpImpl, W_OpArg


CACHE = {}
def make_prebuilt(itemcls: Type[W_Object]) -> W_Type:
    assert issubclass(itemcls, W_Object)
    if itemcls not in CACHE:
        W_MyList = _make_W_List(itemcls._w)
        CACHE[itemcls] = W_MyList
    return W_MyList._w


class W_ListType(W_Type):
    """
    A specialized list type.
    list[i32] -> W_ListType(fqn, B.w_i32)
    """
    w_itemtype: W_Type

    def __init__(self, fqn: FQN, w_itemtype: W_Type,
                 *,
                 pyclass # temporary
                 ) -> None:
        super().__init__(fqn, pyclass)
        self.w_itemtype = w_itemtype


@B.builtin_type('list')
class W_BaseList(W_Object):
    """
    The 'list' type.

    It has two purposes:

      - it's the base type for all lists

      - by implementing meta_op_GETITEM, it can be used to create
       _specialized_ list types, e.g. `list[i32]`.

    In other words, `list[i32]` inherits from `list`.

    The specialized types are created by calling the builtin make_list_type:
    see its docstring for details.
    """
    __spy_storage_category__ = 'reference'

    def __init__(self, items_w: Any) -> None:
        raise Exception("You cannot instantiate W_BaseList, use W_List")

    @staticmethod
    def meta_op_GETITEM(vm: 'SPyVM', wop_obj: 'W_OpArg',
                        wop_i: 'W_OpArg') -> 'W_OpImpl':
        from spy.vm.opimpl import W_OpImpl
        return W_OpImpl(w_make_list_type)


class W_List(W_BaseList):
    w_listtype: W_ListType
    items_w: list[W_Object]

    def __init__(self, w_listtype: W_ListType, items_w: list[W_Object]) -> None:
        assert isinstance(w_listtype, W_ListType)
        self.w_listtype = w_listtype
        # XXX typecheck?
        self.items_w = items_w

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        return f'{cls}({self.items_w})'

    def spy_get_w_type(self, vm: 'SPyVM') -> W_Type:
        return self.w_listtype

    def spy_unwrap(self, vm: 'SPyVM') -> list[Any]:
        return [vm.unwrap(w_item) for w_item in self.items_w]

    @staticmethod
    def _get_listtype(wop_list: 'W_OpArg') -> W_ListType:
        w_listtype = wop_list.w_static_type
        if isinstance(w_listtype, W_ListType):
            return w_listtype
        else:
            # I think we can get here if we have something typed 'list' as
            # opposed to e.g. 'list[i32]'
            assert False, 'FIXME: raise a nice error'

    @staticmethod
    def op_GETITEM(vm: 'SPyVM', wop_list: 'W_OpArg',
                   wop_i: 'W_OpArg') -> 'W_OpImpl':
        from spy.vm.opimpl import W_OpImpl
        w_listtype = W_List._get_listtype(wop_list)
        w_T = w_listtype.w_itemtype
        LIST = Annotated[W_List, w_listtype]
        T = Annotated[W_Object, w_T]

        @builtin_func(w_listtype.fqn)
        def w_getitem(vm: 'SPyVM', w_list: LIST, w_i: W_I32) -> T:
            i = vm.unwrap_i32(w_i)
            # XXX bound check?
            return w_list.items_w[i]
        return W_OpImpl(w_getitem)

    @staticmethod
    def op_SETITEM(vm: 'SPyVM', wop_list: 'W_OpArg', wop_i: 'W_OpArg',
                   wop_v: 'W_OpArg') -> 'W_OpImpl':
        from spy.vm.opimpl import W_OpImpl
        w_listtype = W_List._get_listtype(wop_list)
        w_T = w_listtype.w_itemtype
        LIST = Annotated[W_List, w_listtype]
        T = Annotated[W_Object, w_T]

        @builtin_func(w_listtype.fqn)
        def w_setitem(vm: 'SPyVM', w_list: LIST, w_i: W_I32, w_v: T) -> None:
            i = vm.unwrap_i32(w_i)
            # XXX bound check?
            w_list.items_w[i] = w_v
        return W_OpImpl(w_setitem)


@builtin_func('__spy__', color='blue')
def w_make_list_type(vm: 'SPyVM', w_list: W_Object, w_T: W_Type) -> W_ListType:
    """
    Create a concrete W_List class specialized for W_Type.

    Given a type T, it is always safe to call make_list_type(T) multiple
    types, and it is guaranteed to get always the same type.

    It is worth noting that to achieve that, we have two layers of caching:

      - if we have a prebuilt list type, just use that
      - for other types, we rely on the fact that `make_list_type` is blue.
    """
    assert w_list is W_List._w
    if w_T.pyclass in CACHE:
        # legacy code, kill it eventually
        w_list_type = vm.wrap(CACHE[w_T.pyclass])
        return w_list_type
    #
    # new code
    fqn = FQN('builtins').join('list', [w_T.fqn])  # builtins::list[i32]
    return W_ListType(fqn, w_T, pyclass=W_List)



def _make_W_List(w_T: W_Type) -> Type[W_List]:
    """
    DON'T CALL THIS DIRECTLY!
    You should call make_list_type instead, which knows how to deal with
    prebuilt types.
    """
    from spy.vm.opimpl import W_OpImpl
    # legacy code for list[OpArg], we will kill it eventually
    assert w_T.fqn == FQN('operator::OpArg')

    T = Annotated[W_Object, w_T]

    fqn = FQN('builtins').join('list', [w_T.fqn])

    class W_MyList(W_List):
        __qualname__ = f'W_List[{w_T.pyclass.__name__}]' # e.g. W_List[W_I32]


        @staticmethod
        def op_EQ(vm: 'SPyVM', wop_l: 'W_OpArg', wop_r: 'W_OpArg') -> W_OpImpl:
            from spy.vm.b import B
            w_ltype = wop_l.w_static_type
            w_rtype = wop_r.w_static_type
            assert w_ltype.pyclass is W_MyList

            @builtin_func(W_MyList.type_fqn)
            def w_eq(vm: 'SPyVM', w_l1: W_MyList, w_l2: W_MyList) -> W_Bool:
                items1_w = w_l1.items_w
                items2_w = w_l2.items_w
                if len(items1_w) != len(items2_w):
                    return B.w_False
                for w_1, w_2 in zip(items1_w, items2_w):
                    if vm.is_False(vm.eq(w_1, w_2)):
                        return B.w_False
                return B.w_True

            if w_ltype is w_rtype:
                return W_OpImpl(w_eq)
            else:
                return W_OpImpl.NULL

    W_MyList.__name__ = W_MyList.__qualname__
    w_listtype = W_ListType(fqn, w_T, pyclass=W_MyList)
    W_MyList._w = w_listtype
    W_MyList.type_fqn = fqn

    return W_MyList
