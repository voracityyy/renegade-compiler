import pytest
from parser import parse_source
from typechecker import typecheck_program, TypeError, Typechecker, is_types_equal, type_to_string, Environment, \
    GlobalEnvironment
from nodes import (
    IntType, VoidType, BooleanType, SelfType, StructType, FunctionType,
    Param, StructDef, TraitDef, ImplDef, FuncDef,
    AbsMethodDef, ConcMethodDef,
    Program,
)

def check(source: str) -> None:
    typecheck_program(parse_source(source))


def check_error(source: str) -> None:
    with pytest.raises(TypeError):
        typecheck_program(parse_source(source))

# is types equal
class TestIsTypesEqual:

    def test_int_int(self):
        assert is_types_equal(IntType(), IntType())

    def test_void_void(self):
        assert is_types_equal(VoidType(), VoidType())

    def test_boolean_boolean(self):
        assert is_types_equal(BooleanType(), BooleanType())

    def test_self_self(self):
        assert is_types_equal(SelfType(), SelfType())

    def test_int_vs_boolean(self):
        assert not is_types_equal(IntType(), BooleanType())

    def test_struct_same_name(self):
        assert is_types_equal(StructType("Point"), StructType("Point"))

    def test_struct_different_name(self):
        assert not is_types_equal(StructType("Point"), StructType("Rect"))

    def test_function_type_equal(self):
        a = FunctionType([IntType()], BooleanType())
        b = FunctionType([IntType()], BooleanType())
        assert is_types_equal(a, b)

    def test_function_type_param_count_mismatch(self):
        a = FunctionType([IntType(), IntType()], BooleanType())
        b = FunctionType([IntType()], BooleanType())
        assert not is_types_equal(a, b)

    def test_function_type_param_type_mismatch(self):
        a = FunctionType([IntType()], BooleanType())
        b = FunctionType([BooleanType()], BooleanType())
        assert not is_types_equal(a, b)

    def test_function_type_return_mismatch(self):
        a = FunctionType([IntType()], IntType())
        b = FunctionType([IntType()], BooleanType())
        assert not is_types_equal(a, b)

    def test_empty_function_types_equal(self):
        assert is_types_equal(FunctionType([], VoidType()), FunctionType([], VoidType()))

# type to string
class TestTypeToString:

    def test_int(self):
        assert type_to_string(IntType()) == "Int"

    def test_void(self):
        assert type_to_string(VoidType()) == "Void"

    def test_boolean(self):
        assert type_to_string(BooleanType()) == "Boolean"

    def test_self(self):
        assert type_to_string(SelfType()) == "Self"

    def test_function_no_params(self):
        assert type_to_string(FunctionType([], VoidType())) == "() => Void"

    def test_function_with_params(self):
        assert type_to_string(FunctionType([IntType(), BooleanType()], IntType())) == "(Int, Boolean) => Int"

# Environment
class TestEnvironment:

    def test_bind_and_lookup(self):
        env = Environment()
        env.bind("x", IntType())
        assert is_types_equal(env.lookup("x"), IntType())

    def test_lookup_missing(self):
        env = Environment()
        assert env.lookup("y") is None

    def test_child_inherits_parent(self):
        parent = Environment()
        parent.bind("x", BooleanType())
        child = parent.child()
        assert is_types_equal(child.lookup("x"), BooleanType())

    def test_child_shadows_parent(self):
        parent = Environment()
        parent.bind("x", IntType())
        child = parent.child()
        child.bind("x", BooleanType())
        assert is_types_equal(child.lookup("x"), BooleanType())
        assert is_types_equal(parent.lookup("x"), IntType())

