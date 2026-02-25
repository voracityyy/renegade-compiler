import pytest
from lexer import Lexer, TokenKind, LexError


class TestLiterals:

    def test_integer(self):
        # Test for LexError
        tokens = Lexer("5").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.INTEGER
        assert tokens[0].value == "5"

    def test_identifier(self):
        # Test for LexError
        tokens = Lexer("x").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.IDENTIFIER
        assert tokens[0].value == "x"


class TestKeywords:

    def test_struct(self):
        # Test for LexError
        tokens = Lexer("struct").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.STRUCT
        assert tokens[0].value == "struct"

    def test_trait(self):
        # Test for LexError
        tokens = Lexer("trait").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.TRAIT
        assert tokens[0].value == "trait"

    def test_impl(self):
        # Test for LexError
        tokens = Lexer("impl").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.IMPL
        assert tokens[0].value == "impl"

    def test_for(self):
        # Test for LexError
        tokens = Lexer("for").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.FOR
        assert tokens[0].value == "for"

    def test_func(self):
        # Test for LexError
        tokens = Lexer("func").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.FUNC
        assert tokens[0].value == "func"

    def test_method(self):
        # Test for LexError
        tokens = Lexer("method").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.METHOD
        assert tokens[0].value == "method"

    def test_let(self):
        # Test for LexError
        tokens = Lexer("let").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.LET
        assert tokens[0].value == "let"

    def test_if(self):
        # Test for LexError
        tokens = Lexer("if").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.IF
        assert tokens[0].value == "if"

    def test_else(self):
        # Test for LexError
        tokens = Lexer("else").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.ELSE
        assert tokens[0].value == "else"

    def test_while(self):
        # Test for LexError
        tokens = Lexer("while").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.WHILE
        assert tokens[0].value == "while"

    def test_break(self):
        # Test for LexError
        tokens = Lexer("break").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.BREAK
        assert tokens[0].value == "break"

    def test_return(self):
        # Test for LexError
        tokens = Lexer("return").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.RETURN
        assert tokens[0].value == "return"

    def test_println(self):
        # Test for LexError
        tokens = Lexer("println").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.PRINTLN
        assert tokens[0].value == "println"

    def test_new(self):
        # Test for LexError
        tokens = Lexer("new").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.NEW
        assert tokens[0].value == "new"

    def test_true(self):
        # Test for LexError
        tokens = Lexer("true").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.TRUE
        assert tokens[0].value == "true"

    def test_false(self):
        # Test for LexError
        tokens = Lexer("false").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.FALSE
        assert tokens[0].value == "false"

    def test_self(self):
        # Test for LexError
        tokens = Lexer("self").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.SELF
        assert tokens[0].value == "self"


class TestBuiltInTypes:

    def test_int(self):
        # Test for LexError
        tokens = Lexer("Int").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.INT_TYPE
        assert tokens[0].value == "Int"

    def test_void(self):
        # Test for LexError
        tokens = Lexer("Void").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.VOID_TYPE
        assert tokens[0].value == "Void"

    def test_boolean(self):
        # Test for LexError
        tokens = Lexer("Boolean").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.BOOLEAN_TYPE
        assert tokens[0].value == "Boolean"

    def test_self(self):
        # Test for LexError
        tokens = Lexer("Self").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.SELF_TYPE
        assert tokens[0].value == "Self"


class TestArithmeticOperators:

    def test_plus(self):
        # Test for LexError
        tokens = Lexer("+").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.PLUS
        assert tokens[0].value == "+"

    def test_minus(self):
        # Test for LexError
        tokens = Lexer("-").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.MINUS
        assert tokens[0].value == "-"

    def test_star(self):
        # Test for LexError
        tokens = Lexer("*").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.STAR
        assert tokens[0].value == "*"

    def test_slash(self):
        # Test for LexError
        tokens = Lexer("/").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.SLASH
        assert tokens[0].value == "/"


class TestComparisonOperators:

    def test_less_than(self):
        # Test for LexError
        tokens = Lexer("<").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.LESS_THAN
        assert tokens[0].value == "<"

    def test_equals_equals(self):
        # Test for LexError
        tokens = Lexer("==").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.EQUALS_EQUALS
        assert tokens[0].value == "=="

    def test_not_equals(self):
        # Test for LexError
        tokens = Lexer("!=").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.NOT_EQUALS
        assert tokens[0].value == "!="


class TestAssignment:

    def test_equals(self):
        # Test for LexError
        tokens = Lexer("=").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.EQUALS
        assert tokens[0].value == "="

    def test_fat_arrow(self):
        # Test for LexError
        tokens = Lexer("=>").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.FAT_ARROW
        assert tokens[0].value == "=>"


class TestDelimiters:

    def test_lparen(self):
        # Test for LexError
        tokens = Lexer("(").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.LPAREN
        assert tokens[0].value == "("

    def test_rparent(self):
        # Test for LexError
        tokens = Lexer(")").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.RPAREN
        assert tokens[0].value == ")"

    def test_lbrace(self):
        # Test for LexError
        tokens = Lexer("{").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.LBRACE
        assert tokens[0].value == "{"

    def test_rbrace(self):
        # Test for LexError
        tokens = Lexer("}").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.RBRACE
        assert tokens[0].value == "}"

    def test_comma(self):
        # Test for LexError
        tokens = Lexer(",").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.COMMA
        assert tokens[0].value == ","

    def test_colon(self):
        # Test for LexError
        tokens = Lexer(":").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.COLON
        assert tokens[0].value == ":"

    def test_semicolon(self):
        # Test for LexError
        tokens = Lexer(";").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.SEMICOLON
        assert tokens[0].value == ";"

    def test_dot(self):
        # Test for LexError
        tokens = Lexer(".").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.DOT
        assert tokens[0].value == "."

    def test_eof(self):
        # Test for LexError
        tokens = Lexer("").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.EOF
        assert tokens[0].value == ""


class TestEdgeCases:

    def test_whitespace(self):
            # Test for LexError
            Lexer("    ").tokenize()
            # No need to test AssertionError for whitespace
    
    def test_comments(self):
            # Test for LexError
            Lexer("//").tokenize()
            # No need to test AssertionError for comments

    def test_lexerror(self):
            # Test for LexError
            with pytest.raises(LexError):
                Lexer("$").tokenize()

    def test_assertionerror(self):
        # Test for LexError
        tokens = Lexer("5").tokenize()
        # Test for AssertionError
        assert tokens[0].kind == TokenKind.INTEGER
        with pytest.raises(AssertionError):
            assert tokens[0].value == "7"