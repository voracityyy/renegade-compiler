from __future__ import annotations
from typing import List, Optional
from lexer import Lexer, Token, TokenKind
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

class ParseError(Exception):
    def __init__(self, message: str, line: int, col: int) -> None:
        super().__init__(f"[line {line}, col {col}] {message}")
        self.line = line
        self.col = col

class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

# Helper functions
    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        if tok.kind != TokenKind.EOF:
            self._pos += 1
        return tok

    def _check(self, kind: TokenKind) -> bool:
        return self._peek().kind == kind

    def _expect(self, kind: TokenKind) -> Token:
        tok = self._peek()
        if tok.kind != kind:
            raise ParseError(
                f"Expected {kind.name} but got {tok.kind.name} ({tok.value!r})",
                tok.line, tok.col,
            )
        return self._advance()

    def _match(self, *kinds: TokenKind) -> Optional[Token]:
        if self._peek().kind in kinds:
            return self._advance()
        return None

# Entry
    def parse(self) -> Program:
        program_items: List[ProgramItem] = []
        stmts: List[Stmt] = []

        while not self._check(TokenKind.EOF):
            if self._peek().kind in (
                TokenKind.STRUCT, TokenKind.TRAIT,
                TokenKind.IMPL, TokenKind.FUNC,
            ):
                program_items.append(self._parse_program_item())
            else:
                stmts.append(self._parse_stmt())

        return Program(program_item=program_items, stmt=stmts)