# Valid programs
class TestValidPrograms:

    def test_empty_program(self):
        check("")

    def test_let_int(self):
        check("let x: Int = 5;")

    def test_let_boolean(self):
        check("let b: Boolean = true;")

    def test_assign(self):
        check("let x: Int = 0; x = 1;")

    def test_println_int(self):
        check("println(42);")

    def test_println_boolean(self):
        check("println(true);")

    def test_if_no_else(self):
        check("if (true) { }")

    def test_if_with_else(self):
        check("if (true) { } else { }")

    def test_while_break(self):
        check("while (true) { break; }")

    def test_arithmetic(self):
        check("let x: Int = 1 + 2 * 3;")

    def test_comparison_less_than(self):
        check("let b: Boolean = 1 < 2;")

    def test_equals_equals(self):
        check("let b: Boolean = 1 == 1;")

    def test_not_equals(self):
        check("let b: Boolean = 1 != 2;")

    def test_paren_exp(self):
        check("let x: Int = (5);")

    def test_empty_struct(self):
        check("struct Point { }")

    def test_struct_with_fields(self):
        check("struct Point { x: Int, y: Int }")

    def test_new_struct_no_fields(self):
        check("struct Empty { } let e: Empty = new Empty {};")

    def test_new_struct_with_fields(self):
        check("struct Point { x: Int, y: Int } let p: Point = new Point { x: 1, y: 2 };")

    def test_struct_field_access(self):
        check("struct Point { x: Int, y: Int } let p: Point = new Point { x: 1, y: 2 }; let n: Int = p.x;")

    def test_func_no_params(self):
        check("func f(): Void { }")

    def test_func_with_params_and_return(self):
        check("func add(a: Int, b: Int): Int { return a; }")

    def test_func_called_from_entry(self):
        check("func greet(): Void { } greet();")

    def test_trait_and_impl_int(self):
        check("""
            trait Addable { method add(other: Self): Self; }
            impl Addable for Int { method add(other: Int): Int { return self; } }
        """)

    def test_method_call_on_int(self):
        check("""
            trait Addable { method add(other: Self): Self; }
            impl Addable for Int { method add(other: Int): Int { return self; } }
            let x: Int = 5;
            let y: Int = x.add(3);
        """)

    def test_impl_for_struct(self):
        check("""
            trait Greet { method greet(): Void; }
            struct Dog { name: Int }
            impl Greet for Dog {
                method greet(): Void { println(self.name); }
            }
        """)

    def test_higher_order_function_type(self):
        check("func apply(f: (Int) => Int, x: Int): Int { return x; }")

    def test_nested_if_else(self):
        check("if (true) { } else if (false) { } ")

    def test_return_void(self):
        check("func f(): Void { return; }")

    def test_block_stmt(self):
        check("{ let x: Int = 1; }")

    def test_self_in_method(self):
        check("""
            trait T { method val(): Int; }
            impl T for Int { method val(): Int { return self; } }
        """)

    def test_subtraction(self):
        check("let x: Int = 10 - 3;")

    def test_division(self):
        check("let x: Int = 10 / 2;")

    def test_chained_method_calls(self):
        check("""
            trait T { method inc(): Self; }
            impl T for Int { method inc(): Int { return self; } }
            let x: Int = 5;
            let y: Int = x.inc();
        """)

    def test_multiple_impl_methods(self):
        check("""
            trait Shape { method area(): Int; method perimeter(): Int; }
            struct Rect { w: Int, h: Int }
            impl Shape for Rect {
                method area(): Int { return self.w; }
                method perimeter(): Int { return self.h; }
            }
        """)

    def test_boolean_equality(self):
        check("let b: Boolean = true == false;")

    def test_while_with_body(self):
        check("let x: Int = 0; while (true) { x = 1; }")

# Type errors
class TestTypeErrors:

    def test_undeclared_variable(self):
        check_error("x;")

    def test_let_type_mismatch(self):
        check_error("let x: Int = true;")

    def test_assign_to_undeclared(self):
        check_error("x = 5;")

    def test_assign_type_mismatch(self):
        check_error("let x: Int = 0; x = true;")

    def test_if_non_boolean_condition(self):
        check_error("if (5) { }")

    def test_while_non_boolean_condition(self):
        check_error("while (5) { }")

    def test_break_outside_loop(self):
        check_error("break;")

    def test_return_type_mismatch(self):
        check_error("func f(): Int { return true; }")

    def test_add_non_int(self):
        check_error("let x: Int = true + 1;")

    def test_multiply_non_int(self):
        check_error("let x: Int = true * 1;")

    def test_less_than_non_int(self):
        check_error("let b: Boolean = true < 1;")

    def test_equals_type_mismatch(self):
        check_error("let b: Boolean = 1 == true;")

    def test_new_unknown_struct(self):
        check_error("let x: Foo = new Foo {};")

    def test_new_missing_field(self):
        check_error("struct Point { x: Int, y: Int } let p: Point = new Point { x: 1 };")

    def test_new_unknown_field(self):
        check_error("struct Point { x: Int } let p: Point = new Point { x: 1, z: 2 };")

    def test_new_field_type_mismatch(self):
        check_error("struct Point { x: Int } let p: Point = new Point { x: true };")

    def test_struct_no_such_field(self):
        check_error("struct Point { x: Int } let p: Point = new Point { x: 1 }; let n: Int = p.z;")

    def test_duplicate_struct(self):
        check_error("struct A { } struct A { }")

    def test_duplicate_trait(self):
        check_error("trait T { } trait T { }")

    def test_duplicate_func(self):
        check_error("func f(): Void { } func f(): Void { }")

    def test_impl_unknown_trait(self):
        check_error("impl UnknownTrait for Int { }")

    def test_impl_missing_method(self):
        check_error("""
            trait T { method foo(): Int; }
            impl T for Int { }
        """)

    def test_impl_extra_method(self):
        check_error("""
            trait T { }
            impl T for Int { method foo(): Int { return 1; } }
        """)

    def test_impl_return_type_mismatch(self):
        check_error("""
            trait T { method foo(): Int; }
            impl T for Int { method foo(): Boolean { return true; } }
        """)

    def test_impl_param_type_mismatch(self):
        check_error("""
            trait T { method foo(other: Self): Self; }
            impl T for Int { method foo(other: Boolean): Int { return self; } }
        """)

    def test_self_outside_method(self):
        check_error("self;")

    def test_duplicate_impl(self):
        check_error("""
            trait T { }
            impl T for Int { }
            impl T for Int { }
        """)

    def test_struct_unknown_field_type(self):
        check_error("struct S { x: Unknown }")

    def test_self_type_in_struct_field(self):
        check_error("struct S { x: Self }")

    def test_method_on_non_struct(self):
        check_error("""
            trait T { method foo(): Int; }
            let x: Int = 5;
            let y: Int = x.foo();
        """)

    def test_wrong_arg_count_method(self):
        check_error("""
            trait T { method foo(other: Self): Self; }
            impl T for Int { method foo(other: Int): Int { return self; } }
            let x: Int = 5;
            let y: Int = x.foo(1, 2);
        """)

    def test_wrong_arg_type_method(self):
        check_error("""
            trait T { method foo(other: Self): Self; }
            impl T for Int { method foo(other: Int): Int { return self; } }
            let x: Int = 5;
            let y: Int = x.foo(true);
        """)

    def test_duplicate_struct_field(self):
        check_error("struct S { x: Int, x: Boolean }")

    def test_impl_param_count_mismatch(self):
        check_error("""
            trait T { method foo(a: Self, b: Self): Self; }
            impl T for Int { method foo(a: Int): Int { return self; } }
        """)

