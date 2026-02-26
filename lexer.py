from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import List

# Token kinds
class TokenKind(Enum):
    # Literals
    INTEGER    = auto()   # ex. 42
    IDENTIFIER = auto()   # ex. myVar, MyStruct, MyTrait

    # Keywords
    STRUCT  = auto()   # struct
    TRAIT   = auto()   # trait
    IMPL    = auto()   # impl
    FOR     = auto()   # for
    FUNC    = auto()   # func
    METHOD  = auto()   # method
    LET     = auto()   # let
    IF      = auto()   # if
    ELSE    = auto()   # else
    WHILE   = auto()   # while
    BREAK   = auto()   # break
    RETURN  = auto()   # return
    PRINTLN = auto()   # println
    NEW     = auto()   # new
    TRUE    = auto()   # true
    FALSE   = auto()   # false
    SELF    = auto()   # self

    # Built-in type keywords
    INT_TYPE     = auto()  # Int
    VOID_TYPE    = auto()  # Void
    BOOLEAN_TYPE = auto()  # Boolean
    SELF_TYPE    = auto()  # Self

    # Arithmetic operators
    PLUS   = auto()  # +
    MINUS  = auto()  # -
    STAR   = auto()  # *
    SLASH  = auto()  # /

    # Comparison operators
    LESS_THAN    = auto()  # <
    EQUALS_EQUALS = auto() # ==
    NOT_EQUALS   = auto()  # !=

    # Assignment / arrow
    EQUALS    = auto()  # =
    FAT_ARROW = auto()  # =>

    # Punctuation / delimiters
    LPAREN    = auto()  # (
    RPAREN    = auto()  # )
    LBRACE    = auto()  # {
    RBRACE    = auto()  # }
    COMMA     = auto()  # ,
    COLON     = auto()  # :
    SEMICOLON = auto()  # ;
    DOT       = auto()  # .

    # Special
    EOF = auto()

# Token dataclass
@dataclass
class Token:
    kind: TokenKind
    value: str        # raw text from source
    line: int         # 1-based line number
    col: int          # 1-based column number

    def __repr__(self) -> str:
        return f"Token({self.kind.name}, {self.value!r}, line={self.line}, col={self.col})"

# Keyword / type-keyword tables
KEYWORDS: dict[str, TokenKind] = {
    "struct":   TokenKind.STRUCT,
    "trait":    TokenKind.TRAIT,
    "impl":     TokenKind.IMPL,
    "for":      TokenKind.FOR,
    "func":     TokenKind.FUNC,
    "method":   TokenKind.METHOD,
    "let":      TokenKind.LET,
    "if":       TokenKind.IF,
    "else":     TokenKind.ELSE,
    "while":    TokenKind.WHILE,
    "break":    TokenKind.BREAK,
    "return":   TokenKind.RETURN,
    "println":  TokenKind.PRINTLN,
    "new":      TokenKind.NEW,
    "true":     TokenKind.TRUE,
    "false":    TokenKind.FALSE,
    "self":     TokenKind.SELF,
    
    # Built-in types (capitalised identifiers reserved by the language)
    "Int":      TokenKind.INT_TYPE,
    "Void":     TokenKind.VOID_TYPE,
    "Boolean":  TokenKind.BOOLEAN_TYPE,
    "Self":     TokenKind.SELF_TYPE,
}

# LexError
class LexError(Exception):
    def __init__(self, message: str, line: int, col: int) -> None:
        super().__init__(f"[line {line}, col {col}] {message}")
        self.line = line
        self.col = col

# Lexer
class Lexer:
    def __init__(self, source: str) -> None:
        self._source = source
        self._pos = 0          # current character index
        self._line = 1
        self._col = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while True:
            tok = self._next_token()
            tokens.append(tok)
            if tok.kind == TokenKind.EOF:
                break
        return tokens

    # Internal helpers
    def _peek(self, offset: int = 0) -> str:
        idx = self._pos + offset
        return self._source[idx] if idx < len(self._source) else ""

    def _advance(self) -> str:
        ch = self._source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 1
        else:
            self._col += 1
        return ch

    def _skip_whitespace_and_comments(self) -> None:
        while self._pos < len(self._source):
            ch = self._peek()
            if ch in (" ", "\t", "\r", "\n"):
                self._advance()
            # Single-line comment: //
            elif ch == "/" and self._peek(1) == "/":
                while self._pos < len(self._source) and self._peek() != "\n":
                    self._advance()
            else:
                break

    def _next_token(self) -> Token:
        self._skip_whitespace_and_comments()

        if self._pos >= len(self._source):
            return Token(TokenKind.EOF, "", self._line, self._col)

        start_line = self._line
        start_col = self._col
        ch = self._peek()

        # Integer literal
        if ch.isdigit():
            return self._read_integer(start_line, start_col)

        # Identifier or keyword
        if ch.isalpha() or ch == "_":
            return self._read_identifier_or_keyword(start_line, start_col)

        # Two-character tokens that start with '='
        if ch == "=":
            self._advance()
            if self._peek() == ">":
                self._advance()
                return Token(TokenKind.FAT_ARROW, "=>", start_line, start_col)
            if self._peek() == "=":
                self._advance()
                return Token(TokenKind.EQUALS_EQUALS, "==", start_line, start_col)
            return Token(TokenKind.EQUALS, "=", start_line, start_col)

        # !=
        if ch == "!":
            self._advance()
            if self._peek() == "=":
                self._advance()
                return Token(TokenKind.NOT_EQUALS, "!=", start_line, start_col)
            raise LexError(f"Unexpected character '!'", start_line, start_col)

        # Single-character tokens
        SINGLE: dict[str, TokenKind] = {
            "+": TokenKind.PLUS,
            "-": TokenKind.MINUS,
            "*": TokenKind.STAR,
            "/": TokenKind.SLASH,
            "<": TokenKind.LESS_THAN,
            "(": TokenKind.LPAREN,
            ")": TokenKind.RPAREN,
            "{": TokenKind.LBRACE,
            "}": TokenKind.RBRACE,
            ",": TokenKind.COMMA,
            ":": TokenKind.COLON,
            ";": TokenKind.SEMICOLON,
            ".": TokenKind.DOT,
        }
        if ch in SINGLE:
            self._advance()
            return Token(SINGLE[ch], ch, start_line, start_col)

        raise LexError(f"Unexpected character {ch!r}", start_line, start_col)

    def _read_integer(self, line: int, col: int) -> Token:
        start = self._pos
        while self._peek().isdigit():
            self._advance()
        value = self._source[start:self._pos]
        return Token(TokenKind.INTEGER, value, line, col)

    def _read_identifier_or_keyword(self, line: int, col: int) -> Token:
        start = self._pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        value = self._source[start:self._pos]
        kind = KEYWORDS.get(value, TokenKind.IDENTIFIER)
        return Token(kind, value, line, col)

# Helpers
def _lex_and_print(source: str) -> None:
    try:
        for tok in Lexer(source).tokenize():
            print(tok)
    except LexError as e:
        print(f"LexError: {e}")


# Entry point  (python lexer.py <file>)
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python lexer.py <source_file>")
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
    except OSError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    _lex_and_print(source)
