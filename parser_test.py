import pytest
from parser import ParseError, parse_source
from nodes import (
    IntType, VoidType, BooleanType, SelfType, StructType, FunctionType,
    Param,
    StructDef, AbsMethodDef, ConcMethodDef, TraitDef, ImplDef, FuncDef,
    LetStmt, AssignStmt, IfStmt, WhileStmt, BreakStmt, PrintlnStmt,
    BlockStmt, ReturnStmt, ExpStmt,
    StructActualParam,
    IntExp, VarExp, BooleanExp, SelfExp, ParenExp, NewExp,
    DotExp, CallExp,
    MultOps, MultExp,
    AddOps, AddExp,
    LessThanExp,
    EqualsOps, EqualsExp,
    Program,
)

# Helper
def _primary(stmt):
    return (
        stmt.exp
        .less_than_exp_left
        .add_exp_left
        .mult_exp_left
        .call_exp_left
        .dot_exp
        .primary_exp
    )

# Types
class TestTypes:

    def test_int_type(self):
        prog = parse_source("let x: Int = 0;")
        assert prog.stmt[0].param.type == IntType()

    def test_void_type(self):
        prog = parse_source("func f(): Void { }")
        assert prog.program_item[0].type == VoidType()

    def test_boolean_type(self):
        prog = parse_source("let b: Boolean = true;")
        assert prog.stmt[0].param.type == BooleanType()

    def test_self_type(self):
        prog = parse_source("trait T { method m(self: Self): Self; }")
        method = prog.program_item[0].abs_methoddef[0]
        assert method.comma_param[0].type == SelfType()
        assert method.type == SelfType()

    def test_struct_type(self):
        prog = parse_source("let p: Point = new Point {};")
        assert prog.stmt[0].param.type == StructType(structname="Point")

    def test_function_type(self):
        prog = parse_source("let f: (Int, Int) => Boolean = g;")
        t = prog.stmt[0].param.type
        assert t == FunctionType(comma_type=[IntType(), IntType()], type=BooleanType())

    def test_empty_function_type(self):
        prog = parse_source("let f: () => Void = g;")
        t = prog.stmt[0].param.type
        assert t == FunctionType(comma_type=[], type=VoidType())

    def test_parenthesized_type_unwraps(self):
        prog = parse_source("let x: (Int) = 0;")
        assert prog.stmt[0].param.type == IntType()

    def test_function_type_single_param(self):
        prog = parse_source("let f: (Boolean) => Int = g;")
        t = prog.stmt[0].param.type
        assert t == FunctionType(comma_type=[BooleanType()], type=IntType())