# Program items
    def _parse_program_item(self) -> ProgramItem:
        tok = self._peek()
        if tok.kind == TokenKind.STRUCT:
            return self._parse_structdef()
        if tok.kind == TokenKind.TRAIT:
            return self._parse_traitdef()
        if tok.kind == TokenKind.IMPL:
            return self._parse_impldef()
        if tok.kind == TokenKind.FUNC:
            return self._parse_funcdef()
        raise ParseError(
            f"Expected program item but got {tok.kind.name}",
            tok.line, tok.col,
        )

    def _parse_structdef(self) -> StructDef:
        self._expect(TokenKind.STRUCT)
        name = self._expect(TokenKind.IDENTIFIER).value
        self._expect(TokenKind.LBRACE)
        params = self._parse_comma_param()
        self._expect(TokenKind.RBRACE)
        return StructDef(structname=name, comma_param=params)

    def _parse_traitdef(self) -> TraitDef:
        self._expect(TokenKind.TRAIT)
        name = self._expect(TokenKind.IDENTIFIER).value
        self._expect(TokenKind.LBRACE)
        methods: List[AbsMethodDef] = []
        while not self._check(TokenKind.RBRACE):
            methods.append(self._parse_abs_methoddef())
        self._expect(TokenKind.RBRACE)
        return TraitDef(traitname=name, abs_methoddef=methods)

    def _parse_impldef(self) -> ImplDef:
        self._expect(TokenKind.IMPL)
        traitname = self._expect(TokenKind.IDENTIFIER).value
        self._expect(TokenKind.FOR)
        typ = self._parse_type()
        self._expect(TokenKind.LBRACE)
        methods: List[ConcMethodDef] = []
        while not self._check(TokenKind.RBRACE):
            methods.append(self._parse_conc_methoddef())
        self._expect(TokenKind.RBRACE)
        return ImplDef(traitname=traitname, type=typ, conc_methoddef=methods)

    def _parse_funcdef(self) -> FuncDef:
        self._expect(TokenKind.FUNC)
        name = self._expect(TokenKind.IDENTIFIER).value
        self._expect(TokenKind.LPAREN)
        params = self._parse_comma_param()
        self._expect(TokenKind.RPAREN)
        self._expect(TokenKind.COLON)
        typ = self._parse_type()
        self._expect(TokenKind.LBRACE)
        stmts = self._parse_stmts()
        self._expect(TokenKind.RBRACE)
        return FuncDef(var=name, comma_param=params, type=typ, stmt=stmts)

    # Method definitions
    def _parse_abs_methoddef(self) -> AbsMethodDef:
        self._expect(TokenKind.METHOD)
        name = self._expect(TokenKind.IDENTIFIER).value
        self._expect(TokenKind.LPAREN)
        params = self._parse_comma_param()
        self._expect(TokenKind.RPAREN)
        self._expect(TokenKind.COLON)
        typ = self._parse_type()
        self._expect(TokenKind.SEMICOLON)
        return AbsMethodDef(var=name, comma_param=params, type=typ)

    def _parse_conc_methoddef(self) -> ConcMethodDef:
        self._expect(TokenKind.METHOD)
        name = self._expect(TokenKind.IDENTIFIER).value
        self._expect(TokenKind.LPAREN)
        params = self._parse_comma_param()
        self._expect(TokenKind.RPAREN)
        self._expect(TokenKind.COLON)
        typ = self._parse_type()
        self._expect(TokenKind.LBRACE)
        stmts = self._parse_stmts()
        self._expect(TokenKind.RBRACE)
        return ConcMethodDef(var=name, comma_param=params, type=typ, stmt=stmts)

    # Types
    def _parse_type(self) -> Type:
        tok = self._peek()

        if tok.kind == TokenKind.INT_TYPE:
            self._advance()
            return IntType()
        if tok.kind == TokenKind.VOID_TYPE:
            self._advance()
            return VoidType()
        if tok.kind == TokenKind.BOOLEAN_TYPE:
            self._advance()
            return BooleanType()
        if tok.kind == TokenKind.SELF_TYPE:
            self._advance()
            return SelfType()

        # Identifier
        if tok.kind == TokenKind.IDENTIFIER:
            self._advance()
            return StructType(structname=tok.value)

        # Parenthesized type OR higher-order function type
        if tok.kind == TokenKind.LPAREN:
            self._advance()
            types = self._parse_comma_type()
            self._expect(TokenKind.RPAREN)
            if self._check(TokenKind.FAT_ARROW):
                self._advance()
                return_type = self._parse_type()
                return FunctionType(comma_type=types, type=return_type)
            else:
                if len(types) != 1:
                    raise ParseError(
                        "Parenthesized type must contain exactly one type",
                        tok.line, tok.col,
                    )
                return types[0]

        raise ParseError(
            f"Expected type but got {tok.kind.name} ({tok.value!r})",
            tok.line, tok.col,
        )

    def _parse_comma_type(self) -> List[Type]:
        types: List[Type] = []
        if self._check(TokenKind.RPAREN):
            return types
        types.append(self._parse_type())
        while self._match(TokenKind.COMMA):
            types.append(self._parse_type())
        return types

    # Params
    def _parse_param(self) -> Param:
        tok = self._peek()
        if tok.kind in (TokenKind.IDENTIFIER, TokenKind.SELF):
            name = self._advance().value
        else:
            raise ParseError(
                f"Expected parameter name but got {tok.kind.name} ({tok.value!r})",
                tok.line, tok.col,
            )
        self._expect(TokenKind.COLON)
        typ = self._parse_type()
        return Param(var=name, type=typ)

    def _parse_comma_param(self) -> List[Param]:
        params: List[Param] = []
        if self._check(TokenKind.RPAREN) or self._check(TokenKind.RBRACE):
            return params
        params.append(self._parse_param())
        while self._match(TokenKind.COMMA):
            params.append(self._parse_param())
        return params

    # Statements
    def _parse_stmts(self) -> List[Stmt]:
        stmts: List[Stmt] = []
        while not self._check(TokenKind.RBRACE) and not self._check(TokenKind.EOF):
            stmts.append(self._parse_stmt())
        return stmts

    def _parse_stmt(self) -> Stmt:
        tok = self._peek()

        if tok.kind == TokenKind.LET:
            self._advance()
            param = self._parse_param()
            self._expect(TokenKind.EQUALS)
            exp = self._parse_exp()
            self._expect(TokenKind.SEMICOLON)
            return LetStmt(param=param, exp=exp)

        if tok.kind == TokenKind.IF:
            self._advance()
            self._expect(TokenKind.LPAREN)
            exp = self._parse_exp()
            self._expect(TokenKind.RPAREN)
            then_body = self._parse_stmt()
            else_body: Optional[Stmt] = None
            if self._match(TokenKind.ELSE):
                else_body = self._parse_stmt()
            return IfStmt(exp=exp, then_condition=then_body, else_condition=else_body)

        if tok.kind == TokenKind.WHILE:
            self._advance()
            self._expect(TokenKind.LPAREN)
            exp = self._parse_exp()
            self._expect(TokenKind.RPAREN)
            body = self._parse_stmt()
            return WhileStmt(exp=exp, stmt=body)

        if tok.kind == TokenKind.BREAK:
            self._advance()
            self._expect(TokenKind.SEMICOLON)
            return BreakStmt()

        if tok.kind == TokenKind.PRINTLN:
            self._advance()
            self._expect(TokenKind.LPAREN)
            exp = self._parse_exp()
            self._expect(TokenKind.RPAREN)
            self._expect(TokenKind.SEMICOLON)
            return PrintlnStmt(exp=exp)

        if tok.kind == TokenKind.LBRACE:
            self._advance()
            stmts = self._parse_stmts()
            self._expect(TokenKind.RBRACE)
            return BlockStmt(stmt=stmts)

        if tok.kind == TokenKind.RETURN:
            self._advance()
            exp = None
            if not self._check(TokenKind.SEMICOLON):
                exp = self._parse_exp()
            self._expect(TokenKind.SEMICOLON)
            return ReturnStmt(exp=exp)

        if tok.kind == TokenKind.IDENTIFIER and self._lookahead_is_assign():
            name = self._advance().value
            self._expect(TokenKind.EQUALS)
            exp = self._parse_exp()
            self._expect(TokenKind.SEMICOLON)
            return AssignStmt(var=name, exp=exp)

        exp = self._parse_exp()
        self._expect(TokenKind.SEMICOLON)
        return ExpStmt(exp=exp)

    def _lookahead_is_assign(self) -> bool:
        if self._pos + 1 >= len(self._tokens):
            return False
        next_tok = self._tokens[self._pos + 1]
        return next_tok.kind == TokenKind.EQUALS

    # Expressions
    def _parse_exp(self) -> Exp:
        return self._parse_equals_exp()

    def _parse_equals_exp(self) -> EqualsExp:
        left = self._parse_less_than_exp()
        op: Optional[EqualsOps] = None
        right: Optional[LessThanExp] = None
        if self._check(TokenKind.EQUALS_EQUALS):
            self._advance()
            op = EqualsOps.EQUALS_EQUALS
            right = self._parse_less_than_exp()
        elif self._check(TokenKind.NOT_EQUALS):
            self._advance()
            op = EqualsOps.NOT_EQUALS
            right = self._parse_less_than_exp()
        return EqualsExp(less_than_exp_left=left, op=op, less_than_exp_right=right)

    def _parse_less_than_exp(self) -> LessThanExp:
        left = self._parse_add_exp()
        right: Optional[AddExp] = None
        if self._match(TokenKind.LESS_THAN):
            right = self._parse_add_exp()
        return LessThanExp(add_exp_left=left, add_exp_right=right)

    def _parse_add_exp(self) -> AddExp:
        left = self._parse_mult_exp()
        rights: List[tuple[AddOps, MultExp]] = []
        while True:
            if self._check(TokenKind.PLUS):
                self._advance()
                rights.append((AddOps.ADD, self._parse_mult_exp()))
            elif self._check(TokenKind.MINUS):
                self._advance()
                rights.append((AddOps.SUB, self._parse_mult_exp()))
            else:
                break
        return AddExp(mult_exp_left=left, mult_exp_right=rights)

    def _parse_mult_exp(self) -> MultExp:
        left = self._parse_call_exp()
        rights: List[tuple[MultOps, CallExp]] = []
        while True:
            if self._check(TokenKind.STAR):
                self._advance()
                rights.append((MultOps.MULT, self._parse_call_exp()))
            elif self._check(TokenKind.SLASH):
                self._advance()
                rights.append((MultOps.DIV, self._parse_call_exp()))
            else:
                break
        return MultExp(call_exp_left=left, call_exp_right=rights)

    def _parse_call_exp(self) -> CallExp:
        dot = self._parse_dot_exp()
        calls: List[List[Exp]] = []
        while self._check(TokenKind.LPAREN):
            self._advance()
            args = self._parse_comma_exp()
            self._expect(TokenKind.RPAREN)
            calls.append(args)
        return CallExp(dot_exp=dot, comma_exp=calls)

    def _parse_dot_exp(self) -> DotExp:
        primary = self._parse_primary_exp()
        vars_: List[str] = []
        while self._match(TokenKind.DOT):
            vars_.append(self._expect(TokenKind.IDENTIFIER).value)
        return DotExp(primary_exp=primary, var=vars_)

    def _parse_primary_exp(self) -> PrimaryExp:
        tok = self._peek()

        if tok.kind == TokenKind.INTEGER:
            self._advance()
            return IntExp(i=int(tok.value))

        if tok.kind == TokenKind.TRUE:
            self._advance()
            return BooleanExp(value=True)

        if tok.kind == TokenKind.FALSE:
            self._advance()
            return BooleanExp(value=False)

        if tok.kind == TokenKind.SELF:
            self._advance()
            return SelfExp()

        if tok.kind == TokenKind.LPAREN:
            self._advance()
            exp = self._parse_exp()
            self._expect(TokenKind.RPAREN)
            return ParenExp(exp=exp)

        if tok.kind == TokenKind.NEW:
            self._advance()
            name = self._expect(TokenKind.IDENTIFIER).value
            self._expect(TokenKind.LBRACE)
            params = self._parse_struct_actual_params()
            self._expect(TokenKind.RBRACE)
            return NewExp(structname=name, struct_actual_params=params)

        if tok.kind == TokenKind.IDENTIFIER:
            self._advance()
            return VarExp(var=tok.value)

        raise ParseError(
            f"Expected expression but got {tok.kind.name} ({tok.value!r})",
            tok.line, tok.col,
        )

    def _parse_comma_exp(self) -> List[Exp]:
        exps: List[Exp] = []
        if self._check(TokenKind.RPAREN):
            return exps
        exps.append(self._parse_exp())
        while self._match(TokenKind.COMMA):
            exps.append(self._parse_exp())
        return exps

    def _parse_struct_actual_params(self) -> List[StructActualParam]:
        params: List[StructActualParam] = []
        if self._check(TokenKind.RBRACE):
            return params
        params.append(self._parse_struct_actual_param())
        while self._match(TokenKind.COMMA):
            params.append(self._parse_struct_actual_param())
        return params

    def _parse_struct_actual_param(self) -> StructActualParam:
        name = self._expect(TokenKind.IDENTIFIER).value
        self._expect(TokenKind.COLON)
        exp = self._parse_exp()
        return StructActualParam(var=name, exp=exp)

# Helpers
def parse_source(source: str) -> Program:
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def _parse_and_print(source: str) -> None:
    try:
        program = parse_source(source)
        print(program)
    except Exception as e:
        print(f"ParseError: {e}")

# Entry point  e.g. python parser.py "name of the test file")
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
    except OSError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    _parse_and_print(source)