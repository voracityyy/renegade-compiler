from __future__ import annotations
from typing import List, Optional, Dict, Tuple
from nodes import (
    Node, Type, Stmt, Exp, PrimaryExp, ProgramItem,
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


# TypeError definition
class TypeError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


# Check if two node types are equal
def is_types_equal(a: Type, b: Type) -> bool:
    # Different class check
    if type(a) != type(b):
        return False
    # Built-in types check, previous gaurantees they are the same type
    if isinstance(a, IntType) or isinstance(a, VoidType) or isinstance(a, BooleanType) or isinstance(a, SelfType):
        return True
    # Structs: a & b are only equal if they are same struct
    if isinstance(a, StructType):
        assert isinstance(b, StructType)
        return a.structname == b.structname
    # Functions: a & b are only equal if parameters and return type match
    # We do not check for function name because they are not valid types.
    if isinstance(a, FunctionType):
        assert isinstance(b, FunctionType)
        if len(a.comma_type) != len(b.comma_type):
            return False
        for ta, tb in zip(a.comma_type, b.comma_type):
            if not is_types_equal(ta, tb):
                return False
        return is_types_equal(a.type, b.type)
    raise TypeError(f"Type equality mismatch: expected {type_to_string(type(a))}, got {type_to_string(type(b))}")


# Define strings for TypeErrors
def type_to_string(t: Type) -> str:
    if isinstance(t, IntType):
        return "Int"
    if isinstance(t, VoidType):
        return "Void"
    if isinstance(t, BooleanType):
        return "Boolean"
    if isinstance(t, SelfType):
        return "Self"
    if isinstance(t, StructType):
        return t.structname
    if isinstance(t, FunctionType):
        params = ", ".join(type_to_string(param) for param in t.comma_type)
        return f"({params}) => {type_to_string(t.type)}"
    return repr(t)


# For type checking local scope / variables
class Environment:

    def __init__(self, parent: Optional[Environment] = None) -> None:
        self._var_type_dict: Dict[str, Type] = {}
        self._parent = parent

    def lookup(self, var: str) -> Optional[Type]:
        if var in self._var_type_dict:
            return self._var_type_dict[var]
        if self._parent:
            return self._parent.lookup(var)
        return None

    def bind(self, var: str, t: Type) -> None:
        self._var_type_dict[var] = t

    def child(self) -> Environment:
        return Environment(parent=self)


# For type checking global scope / variables
class GlobalEnvironment:

    def __init__(self) -> None:
        self.struct_fields: Dict[str, List[Param]] = {}
        self.trait_methods: Dict[str, Dict[str, AbsMethodDef]] = {}
        self.impl_table: Dict[Tuple[str, str], Dict[str, ConcMethodDef]] = {}
        self.func_defs: Dict[str, FuncDef] = {}

    # Register the above fields / instance variables
    def register_struct(self, struct_def: StructDef) -> None:
        if struct_def.structname in self.struct_fields:
            raise TypeError(f"Duplicate struct definition: {struct_def.structname}")
        self.struct_fields[struct_def.structname] = struct_def.comma_param

    def register_trait(self, trait_def: TraitDef) -> None:
        if trait_def.traitname in self.trait_methods:
            raise TypeError(f"Duplicate trait definition: {trait_def.traitname}")
        methods: Dict[str, AbsMethodDef] = {}
        for method in trait_def.abs_methoddef:
            if method.var in methods:
                raise TypeError(f"Duplicate method {method} in trait {trait_def.traitname}")
            methods[method.var] = method
        self.trait_methods[trait_def.traitname] = methods

    def register_impl(self, impl_def: ImplDef) -> None:
        if impl_def.traitname not in self.trait_methods:
            raise TypeError(f"Implementation for unknown trait {impl_def.traitname}"
                            )
        key = (impl_def.traitname, type_to_string(impl_def.type))
        if key in self.impl_table:
            raise TypeError(f"Duplicate implementation of trait {impl_def.traitname} for type {type_to_string(impl_def.type)}")
        
        methods: Dict[str, ConcMethodDef] = {}
        for method in impl_def.conc_methoddef:
            if method.var in methods:
                raise TypeError(f"Duplicate method {method.var} in implementation {impl_def.traitname} for {type_to_string(impl_def.type)}")
            methods[method.var] = method
        self.impl_table[key] = methods

    def register_func(self, func_def: FuncDef) -> None:
        if func_def.var in self.func_defs:
            raise TypeError(f"Duplicate function definition: {func_def.var}")
        self.func_defs[func_def.var] = func_def

    # Lookup the above fields / instance variables
    def get_struct_fields(self, structname: str) -> List[Param]:
        if structname not in self.struct_fields:
            raise TypeError(f"Unknown struct: {structname}")
        return self.struct_fields[structname]

    def lookup_func(self, name: str) -> Optional[FuncDef]:
        return self.func_defs.get(name)

    def lookup_method_on_type(self, receiver_type: Type, method_name: str) -> Optional[ConcMethodDef]:
        receiver_type_string = type_to_string(receiver_type)
        # Use _ just for iteration
        for (_, impl_type_string), methods in self.impl_table.items():
            if impl_type_string == receiver_type_string and method_name in methods:
                return methods[method_name]
        return None
    

# Main typechecker class
class Typechecker:

    def __init__(self, program: Program) -> None:
        self._program = program
        self._global_env = GlobalEnvironment()

    # Typecheck the entire program
    def typecheck(self) -> None:
        self._first_pass()
        self._check_program_items()
        self._check_entry_stmts()

    # First pass / collect declarations
    def _first_pass(self) -> None:
        for item in self._program.program_item:
            if isinstance(item, StructDef):
                self._global_env.register_struct(item)
            elif isinstance(item, TraitDef):
                self._global_env.register_trait(item)
            elif isinstance(item, ImplDef):
                pass
            elif isinstance(item, FuncDef):
                self._global_env.register_func(item)

        # Register implementations second (guarantees traits and struct types exist beforehand)
        for item in self._program.program_item:
            if isinstance(item, ImplDef):
                self._global_env.register_impl(item)

    # Check program items
    def _check_program_items(self) -> None:
        for item in self._program.program_item:
            if isinstance(item, StructDef):
                self._check_structdef(item)
            elif isinstance(item, TraitDef):
                self._check_traitdef(item)
            elif isinstance(item, ImplDef):
                self._check_impldef(item)
            elif isinstance(item, FuncDef):
                self._check_funcdef(item)

    # Check StructDef
    def _check_structdef(self, struct_def: StructDef) -> None:
        seen: set = set()
        for param in struct_def.comma_param:
            if param.var in seen:
                raise TypeError(f"Duplicate field {param.var} in struct {struct_def.structname}")
            seen.add(param.var)
            self._require_known_type(param.type, context=f"struct {struct_def.structname} field {param.var}")

    # Check TraitDef
    def _check_traitdef(self, trait_def: TraitDef) -> None:
        for method in trait_def.abs_methoddef:
            self._require_known_type_trait(method.type, context=f"trait {trait_def.traitname} method {method.var} return type")
            for param in method.comma_param:
                self._require_known_type_trait(param.type, context=f"trait {trait_def.traitname} method {method.var} param {param.var}")

    # Check ImplDef
    def _check_impldef(self, impl_def: ImplDef) -> None:
        if impl_def.traitname not in self._global_env.trait_methods:
            raise TypeError(f"Implementation references unknown trait {impl_def.traitname}")
        self._require_known_type(impl_def.type, context=f"impl {impl_def.traitname} for ...")

        concrete_type = impl_def.type
        abstract_methods = self._global_env.trait_methods[impl_def.traitname]
        impl_methods = self._global_env.impl_table[(impl_def.traitname, type_to_string(concrete_type))]

        # Every abstract method must have been implemented
        for name, abs_method in abstract_methods.items():
            if name not in impl_methods:
                raise TypeError(f"Implementation of {impl_def.traitname} for {type_to_string(concrete_type)} is missing method {name}")

        # Every concrete method must match its abstract signature
        for name, conc_method in impl_methods.items():
            if name not in abstract_methods:
                raise TypeError(f"Implementation of {impl_def.traitname} for {type_to_string(concrete_type)} defines method {name} not in trait")
            abs_method = abstract_methods[name]

            # Check param count
            if len(conc_method.comma_param) != len(abs_method.comma_param):
                raise TypeError(f"Method {name} in implementation of {impl_def.traitname} for {type_to_string(concrete_type)}: parameter count mismatch")

            # Check param types (Self in abstract -> concrete type in impl)
            for i, (conc_param, abs_param) in enumerate(zip(conc_method.comma_param, abs_method.comma_param)):
                expected = self._resolve_self(abs_param.type, concrete_type)
                actual = conc_param.type
                if not is_types_equal(expected, actual):
                    raise TypeError(f"Method {name} in impl of {impl_def.traitname} for {type_to_string(concrete_type)}: parameter {i} type mismatch: "
                                    f"expected {type_to_string(expected)}, got {type_to_string(actual)}"
                    )

            # Check return type (Self in abstract -> concrete type in impl)
            expected_return_type = self._resolve_self(abs_method.type, concrete_type)
            actual_return_type = conc_method.type
            if not is_types_equal(expected_return_type, actual_return_type):
                raise TypeError(
                                f"Method {name} in implementation of {impl_def.traitname} for {type_to_string(concrete_type)}: return type mismatch: "
                                f"expected {type_to_string(expected_return_type)}, got {type_to_string(actual_return_type)}"
                )

            # Typecheck the inside body
            environment = Environment()
            environment.bind("self", concrete_type)
            
            for param in conc_method.comma_param:
                environment.bind(param.var, param.type)
                
            self._check_stmts(conc_method.stmt, environment, expected_return_type=conc_method.type, in_loop=False, self_type=concrete_type)

    # Check FuncDef
    def _check_funcdef(self, func_def: FuncDef) -> None:
        self._require_known_type(func_def.type, context=f"function {func_def.var} return type")
        environment = Environment()
        
        for param in func_def.comma_param:
            self._require_known_type(param.type, context=f"function {func_def.var} param {param.var}")
            environment.bind(param.var, param.type)
            
        self._check_stmts(func_def.stmt, environment, expected_return_type=func_def.type, in_loop=False, self_type=None)

    # Check Entry Statements
    def _check_entry_stmts(self) -> None:
        environment = Environment()
        
        for name, func_def in self._global_env.func_defs.items():
            param_types = [param.type for param in func_def.comma_param]
            environment.bind(name, FunctionType(comma_type=param_types, type=func_def.type))
        
        self._check_stmts(self._program.stmt, environment, expected_return_type=VoidType(), in_loop=False, self_type=None)

    # Check Statements
    def _check_stmts(self, stmts: List[Stmt], environment: Environment, expected_return_type: Type, in_loop: bool, self_type: Optional[Type]) -> None:
        for stmt in stmts:
            self._check_stmt(stmt, environment, expected_return_type, in_loop, self_type)

    # Check Statement
    def _check_stmt( self, stmt: Stmt, environment: Environment, expected_return_type: Type, in_loop: bool, self_type: Optional[Type]) -> None:

        # let param = exp;
        if isinstance(stmt, LetStmt):
            self._require_known_type(stmt.param.type, context=f"let {stmt.param.var}")
            exp_type = self._check_exp(stmt.exp, environment, self_type)
            if not is_types_equal(stmt.param.type, exp_type):
                raise TypeError(f"let {stmt.param.var}: declared type {type_to_string(stmt.param.type)} but expression has type {type_to_string(exp_type)}")
            environment.bind(stmt.param.var, stmt.param.type)
            return

        # var = exp;
        if isinstance(stmt, AssignStmt):
            existing = environment.lookup(stmt.var)
            if existing is None:
                raise TypeError(f"Assignment to undeclared variable {stmt.var}")
            exp_type = self._check_exp(stmt.exp, environment, self_type)
            if not is_types_equal(existing, exp_type):
                raise TypeError(f"Assignment to {stmt.var}: variable has type {type_to_string(existing)} but expression has type {type_to_string(exp_type)}")
            return

        # if (exp) stmt [else stmt]
        if isinstance(stmt, IfStmt):
            cond_type = self._check_exp(stmt.exp, environment, self_type)
            if not is_types_equal(cond_type, BooleanType()):
                raise TypeError(f"if condition must be Boolean, got {type_to_string(cond_type)}")
            self._check_stmt(stmt.then_condition, environment.child(), expected_return_type, in_loop, self_type)
            if stmt.else_condition is not None:
                self._check_stmt(stmt.else_condition, environment.child(), expected_return_type, in_loop, self_type)
            return

        # while (exp) stmt
        if isinstance(stmt, WhileStmt):
            cond_type = self._check_exp(stmt.exp, environment, self_type)
            if not is_types_equal(cond_type, BooleanType()):
                raise TypeError(f"while condition must be Boolean, got {type_to_string(cond_type)}")
            self._check_stmt(stmt.stmt, environment.child(), expected_return_type, in_loop=True, self_type=self_type)
            return

        # break;
        if isinstance(stmt, BreakStmt):
            if not in_loop:
                raise TypeError("break used outside of a loop")
            return

        # println (exp)
        if isinstance(stmt, PrintlnStmt):
            self._check_exp(stmt.exp, environment, self_type)
            return

        # {stmt*}
        if isinstance(stmt, BlockStmt):
            child_env = environment.child()
            self._check_stmts(stmt.stmt, child_env, expected_return_type, in_loop, self_type)
            return

        # return [exp];
        if isinstance(stmt, ReturnStmt):
            if stmt.exp is None:
                actual = VoidType()
            else:
                actual = self._check_exp(stmt.exp, environment, self_type)
            if not is_types_equal(actual, expected_return_type):
                raise TypeError(f"return type mismatch: expected {type_to_string(expected_return_type)}, got {type_to_string(actual)}")
            return

        # exp;
        if isinstance(stmt, ExpStmt):
            self._check_exp(stmt.exp, environment, self_type)
            return

        raise TypeError(f"Unknown statement type: {type(stmt)}")


    # Check expression
    def _check_exp(self, exp: Exp, environment: Environment, self_type: Optional[Type]) -> Type:
        # equals_exp ::= less_than_exp [( == | != ) less_than_exp]
        if isinstance(exp, EqualsExp):
            left_type = self._check_less_than_exp(exp.less_than_exp_left, environment, self_type)
            if exp.op is not None:
                right_type = self._check_less_than_exp(exp.less_than_exp_right, environment, self_type)
                if not is_types_equal(left_type, right_type):
                    raise TypeError(f"Equality operator operands must have the same type: {type_to_string(left_type)} vs {type_to_string(right_type)}")
                return BooleanType()
            return left_type
        if isinstance(exp, LessThanExp):
            return self._check_less_than_exp(exp, environment, self_type)
        if isinstance(exp, AddExp):
            return self._check_add_exp(exp, environment, self_type)
        if isinstance(exp, MultExp):
            return self._check_mult_exp(exp, environment, self_type)
        if isinstance(exp, CallExp):
            return self._check_call_exp(exp, environment, self_type)
        if isinstance(exp, DotExp):
            return self._check_dot_exp_type(exp, environment, self_type)

        # Primary expressions
        return self._check_primary_exp(exp, environment, self_type)

    def _check_less_than_exp(self, exp: LessThanExp, environment: Environment, self_type: Optional[Type]) -> Type:
        left_type = self._check_add_exp(exp.add_exp_left, environment, self_type)
        if exp.add_exp_right is not None:
            if not is_types_equal(left_type, IntType()):
                raise TypeError(f"< requires Int operands, got {type_to_string(left_type)} on left")
            right_type = self._check_add_exp(exp.add_exp_right, environment, self_type)
            if not is_types_equal(right_type, IntType()):
                raise TypeError(f"< requires Int operands, got {type_to_string(right_type)} on right")
            return BooleanType()
        return left_type

    def _check_add_exp(self, exp: AddExp, environment: Environment, self_type: Optional[Type]) -> Type:
        result_type = self._check_mult_exp(exp.mult_exp_left, environment, self_type)
        for (_, rhs) in exp.mult_exp_right:
            if not is_types_equal(result_type, IntType()):
                raise TypeError(f"+ and - requires Int operands, got {type_to_string(result_type)}")
            rhs_type = self._check_mult_exp(rhs, environment, self_type)
            if not is_types_equal(rhs_type, IntType()):
                raise TypeError(f"+ and - requires Int operands, got {type_to_string(rhs_type)}")
            result_type = IntType()
        return result_type

    def _check_mult_exp(self, exp: MultExp, environment: Environment, self_type: Optional[Type]) -> Type:
        result_type = self._check_call_exp(exp.call_exp_left, environment, self_type)
        for (_, rhs) in exp.call_exp_right:
            if not is_types_equal(result_type, IntType()):
                raise TypeError(f"* and / requires Int operands, got {type_to_string(result_type)}")
            rhs_type = self._check_call_exp(rhs, environment, self_type)
            if not is_types_equal(rhs_type, IntType()):
                raise TypeError(f"* and / requires Int operands, got {type_to_string(rhs_type)}")
            result_type = IntType()
        return result_type

    def _check_call_exp(self, exp: CallExp, environment: Environment, self_type: Optional[Type]) -> Type:
        # call_exp ::= dot_exp (`(`comma_exp`)`)*
        dot_type = self._check_dot_exp_type(exp.dot_exp, environment, self_type)
        if not exp.comma_exp:
            return dot_type
        current_type = dot_type
        for i, arg_list in enumerate(exp.comma_exp):
            current_type = self._apply_call(current_type, arg_list, exp.dot_exp, i, environment, self_type)
        return current_type


    # Handle different calling layers
    def _apply_call(self, callee_type: Type, arg_list: List[Exp], dot_exp: DotExp, call_index: int, environment: Environment, self_type: Optional[Type]) -> Type:
        
        arg_types = [self._check_exp(a, environment, self_type) for a in arg_list]

        # Calling a higher-order function value
        if isinstance(callee_type, FunctionType):
            if len(arg_types) != len(callee_type.comma_type):
                raise TypeError(f"Function expects {len(callee_type.comma_type)} argument(s), got {len(arg_types)}")
            for j, (arg_type, expected_type) in enumerate(zip(arg_types, callee_type.comma_type)):
                if not is_types_equal(arg_type, expected_type):
                    raise TypeError(f"Argument {j} type mismatch: expected {type_to_string(expected_type)}, got {type_to_string(arg_type)}")
            return callee_type.type

        # Calling a function by name
        if call_index == 0 and not dot_exp.var:
            primary = dot_exp.primary_exp
            if isinstance(primary, VarExp):
                func_def = self._global_env.lookup_func(primary.var)
                if func_def is not None:
                    return self._check_func_call(func_def, arg_types, primary.var)

        # Method call via dot chain calls
        if dot_exp.var:
            method_name = dot_exp.var[-1]
            receiver_type = self._dot_exp_receiver_type(dot_exp, environment, self_type)
            method = self._global_env.lookup_method_on_type(receiver_type, method_name)
            if method is None:
                raise TypeError(f"No method {method_name} found for type {type_to_string(receiver_type)}")
            return self._check_method_call(method, arg_types, method_name, receiver_type)


    def _check_func_call(self, func_def: FuncDef, arg_types: List[Type], func_name: str) -> Type:
        if len(arg_types) != len(func_def):
            raise TypeError(f"Function {func_name} expects {len(func_def.comma_param)} argument(s), got {len(arg_types)}")
        for j, (arg_type, param) in enumerate(zip(arg_types, func_def.comma_param)):
            if not is_types_equal(arg_type, param.type):
                raise TypeError(f"Function {func_name} argument {j}: expected {type_to_string(param.type)}, got {type_to_string(arg_type)}")
            
        return func_def.type
    

    def _check_method_call(self, method: ConcMethodDef, arg_types: List[Type], method_name: str, receiver_type: Type) -> Type:
        if len(arg_types) != len(method.comma_param):
            raise TypeError(f"Method {method_name} on {type_to_string(receiver_type)} expects {len(method.comma_param)} argument(s), got {len(arg_types)}")
        for j, (arg_type, param) in enumerate(zip(arg_types, method.comma_param)):
            if not is_types_equal(arg_type, param.type):
                raise TypeError(
                    f"Method {method_name} on {type_to_string(receiver_type)} argument {j}: expected {type_to_string(param.type)}, got {type_to_string(arg_type)}")
                
        return method.type


    # Check DotExp type
    def _check_dot_exp_type(self, dot_exp: DotExp, environment: Environment, self_type: Optional[Type]) -> Type:
        # dot_exp ::= primary_exp (`.`var)*
        current_type = self._check_primary_exp(dot_exp.primary_exp, environment, self_type)
        
        for field_or_method in dot_exp.var:
            if isinstance(current_type, StructType):
                struct_fields = self._global_env.get_struct_fields(current_type.structname)
                field_match = next((param.type for param in struct_fields if param.var == field_or_method), None)
                if field_match is not None:
                    current_type = field_match
                    continue
                method = self._global_env.lookup_method_on_type(current_type, field_or_method)
                if method is not None:
                    param_types = [param.type for param in method.comma_param]
                    current_type = FunctionType(comma_type=param_types, type=method.type)
                    continue
                raise TypeError(f"Struct {current_type.structname} has no field or method {field_or_method}")
            elif isinstance(current_type, IntType):
                method = self._global_env.lookup_method_on_type(current_type, field_or_method)
                if method is not None:
                    param_types = [param.type for param in method.comma_param]
                    current_type = FunctionType(comma_type=param_types, type=method.type)
                    continue
                raise TypeError(f"Type Int has no method {field_or_method}")
            elif isinstance(current_type, BooleanType):
                method = self._global_env.lookup_method_on_type(current_type, field_or_method)
                if method is not None:
                    param_types = [param.type for param in method.comma_param]
                    current_type = FunctionType(comma_type=param_types, type=method.type)
                    continue
                raise TypeError(f"Type Boolean has no method {field_or_method}")
            else:
                raise TypeError(f"Cannot access field/method {field_or_method} on type {type_to_string(current_type)}")

        return current_type

    # Get DotExp receiver type
    def _dot_exp_receiver_type(self, dot_exp: DotExp, environment: Environment, self_type: Optional[Type]) -> Type:
        
        current_type = self._check_primary_exp(dot_exp.primary_exp, environment, self_type)
        accesses = dot_exp.var

        for field_or_method in accesses[:-1]:
            if isinstance(current_type, StructType):
                struct_fields = self._global_env.get_struct_fields(current_type.structname)
                field_match = next((param.type for param in struct_fields if param.var == field_or_method), None)
                if field_match is not None:
                    current_type = field_match
                    continue
                method = self._global_env.lookup_method_on_type(current_type, field_or_method)
                if method is not None:
                    current_type = method.type
                    continue
                raise TypeError(f"Struct {current_type.structname} has no field or method {field_or_method}")
            else:
                raise TypeError(f"Cannot access field/method on type {type_to_string(current_type)}")
            
        return current_type


    # Check PrimaryExp
    def _check_primary_exp(self, exp: PrimaryExp, environment: Environment, self_type: Optional[Type]) -> Type:
        # i
        if isinstance(exp, IntExp):
            return IntType()
        # true or false
        if isinstance(exp, BooleanExp):
            return BooleanType()
        # self
        if isinstance(exp, SelfExp):
            if self_type is None:
                raise TypeError("self used outside of a method")
            return self_type
        # var
        if isinstance(exp, VarExp):
            t = environment.lookup(exp.var)
            if t is not None:
                return t
            func_def = self._global_env.lookup_func(exp.var)
            if func_def is not None:
                param_types = [param.type for param in func_def.comma_param]
                return FunctionType(comma_type=param_types, type=func_def.type)
            raise TypeError(f"Undeclared variable {exp.var}")

        # (exp)
        if isinstance(exp, ParenExp):
            return self._check_exp(exp.exp, environment, self_type)

        # new structname {struct_actual_params}
        if isinstance(exp, NewExp):
            if exp.structname not in self._global_env.struct_fields:
                raise TypeError(f"Unknown struct {exp.structname} in new expression")
            fields = self._global_env.get_struct_fields(exp.structname)
            provided = {sap.var: sap for sap in exp.struct_actual_params}

            for field in fields:
                if field.var not in provided:
                    raise TypeError(f"new {exp.structname}: missing field {field.var}")
                actual_type = self._check_exp(provided[field.var].exp, environment, self_type)
                if not is_types_equal(field.type, actual_type):
                    raise TypeError(f"new {exp.structname}: field '{field.var}' expects {type_to_string(field.type)}, got {type_to_string(actual_type)}")

            declared_names = {f.var for f in fields}
            for name in provided:
                if name not in declared_names:
                    raise TypeError(f"new {exp.structname}: unknown field {name}")

            return StructType(structname=exp.structname)


    # Helper functions
    def _resolve_self(self, t: Type, concrete: Type) -> Type:
        if isinstance(t, SelfType):
            return concrete
        if isinstance(t, FunctionType):
            return FunctionType(comma_type=[self._resolve_self(p, concrete) for p in t.comma_type], type=self._resolve_self(t.type, concrete))
        return t

    def _require_known_type(self, t: Type, context: str) -> None:
        if isinstance(t, SelfType):
            raise TypeError(f"{context}: Self type is only valid inside a trait definition")
        if isinstance(t, StructType):
            if t.structname not in self._global_env.struct_fields:
                raise TypeError(f"{context}: unknown type {t.structname}")
        if isinstance(t, FunctionType):
            for param in t.comma_type:
                self._require_known_type(param, context)
            self._require_known_type(t.type, context)

    def _require_known_type_trait(self, t: Type, context: str) -> None:
        if isinstance(t, SelfType):
            return
        if isinstance(t, StructType):
            if t.structname not in self._global_env.struct_fields:
                raise TypeError(f"{context}: unknown type {t.structname}")
        if isinstance(t, FunctionType):
            for param in t.comma_type:
                self._require_known_type_trait(param, context)
            self._require_known_type_trait(t.type, context)


# Typecheck the entire program
def typecheck_program(program: Program) -> None:
    Typechecker(program).typecheck()

# Entry point e.g. python typechecker.py "name of the test file")
if __name__ == "__main__":
    import sys
    from parser import parse_source

    if len(sys.argv) != 2:
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
    except OSError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    program = parse_source(source)
    typecheck_program(program)
    print("Typechecker Success")