# Expressions
class TestExpressions:

    def test_integer_literal(self):
        prog = parse_source("42;")
        assert _primary(prog.stmt[0]) == IntExp(i=42)

    def test_integer_zero(self):
        prog = parse_source("0;")
        assert _primary(prog.stmt[0]) == IntExp(i=0)

    def test_boolean_true(self):
        prog = parse_source("true;")
        assert _primary(prog.stmt[0]) == BooleanExp(value=True)

    def test_boolean_false(self):
        prog = parse_source("false;")
        assert _primary(prog.stmt[0]) == BooleanExp(value=False)

    def test_variable_expression(self):
        prog = parse_source("x;")
        assert _primary(prog.stmt[0]) == VarExp(var="x")

    def test_self_expression(self):
        prog = parse_source("self;")
        assert _primary(prog.stmt[0]) == SelfExp()

    def test_parenthesized_expression(self):
        prog = parse_source("(5);")
        paren = _primary(prog.stmt[0])
        assert isinstance(paren, ParenExp)
        inner = _primary(ExpStmt(exp=paren.exp))
        assert inner == IntExp(i=5)

    def test_new_expression_no_fields(self):
        prog = parse_source("new Point {};")
        new = _primary(prog.stmt[0])
        assert isinstance(new, NewExp)
        assert new.structname == "Point"
        assert new.struct_actual_params == []

    def test_new_expression_with_fields(self):
        prog = parse_source("new Point { x: 1, y: 2 };")
        new = _primary(prog.stmt[0])
        assert isinstance(new, NewExp)
        assert new.structname == "Point"
        assert len(new.struct_actual_params) == 2
        assert new.struct_actual_params[0].var == "x"
        assert new.struct_actual_params[1].var == "y"

    def test_dot_expression_single(self):
        prog = parse_source("p.x;")
        dot = prog.stmt[0].exp.less_than_exp_left.add_exp_left.mult_exp_left.call_exp_left.dot_exp
        assert dot.primary_exp == VarExp(var="p")
        assert dot.var == ["x"]

    def test_dot_expression_chained(self):
        prog = parse_source("a.b.c;")
        dot = prog.stmt[0].exp.less_than_exp_left.add_exp_left.mult_exp_left.call_exp_left.dot_exp
        assert dot.primary_exp == VarExp(var="a")
        assert dot.var == ["b", "c"]

    def test_call_no_args(self):
        prog = parse_source("f();")
        call = prog.stmt[0].exp.less_than_exp_left.add_exp_left.mult_exp_left.call_exp_left
        assert isinstance(call, CallExp)
        assert call.dot_exp.primary_exp == VarExp(var="f")
        assert call.comma_exp == [[]]

    def test_call_with_args(self):
        prog = parse_source("f(1, 2);")
        call = prog.stmt[0].exp.less_than_exp_left.add_exp_left.mult_exp_left.call_exp_left
        assert len(call.comma_exp) == 1
        assert len(call.comma_exp[0]) == 2

    def test_method_call_via_dot(self):
        prog = parse_source("obj.foo(1);")
        call = prog.stmt[0].exp.less_than_exp_left.add_exp_left.mult_exp_left.call_exp_left
        assert call.dot_exp.primary_exp == VarExp(var="obj")
        assert call.dot_exp.var == ["foo"]
        assert len(call.comma_exp) == 1

    def test_addition(self):
        prog = parse_source("1 + 2;")
        add = prog.stmt[0].exp.less_than_exp_left.add_exp_left
        assert len(add.mult_exp_right) == 1
        assert add.mult_exp_right[0][0] == AddOps.ADD

    def test_subtraction(self):
        prog = parse_source("5 - 3;")
        add = prog.stmt[0].exp.less_than_exp_left.add_exp_left
        assert add.mult_exp_right[0][0] == AddOps.SUB

    def test_chained_addition(self):
        prog = parse_source("1 + 2 + 3;")
        add = prog.stmt[0].exp.less_than_exp_left.add_exp_left
        assert len(add.mult_exp_right) == 2
        assert add.mult_exp_right[0][0] == AddOps.ADD
        assert add.mult_exp_right[1][0] == AddOps.ADD

    def test_multiplication(self):
        prog = parse_source("3 * 4;")
        mult = prog.stmt[0].exp.less_than_exp_left.add_exp_left.mult_exp_left
        assert len(mult.call_exp_right) == 1
        assert mult.call_exp_right[0][0] == MultOps.MULT

    def test_division(self):
        prog = parse_source("10 / 2;")
        mult = prog.stmt[0].exp.less_than_exp_left.add_exp_left.mult_exp_left
        assert mult.call_exp_right[0][0] == MultOps.DIV

    def test_less_than(self):
        prog = parse_source("1 < 2;")
        lt = prog.stmt[0].exp.less_than_exp_left
        assert lt.add_exp_right is not None

    def test_equals_equals(self):
        prog = parse_source("x == y;")
        eq = prog.stmt[0].exp
        assert eq.op == EqualsOps.EQUALS_EQUALS
        assert eq.less_than_exp_right is not None

    def test_not_equals(self):
        prog = parse_source("x != y;")
        eq = prog.stmt[0].exp
        assert eq.op == EqualsOps.NOT_EQUALS
        assert eq.less_than_exp_right is not None

    def test_no_comparison_operator(self):
        prog = parse_source("42;")
        eq = prog.stmt[0].exp
        assert eq.op is None
        assert eq.less_than_exp_right is None

    def test_no_less_than(self):
        prog = parse_source("42;")
        lt = prog.stmt[0].exp.less_than_exp_left
        assert lt.add_exp_right is None

    def test_mixed_arithmetic(self):
        prog = parse_source("2 + 3 * 4;")
        add = prog.stmt[0].exp.less_than_exp_left.add_exp_left
        # left side is the mult-exp for `2`
        assert len(add.mult_exp_right) == 1
        # right side of add is a mult-exp for `3 * 4`
        right_mult = add.mult_exp_right[0][1]
        assert len(right_mult.call_exp_right) == 1
        assert right_mult.call_exp_right[0][0] == MultOps.MULT

