import re
import pytest
from spy.errors import SPyTypeError
from spy.fqn import FQN
from spy.vm.b import B
from spy.vm.function import W_ASTFunc
from spy.tests.support import (CompilerTest, skip_backends,  expect_errors,
                               only_interp)

class TestTypedef(CompilerTest):

    @pytest.mark.xfail(reason="IMPLEMENT ME")
    def test_from_and_to(self):
        mod = self.compile("""
        @typedef
        class MyInt:
            __inner__: i32

        def box(i: i32) -> MyInt:
            return MyInt.from_inner(i)

        def unbox(m: MyInt) -> i32:
            return m.__inner__

        def call_unbox(i: i32) -> i32:
            return unbox(box(i))

        """)
        assert mod.box(42).__inner__ == 42
        assert mod.call_unbox(43) == 43
