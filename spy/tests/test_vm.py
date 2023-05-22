import pytest
from spy.vm.vm import SPyVM
from spy.vm.objects import W_Object, W_Type, spytype, W_NoneType

class TestVM:

    def test_W_Object(self):
        vm = SPyVM()
        w_obj = W_Object()
        assert repr(w_obj).startswith('<spy instance: type=object, id=')
        assert vm.w_dynamic_type(w_obj) is vm.builtins.w_object

    def test_object_type_metaclass(self):
        # in the following, for each property of the SPy object model we also
        # show and test the corresponding property of the Python object model,
        # to make it clearer what it means
        vm = SPyVM()
        B = vm.builtins
        #
        # the metaclass of <object> is <type>
        assert type(object) is type
        assert vm.w_dynamic_type(B.w_object) is B.w_type
        #
        # the metaclass of <type> is <type> itself
        assert type(type) is type
        assert vm.w_dynamic_type(B.w_type) is B.w_type
        #
        # <type> is a subclass of <object>
        assert type.__base__ is object
        assert B.w_type.w_base is B.w_object

    def test_W_Type_repr(self):
        vm = SPyVM()
        assert repr(vm.builtins.w_object) == "<spy type 'object'>"
        assert repr(vm.builtins.w_type) == "<spy type 'type'>"

    def test_spytype_decorator(self):
        @spytype('foo')
        class W_Foo(W_Object):
            pass
        #
        assert isinstance(W_Foo._w, W_Type)
        assert W_Foo._w.name == 'foo'
        assert W_Foo._w.pyclass is W_Foo

    def test_w_base(self):
        @spytype('A')
        class W_A(W_Object):
            pass
        #
        @spytype('B')
        class W_B(W_A):
            pass
        #
        w_None = W_NoneType._w_singleton
        assert W_Object._w.w_base is w_None
        assert W_A._w.w_base is W_Object._w
        assert W_B._w.w_base is W_A._w

    def test_issubclass(self):
        @spytype('A')
        class W_A(W_Object):
            pass
        #
        @spytype('B')
        class W_B(W_A):
            pass
        #
        vm = SPyVM()
        w_a = W_A._w
        w_b = W_B._w
        #
        assert vm.issubclass(w_a, vm.builtins.w_object)
        assert vm.issubclass(w_b, vm.builtins.w_object)
        assert vm.issubclass(w_a, w_a)
        assert vm.issubclass(w_b, w_b)
        assert vm.issubclass(w_b, w_a)
        assert not vm.issubclass(w_a, w_b)

    def test_wrap_unwrap_types(self):
        vm = SPyVM()
        assert vm.wrap(W_Object) is vm.builtins.w_object
        assert vm.unwrap(vm.builtins.w_object) is W_Object
        #
        # check that wrapping an unsupported type raises
        class Foo:
            pass
        with pytest.raises(Exception,
                           match="Cannot wrap interp-level objects of type Foo"):
            vm.wrap(Foo())

    def test_w_None(self):
        vm = SPyVM()
        w_None = vm.builtins.w_None
        assert isinstance(w_None, W_NoneType)
        assert vm.w_dynamic_type(w_None).name == 'NoneType'
        assert repr(w_None) == '<spy None>'
        #
        assert vm.wrap(None) is w_None