# Statements
class TestStatements:

    def test_let_int(self):
        prog = parse_source("let x: Int = 5;")
        stmt = prog.stmt[0]
        assert isinstance(stmt, LetStmt)
        assert stmt.param == Param(var="x", type=IntType())

    def test_let_boolean(self):
        prog = parse_source("let b: Boolean = false;")
        stmt = prog.stmt[0]
        assert isinstance(stmt, LetStmt)
        assert stmt.param == Param(var="b", type=BooleanType())

    def test_let_struct_type(self):
        prog = parse_source("let p: Point = new Point {};")
        stmt = prog.stmt[0]
        assert isinstance(stmt, LetStmt)
        assert stmt.param.type == StructType(structname="Point")

    def test_assign_stmt(self):
        prog = parse_source("x = 10;")
        stmt = prog.stmt[0]
        assert isinstance(stmt, AssignStmt)
        assert stmt.var == "x"

    def test_if_no_else(self):
        prog = parse_source("if (true) { }")
        stmt = prog.stmt[0]
        assert isinstance(stmt, IfStmt)
        assert stmt.else_condition is None

    def test_if_with_else(self):
        prog = parse_source("if (true) { } else { }")
        stmt = prog.stmt[0]
        assert isinstance(stmt, IfStmt)
        assert stmt.else_condition is not None

    def test_nested_if_else(self):
        prog = parse_source("if (x) { } else if (y) { }")
        stmt = prog.stmt[0]
        assert isinstance(stmt, IfStmt)
        assert isinstance(stmt.else_condition, IfStmt)

    def test_while_stmt(self):
        prog = parse_source("while (true) { }")
        stmt = prog.stmt[0]
        assert isinstance(stmt, WhileStmt)
        assert isinstance(stmt.stmt, BlockStmt)

    def test_break_stmt(self):
        prog = parse_source("while (true) { break; }")
        inner = prog.stmt[0].stmt.stmt[0]
        assert isinstance(inner, BreakStmt)

    def test_println_stmt(self):
        prog = parse_source("println(42);")
        stmt = prog.stmt[0]
        assert isinstance(stmt, PrintlnStmt)

    def test_println_variable(self):
        prog = parse_source("println(x);")
        stmt = prog.stmt[0]
        assert isinstance(stmt, PrintlnStmt)

    def test_block_stmt(self):
        prog = parse_source("{ let x: Int = 1; }")
        stmt = prog.stmt[0]
        assert isinstance(stmt, BlockStmt)
        assert len(stmt.stmt) == 1

    def test_empty_block_stmt(self):
        prog = parse_source("{ }")
        stmt = prog.stmt[0]
        assert isinstance(stmt, BlockStmt)
        assert stmt.stmt == []

    def test_return_with_value(self):
        prog = parse_source("func f(): Int { return 1; }")
        ret = prog.program_item[0].stmt[0]
        assert isinstance(ret, ReturnStmt)
        assert ret.exp is not None

    def test_return_no_value(self):
        prog = parse_source("func f(): Void { return; }")
        ret = prog.program_item[0].stmt[0]
        assert isinstance(ret, ReturnStmt)
        assert ret.exp is None

    def test_expression_stmt(self):
        prog = parse_source("5;")
        assert isinstance(prog.stmt[0], ExpStmt)

    def test_multiple_stmts(self):
        prog = parse_source("let x: Int = 1; let y: Int = 2;")
        assert len(prog.stmt) == 2

    def test_if_body_is_block(self):
        prog = parse_source("if (true) { let x: Int = 0; }")
        stmt = prog.stmt[0]
        assert isinstance(stmt.then_condition, BlockStmt)
        assert len(stmt.then_condition.stmt) == 1

    def test_while_body_executes_multiple(self):
        prog = parse_source("while (x) { y = 1; z = 2; }")
        body = prog.stmt[0].stmt
        assert isinstance(body, BlockStmt)
        assert len(body.stmt) == 2

