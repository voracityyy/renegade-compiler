from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

# Base classes 
class Node: pass
class Type(Node): pass
class Stmt(Node): pass
class Exp(Node): pass
class PrimaryExp(Exp): pass
class ProgramItem(Node): pass

# Built-in types
@dataclass
class IntType(Type): pass
@dataclass
class VoidType(Type): pass
@dataclass
class BooleanType(Type): pass

# Refers to our own type in a trait 
@dataclass
class SelfType(Type): pass

# Structs are a valid kind of type
@dataclass
class StructType(Type):
    structname: str

# No need to define parenthesized types, we can ignore for parser.py to make it easier

# Higher-order function
@dataclass
class FunctionType(Type):
    comma_type: List[Type]
    type: Type

@dataclass
class Param(Node):
    var: str
    type: Type

# Instead of defining comma_param, we can just use List[Param] (list of Param objects)

@dataclass
class StructDef(ProgramItem):
    structname: str
    comma_param: List[Param]

# Definition of an abstract method
@dataclass
class AbsMethodDef(Node):
    var: str
    comma_param: List[Param]
    type: Type

# Definition of a concrete method
@dataclass
class ConcMethodDef(Node):
    var: str
    comma_param: List[Param]
    type: Type
    stmt: List[Stmt]

# Definition of a trait (typeclass)
@dataclass
class TraitDef(ProgramItem):
    traitname: str
    abs_methoddef: List[AbsMethodDef]

# Definition of an implementation of a typeclass
@dataclass
class ImplDef(ProgramItem):
    traitname: str
    type: Type
    conc_methoddef: List[ConcMethodDef]

# Definition of a toplevel function
@dataclass
class FuncDef(ProgramItem):
    var: str
    comma_param: List[Param]
    type: Type
    stmt: List[Stmt]

# Variable declaration statements
@dataclass
class LetStmt(Stmt):
    param: Param
    exp: Exp

# Assignment statements
@dataclass
class AssignStmt(Stmt):
    var: str
    exp: Exp

# If statements
@dataclass
class IfStmt(Stmt):
    exp: Exp
    then_condition: Stmt
    else_condition: Optional[Stmt] = None

# While statements
@dataclass
class WhileStmt(Stmt):
    exp: Exp
    stmt: Stmt

# Break statements
@dataclass
class BreakStmt(Stmt): pass

# Print statements
@dataclass
class PrintlnStmt(Stmt):
    exp: Exp

# Block statements
@dataclass
class BlockStmt(Stmt):
    stmt: List[Stmt]

# Return statements
@dataclass
class ReturnStmt(Stmt):
    exp: Optional[Exp] = None

# Expression statements
@dataclass
class ExpStmt(Stmt):
    exp: Exp

@dataclass
class StructActualParam(Node):
    var: str
    exp: Exp

# Instead of defining struct_actual_param, we can just use List[StructActualParam] (list of StructActualParam objects)

# Integers and variables
@dataclass
class IntExp(PrimaryExp):
    i: int
@dataclass
class VarExp(PrimaryExp):
    var: str

# Booleans
@dataclass
class BooleanExp(PrimaryExp):
    value: bool

# Instance on which we call a method
@dataclass
class SelfExp(PrimaryExp): pass

# Parenthesized expression
@dataclass
class ParenExp(PrimaryExp):
    exp: Exp

# Creates a new instance of a struct
@dataclass
class NewExp(PrimaryExp):
    structname: str
    struct_actual_params: List[StructActualParam]

# Accessing a struct field or method

# Not an actual primary expression, just needed to not break the hierarchy
@dataclass
class DotExp(PrimaryExp):
    primary_exp: PrimaryExp
    var: List[str]

@dataclass
class CallExp(Exp):
    dot_exp: DotExp
    comma_exp: List[List[Exp]]

class MultOps(Enum):
    MULT = '*'
    DIV = '/'

@dataclass
class MultExp(Exp):
    call_exp_left: CallExp
    call_exp_right: List[tuple[MultOps, CallExp]]   

class AddOps(Enum):
    ADD = '+'
    SUB = '-'

@dataclass
class AddExp(Exp):
    mult_exp_left: MultExp
    mult_exp_right: List[tuple[AddOps, MultExp]]

@dataclass
class LessThanExp(Exp):
    add_exp_left: AddExp
    add_exp_right: Optional[AddExp] = None

class EqualsOps(Enum):
    EQUALS_EQUALS = '=='
    NOT_EQUALS = '!='

@dataclass
class EqualsExp(Exp):
    less_than_exp_left: LessThanExp

    # Enforce in parser.py, if one of these is None, the other should be None too,
    op: Optional[EqualsOps] = None
    less_than_exp_right: Optional[LessThanExp] = None
    
# Program items are defined above

# Root Node / entry point
@dataclass
class Program(Node):
    program_item: List[ProgramItem]
    stmt: List[Stmt]