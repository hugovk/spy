import typing
from typing import Any
from spy.vm.object import W_Object, W_Type, spytype
from spy.textbuilder import ColorFormatter

if typing.TYPE_CHECKING:
    from spy.vm.function import W_FunctionType

# for now, each opcode is represented by its name. Very inefficient but we
# don't care for now. Eventually, we could migrate to a more proper bytecode
# or wordcode.
ALL_OPCODES = [
    'return',
    'abort',
    'mark',
    'mark_while',
    'load_const',
    'load_local',
    'load_global',
    'store_local',
    'store_global',
    'call_global',
    'i32_add',
    'i32_sub',
    'i32_mul',
    'i32_eq',
    'i32_neq',
    'i32_lt',
    'i32_lte',
    'i32_gt',
    'i32_gte',
    'pop_and_discard',
    'br',
    'br_if_not',
]

class OpCode:
    name: str
    args: tuple

    def __init__(self, name: str, *args: Any) -> None:
        if name not in ALL_OPCODES:
            raise ValueError(f'Invalid opcode: {name}')
        self.name = name
        self.args = args

    def is_br(self) -> bool:
        return self.name.startswith('br')

    def is_mark(self, marker: str) -> bool:
        return self.name == 'mark' and self.args == (marker,)

    def set_br_target(self, target: int) -> None:
        """
        Assuming that this is an OpCode of the br_* family which is not fully
        initialized yet, set the target opcode.
        """
        if not self.is_br():
            raise ValueError(f'cannot set br target on opcode {self.name}')
        if self.args != (None,):
            raise ValueError('target already set')
        self.args = (target,)

    def __repr__(self) -> str:
        if self.args:
            return f'<OpCode {self.name} {list(self.args)}>'
        else:
            return f'<OpCode {self.name}>'



@spytype('CodeObject')
class W_CodeObject(W_Object):
    name: str
    w_functype: 'W_FunctionType'
    filename: str
    body: list[OpCode]
    locals_w_types: dict[str, W_Type]

    def __init__(self, name: str, *, w_functype: 'W_FunctionType',
                 filename: str = '') -> None:
        self.name = name
        self.w_functype = w_functype
        self.filename = filename
        self.body = []
        self.locals_w_types = {}

    def __repr__(self) -> str:
        return f'<spy CodeObject {self.name}>'

    def declare_local(self, name: str, w_type: W_Type) -> None:
        assert name not in self.locals_w_types
        self.locals_w_types[name] = w_type

    def validate_if_then(self, i: int) -> int:
        """
        Check that the codegen emitted the expected code for an if/then
        block. Return the ENDIF index.

        The expected pattern is the following (see CodeGen.do_exec_If):
            I: mark if_then
               br_if_not ENDIF
                   <then body>
        ENDIF: <rest of the program>
        """
        op_mark = self.body[i]
        assert op_mark.is_mark('if_then')
        op_br_if_not = self.body[i + 1]
        assert op_br_if_not.name == 'br_if_not'
        endif_i = op_br_if_not.args[0]
        return endif_i

    def validate_if_then_else(self, i: int) -> tuple[int, int]:
        """
        Check that the codegen emitted the expected code for an if/then/else
        block. Return the ELSE, ENDIF indexes.

        The expected pattern is the following (see CodeGen.do_exec_If):
            I: mark if_then_else
               br_if_not ELSE
                   <then body>
               br ENDIF
         ELSE:     <else body>
        ENDIF: <rest of the program>
        """
        op_mark = self.body[i]
        assert op_mark.is_mark('if_then_else')
        op_br_if_not = self.body[i + 1]
        assert op_br_if_not.name == 'br_if_not'
        else_i = op_br_if_not.args[0]
        op_br = self.body[else_i - 1]
        assert op_br.name == 'br'
        endif_i = op_br.args[0]
        return else_i, endif_i

    def pp(self) -> None:
        """
        Pretty print
        """
        color = ColorFormatter(use_colors=True)
        name = color.set('green', self.name)
        sig = color.set('red', self.w_functype.name)
        print(f'Disassembly of code {name}: {sig}')
        for name, w_type in self.locals_w_types.items():
            name = color.set('green', name)
            typename = color.set('red', w_type.name)
            print(f'    var {name}: {typename}')
        #
        print()
        # first, find all the branches and record the targets, for coloring
        all_br_targets = set()
        for op in self.body:
            if op.is_br():
                all_br_targets.add(op.args[0])
        #
        for i, op in enumerate(self.body):
            line = [color.set('blue', op.name)]
            args = ', '.join([str(arg) for arg in op.args])
            if op.name in ('load_local', 'store_local', 'load_global', 'store_global'):
                args = color.set('green', args)
            elif op.is_br():
                args = color.set('red', args)
            elif op.name == 'abort':
                args = repr(args)
            #
            label = format(i, '>5')
            if i in all_br_targets:
                label = color.set('red', label)
            print(f'    {label} {op.name:<15} {args}')