# Program Items
class TestProgramItems:

    def test_empty_struct(self):
        prog = parse_source("struct Point { }")
        item = prog.program_item[0]
        assert isinstance(item, StructDef)
        assert item.structname == "Point"
        assert item.comma_param == []

    def test_struct_with_fields(self):
        prog = parse_source("struct Point { x: Int, y: Int }")
        item = prog.program_item[0]
        assert isinstance(item, StructDef)
        assert item.comma_param == [
            Param(var="x", type=IntType()),
            Param(var="y", type=IntType()),
        ]

    def test_struct_mixed_field_types(self):
        prog = parse_source("struct S { a: Int, b: Boolean }")
        item = prog.program_item[0]
        assert item.comma_param[0].type == IntType()
        assert item.comma_param[1].type == BooleanType()

    def test_trait_no_methods(self):
        prog = parse_source("trait Animal { }")
        item = prog.program_item[0]
        assert isinstance(item, TraitDef)
        assert item.traitname == "Animal"
        assert item.abs_methoddef == []

    def test_trait_one_method(self):
        prog = parse_source("trait Animal { method speak(self: Self): Void; }")
        item = prog.program_item[0]
        assert isinstance(item, TraitDef)
        m = item.abs_methoddef[0]
        assert m.var == "speak"
        assert m.comma_param == [Param(var="self", type=SelfType())]
        assert m.type == VoidType()

    def test_trait_multiple_methods(self):
        prog = parse_source("trait T { method a(self: Self): Int; method b(self: Self): Boolean; }")
        item = prog.program_item[0]
        assert len(item.abs_methoddef) == 2
        assert item.abs_methoddef[0].var == "a"
        assert item.abs_methoddef[1].var == "b"

    def test_impl_empty(self):
        prog = parse_source("impl Animal for Dog { }")
        item = prog.program_item[0]
        assert isinstance(item, ImplDef)
        assert item.traitname == "Animal"
        assert item.type == StructType(structname="Dog")
        assert item.conc_methoddef == []

    def test_impl_with_method(self):
        prog = parse_source("impl Animal for Dog { method speak(self: Self): Void { } }")
        item = prog.program_item[0]
        assert isinstance(item, ImplDef)
        assert len(item.conc_methoddef) == 1
        m = item.conc_methoddef[0]
        assert m.var == "speak"
        assert m.type == VoidType()

    def test_impl_for_builtin_type(self):
        prog = parse_source("impl MyTrait for Int { }")
        item = prog.program_item[0]
        assert item.type == IntType()

    def test_func_no_params(self):
        prog = parse_source("func main(): Void { }")
        item = prog.program_item[0]
        assert isinstance(item, FuncDef)
        assert item.var == "main"
        assert item.comma_param == []
        assert item.type == VoidType()
        assert item.stmt == []

    def test_func_with_params(self):
        prog = parse_source("func add(a: Int, b: Int): Int { return a; }")
        item = prog.program_item[0]
        assert isinstance(item, FuncDef)
        assert item.var == "add"
        assert item.comma_param == [
            Param(var="a", type=IntType()),
            Param(var="b", type=IntType()),
        ]
        assert item.type == IntType()

    def test_func_body_stmts(self):
        prog = parse_source("func f(): Int { let x: Int = 1; return x; }")
        item = prog.program_item[0]
        assert len(item.stmt) == 2
        assert isinstance(item.stmt[0], LetStmt)
        assert isinstance(item.stmt[1], ReturnStmt)

    def test_multiple_program_items(self):
        prog = parse_source("struct A { } struct B { }")
        assert len(prog.program_item) == 2

    def test_program_items_and_stmts_coexist(self):
        prog = parse_source("struct A { } let x: Int = 0;")
        assert len(prog.program_item) == 1
        assert len(prog.stmt) == 1

    def test_method_with_multiple_params(self):
        prog = parse_source("trait T { method f(self: Self, a: Int, b: Boolean): Int; }")
        m = prog.program_item[0].abs_methoddef[0]
        assert len(m.comma_param) == 3

    def test_conc_method_with_body(self):
        prog = parse_source("impl T for S { method f(self: Self): Int { return 1; } }")
        m = prog.program_item[0].conc_methoddef[0]
        assert len(m.stmt) == 1
        assert isinstance(m.stmt[0], ReturnStmt)

# Error cases
class TestParseErrors:

    def test_missing_semicolon_let(self):
        with pytest.raises(ParseError):
            parse_source("let x: Int = 5")

    def test_missing_colon_in_param(self):
        with pytest.raises(ParseError):
            parse_source("let x Int = 5;")

    def test_missing_equals_in_let(self):
        with pytest.raises(ParseError):
            parse_source("let x: Int 5;")

    def test_unknown_token_as_expression(self):
        with pytest.raises(ParseError):
            parse_source("let x: Int = ;")

    def test_invalid_type_token(self):
        with pytest.raises(ParseError):
            parse_source("let x: 42 = 5;")

    def test_empty_parenthesized_type(self):
        with pytest.raises(ParseError):
            parse_source("let x: () = 5;")

    def test_unclosed_paren_expression(self):
        with pytest.raises(ParseError):
            parse_source("(5;")

    def test_missing_struct_closing_brace(self):
        with pytest.raises(ParseError):
            parse_source("struct Point { x: Int")

    def test_missing_func_closing_brace(self):
        with pytest.raises(ParseError):
            parse_source("func f(): Void {")

    def test_missing_impl_for_keyword(self):
        with pytest.raises(ParseError):
            parse_source("impl Trait Dog { }")

    def test_missing_semicolon_break(self):
        with pytest.raises(ParseError):
            parse_source("while (true) { break }")

    def test_error_has_line_and_col(self):
        try:
            parse_source("let x: Int = ;")
        except ParseError as e:
            assert e.line >= 1
            assert e.col >= 1
        else:
            pytest.fail("Expected ParseError")

    def test_missing_println_parens(self):
        with pytest.raises(ParseError):
            parse_source("println 42;")

    def test_missing_if_condition_parens(self):
        with pytest.raises(ParseError):
            parse_source("if true { }")

    def test_invalid_param_name(self):
        # A literal integer is not a valid parameter name
        with pytest.raises(ParseError):
            parse_source("func f(42: Int): Void { }")
