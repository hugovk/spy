from typing import Any
import textwrap
import pytest
import spy.ast
from spy.parser import Parser
from spy.ast_dump import dump
from spy.tests.support import CompilerTest, expect_errors

@pytest.mark.usefixtures('init')
class TestParser:

    @pytest.fixture
    def init(self, tmpdir):
        self.tmpdir = tmpdir

    def parse(self, src: str) -> spy.ast.Module:
        f = self.tmpdir.join('test.spy')
        src = textwrap.dedent(src)
        f.write(src)
        parser = Parser(src, str(f))
        self.mod = parser.parse()
        return self.mod

    def expect_errors(self, src: str, *, errors: list[str]):
        with expect_errors(errors):
            self.parse(src)

    def assert_dump(self, node: spy.ast.Node, expected: str):
        dumped = dump(node, use_colors=False)
        expected = textwrap.dedent(expected)
        if '{tmpdir}' in expected:
            expected = expected.format(tmpdir=self.tmpdir)
        assert dumped.strip() == expected.strip()

    def test_Module(self):
        mod = self.parse("""
        def foo() -> void:
            pass
        """)
        expected = """
        Module(
            filename='{tmpdir}/test.spy',
            decls=[
                FuncDef(
                    color='red',
                    name='foo',
                    args=[],
                    return_type=Name(id='void'),
                    body=[
                        Pass(),
                    ],
                ),
            ],
        )
        """
        self.assert_dump(mod, expected)

    def test_FuncDef_arguments(self):
        mod = self.parse("""
        def foo(a: i32, b: float) -> void:
            pass
        """)
        expected = """
        Module(
            filename='{tmpdir}/test.spy',
            decls=[
                FuncDef(
                    color='red',
                    name='foo',
                    args=[
                        FuncArg(
                            name='a',
                            type=Name(id='i32'),
                        ),
                        FuncArg(
                            name='b',
                            type=Name(id='float'),
                        ),
                    ],
                    return_type=Name(id='void'),
                    body=[
                        Pass(),
                    ],
                ),
            ],
        )
        """
        self.assert_dump(mod, expected)

    def test_FuncDef_errors(self):
        self.expect_errors(
            """
            def foo():
                pass

            """,
            errors = ["missing return type"],
        )
        self.expect_errors(
            """
            def foo(*args) -> void:
                pass
            """,
            errors = ["*args is not supported yet"]
        )
        self.expect_errors(
            """
            def foo(**kwargs) -> void:
                pass
            """,
            errors = ["**kwargs is not supported yet"]
        )
        self.expect_errors(
            """
            def foo(a: i32 = 42) -> void:
                pass
            """,
            errors = ["default arguments are not supported yet"]
        )
        self.expect_errors(
            """
            def foo(a: i32, /, b: i32) -> void:
                pass
            """,
            errors = ["positional-only arguments are not supported yet"]
        )
        self.expect_errors(
            """
            def foo(a: i32, *, b: i32) -> void:
                pass
            """,
            errors = ["keyword-only arguments are not supported yet"]
        )
        self.expect_errors(
            """
            def foo(a, b) -> void:
                pass
            """,
            errors = ["missing type for argument 'a'"]
        )
        self.expect_errors(
            """
            @mydecorator
            def foo() -> void:
                pass
            """,
            errors = ["decorators are not supported yet"]
        )

    def test_FuncDef_body(self):
        mod = self.parse("""
        def foo() -> i32:
            return 42
        """)
        funcdef = mod.get_funcdef('foo')
        expected = """
        FuncDef(
            color='red',
            name='foo',
            args=[],
            return_type=Name(id='i32'),
            body=[
                Return(
                    value=Constant(value=42),
                ),
            ],
        )
        """
        self.assert_dump(funcdef, expected)

    def test_blue_FuncDef(self):
        mod = self.parse("""
        @blue
        def foo() -> i32:
            return 42
        """)
        funcdef = mod.get_funcdef('foo')
        expected = """
        FuncDef(
            color='blue',
            name='foo',
            args=[],
            return_type=Name(id='i32'),
            body=[
                Return(
                    value=Constant(value=42),
                ),
            ],
        )
        """
        self.assert_dump(funcdef, expected)

    def test_empty_return(self):
        mod = self.parse("""
        def foo() -> void:
            return
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = """
        Return(
            value=Constant(value=None),
        )
        """
        self.assert_dump(stmt, expected)

    def test_GetItem(self):
        mod = self.parse("""
        def foo() -> void:
            return mylist[0]
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = """
        Return(
            value=GetItem(
                value=Name(id='mylist'),
                index=Constant(value=0),
            ),
        )
        """
        self.assert_dump(stmt, expected)

    def test_VarDef(self):
        mod = self.parse("""
        def foo() -> void:
            x: i32 = 42
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = """
        VarDef(
            name='x',
            type=Name(id='i32'),
            value=Constant(value=42),
        )
        """
        self.assert_dump(stmt, expected)

    def test_global_VarDef(self):
        mod = self.parse("""
        x: i32 = 42
        """)
        expected = f"""
        Module(
            filename='{self.tmpdir}/test.spy',
            decls=[
                GlobalVarDef(
                    vardef=VarDef(
                        name='x',
                        type=Name(id='i32'),
                        value=Constant(value=42),
                    ),
                ),
            ],
        )
        """
        self.assert_dump(mod, expected)

    def test_List(self):
        mod = self.parse("""
        def foo() -> void:
            return [1, 2, 3]
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = """
        Return(
            value=List(
                items=[
                    Constant(value=1),
                    Constant(value=2),
                    Constant(value=3),
                ],
            ),
        )
        """
        self.assert_dump(stmt, expected)

    @pytest.mark.parametrize("op", "+ - * / // % ** << >> | ^ & @".split())
    def test_BinOp(self, op):
        # map the operator to the spy.ast class name
        binops = {
            '+':  'Add',
            '-':  'Sub',
            '*':  'Mul',
            '/':  'Div',
            '//': 'FloorDiv',
            '%':  'Mod',
            '**': 'Pow',
            '<<': 'LShift',
            '>>': 'RShift',
            '|':  'BitOr',
            '^':  'BitXor',
            '&':  'BitAnd',
            '@':  'MatMul',
        }
        OpClass = binops[op]
        #
        mod = self.parse(f"""
        def foo() -> i32:
            return x {op} 1
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = f"""
        Return(
            value={OpClass}(
                left=Name(id='x'),
                right=Constant(value=1),
            ),
        )
        """
        self.assert_dump(stmt, expected)

    @pytest.mark.parametrize("op", "+ - ~ not".split())
    def test_UnaryOp(self, op):
        # map the operator to the spy.ast class name
        unops = {
            '+': 'UnaryPos',
            '-': 'UnaryNeg',
            '~': 'Invert',
            'not': 'Not',
        }
        OpClass = unops[op]
        #
        mod = self.parse(f"""
        def foo() -> i32:
            return {op} x
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = f"""
        Return(
            value={OpClass}(
                value=Name(id='x'),
            ),
        )
        """
        self.assert_dump(stmt, expected)

    def test_negative_const(self):
        # special case -NUM, so that it's seen as a constant by the rest of the code
        mod = self.parse(f"""
        def foo() -> i32:
            return -123
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = """
        Return(
            value=Constant(value=-123),
        )
        """
        self.assert_dump(stmt, expected)

    @pytest.mark.parametrize("op", "== != < <= > >= is is_not in not_in".split())
    def test_CompareOp(self, op):
        op = op.replace('_', ' ')  # is_not ==> is not
        # map the operator to the spy.ast class name
        cmpops = {
            '==':     'Eq',
            '!=':     'NotEq',
            '<':      'Lt',
            '<=':     'LtE',
            '>':      'Gt',
            '>=':     'GtE',
            'is':     'Is',
            'is not': 'IsNot',
            'in':     'In',
            'not in': 'NotIn',

        }
        OpClass = cmpops[op]
        #
        mod = self.parse(f"""
        def foo() -> i32:
            return x {op} 1
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = f"""
        Return(
            value={OpClass}(
                left=Name(id='x'),
                right=Constant(value=1),
            ),
        )
        """
        self.assert_dump(stmt, expected)

    def test_CompareOp_chained(self):
        self.expect_errors(
            """
            def foo() -> i32:
                return 1 == 2 == 3
            """,
            errors = ["not implemented yet: chained comparisons"],
        )

    def test_Assign(self):
        mod = self.parse("""
        def foo() -> void:
            x = 42
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = """
        Assign(
            target='x',
            value=Constant(value=42),
        )
        """
        self.assert_dump(stmt, expected)

    def test_Assign_unsupported(self):
        self.expect_errors(
            """
            def foo() -> void:
                a = b = 1
            """,
            errors = ["not implemented yet: assign to multiple targets"]
        )
        self.expect_errors(
            """
            def foo() -> void:
                a, b = 1, 2
            """,
            errors = ["not implemented yet: assign to complex expressions"]
        )

    def test_Call(self):
        mod = self.parse("""
        def foo() -> i32:
            return bar(1, 2, 3)
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = """
        Return(
            value=Call(
                func=Name(id='bar'),
                args=[
                    Constant(value=1),
                    Constant(value=2),
                    Constant(value=3),
                ],
            ),
        )
        """
        self.assert_dump(stmt, expected)

    def test_Call_errors(self):
        self.expect_errors(
            """
            def foo() -> i32:
                return Bar(1, 2, x=3)
            """,
            errors = ["not implemented yet: keyword arguments"],
        )

    def test_If(self):
        mod = self.parse("""
        def foo() -> i32:
            if x:
                return 1
            else:
                return 2
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = """
        If(
            test=Name(id='x'),
            then_body=[
                Return(
                    value=Constant(value=1),
                ),
            ],
            else_body=[
                Return(
                    value=Constant(value=2),
                ),
            ],
        )
        """
        self.assert_dump(stmt, expected)

    def test_StmtExpr(self):
        mod = self.parse("""
        def foo() -> void:
            42
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = """
        StmtExpr(
            value=Constant(value=42),
        )
        """
        self.assert_dump(stmt, expected)

    def test_While(self):
        mod = self.parse("""
        def foo() -> void:
            while True:
                pass
        """)
        stmt = mod.get_funcdef('foo').body[0]
        expected = """
        While(
            test=Constant(value=True),
            body=[
                Pass(),
            ],
        )
        """
        self.assert_dump(stmt, expected)

    def test_from_import(self):
        mod = self.parse("""
        from testmod import a, b as b2
        """)
        #
        expected = """
        Module(
            filename='{tmpdir}/test.spy',
            decls=[
                Import(fqn=FQN('testmod::a'), asname='a'),
                Import(fqn=FQN('testmod::b'), asname='b2'),
            ],
        )
        """
        self.assert_dump(mod, expected)