class TestAdditionalCoverage:

    def test_duplicate_method_in_trait(self):
        env = GlobalEnvironment()
        trait = TraitDef(
            traitname="T",
            abs_methoddef=[
                AbsMethodDef(var="foo", comma_param=[], type=IntType()),
                AbsMethodDef(var="foo", comma_param=[], type=IntType()),
            ]
        )
        with pytest.raises(TypeError):
            env.register_trait(trait)

    def test_impl_for_int_method_on_int_dot(self):
        check("""
            trait Printable { method show(): Void; }
            impl Printable for Int {
                method show(): Void { println(self); }
            }
            let x: Int = 5;
            x.show();
        """)

class TestMoreCoverage:

    def test_duplicate_method_in_impl(self):
        check_error("""
            trait T { method foo(): Int; method bar(): Int; }
            impl T for Int {
                method foo(): Int { return self; }
                method foo(): Int { return self; }
            }
        """)

    def test_resolve_self_function_type(self):
        check("""
            trait T { method apply(f: (Self) => Self): Self; }
            impl T for Int { method apply(f: (Int) => Int): Int { return self; } }
        """)

    def test_dot_chain_non_struct_receiver_raises(self):
        check_error("""
            let x: Int = 5;
            let y: Int = x.foo.bar();
        """)

    def test_func_wrong_arg_count(self):
        check_error("func f(a: Int, b: Int): Int { return a; } let x: Int = f(1);")

    def test_func_wrong_arg_type(self):
        check_error("func f(a: Int): Int { return a; } let x: Int = f(true);")

    def test_require_known_type_unknown_struct_in_return(self):
        check_error("func f(): Unknown { }")

    def test_require_known_type_trait_function_type(self):
        check("""
            trait T { method apply(f: (Self) => Int): Int; }
            impl T for Int { method apply(f: (Int) => Int): Int { return self; } }
        """)

    def test_require_known_type_trait_unknown_struct_in_function(self):
        check_error("""
            trait T { method foo(f: (Unknown) => Int): Int; }
        """)

    def test_dot_chain_struct_missing_field_in_receiver(self):
        check_error("""
            struct Inner { val: Int }
            struct Outer { inner: Inner }
            let o: Outer = new Outer { inner: new Inner { val: 1 } };
            let x: Int = o.missing.val;
        """)

    def test_method_on_boolean_type(self):
        check("""
            trait Flip { method flip(): Self; }
            impl Flip for Boolean { method flip(): Boolean { return self; } }
            let b: Boolean = true;
            let c: Boolean = b.flip();
        """)

    def test_method_not_found_on_boolean(self):
        check_error("let b: Boolean = true; let x: Int = b.missing();")

    def test_method_not_found_on_int(self):
        check_error("let x: Int = 5; let y: Int = x.missing();")

    def test_method_access_on_function_type_raises(self):
        check_error("func f(): Int { return 1; } let x: Int = f.missing;")

    def test_func_called_with_args(self):
        check("func add(a: Int, b: Int): Int { return a; } let x: Int = add(1, 2);")

    def test_higher_order_func_wrong_arg_count(self):
        check_error("func apply(f: (Int) => Int, x: Int): Int { return f(x, x); }")

    def test_higher_order_func_wrong_arg_type(self):
        check_error("func apply(f: (Int) => Int, x: Boolean): Int { return f(x); }")

    def test_var_resolves_to_func_type(self):
        check("func double(x: Int): Int { return x; } let f: (Int) => Int = double;")

    def test_less_than_right_non_int(self):
        check_error("let b: Boolean = 1 < true;")

    def test_add_rhs_non_int(self):
        check_error("let x: Int = 1 + true;")

    def test_mult_lhs_non_int(self):
        check_error("let x: Int = true * 2;")

    def test_mult_rhs_non_int(self):
        check_error("let x: Int = 2 * true;")

    def test_require_known_type_function_type(self):
        check("func f(g: (Int) => Boolean): Void { }")

    def test_require_known_type_unknown_struct_in_func(self):
        check_error("func f(x: Unknown): Void { }")