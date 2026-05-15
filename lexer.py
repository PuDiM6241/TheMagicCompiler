# ============================================================
# LEXER - Analisador Léxico
# Linguagem: MTG-Lang → C#
# ============================================================

import re

# ---------- Definição de Tokens ----------
TOKEN_TYPES = [
    # Palavras reservadas (ordem importa: mais longas primeiro)
    ('UPKEEP',           r'\bupkeep\b'),
    ('ENDSTEP',          r'\bendStep\b'),
    ('LAND',             r'\bland\b'),
    ('ARTIFACT',         r'\bartifact\b'),
    ('CREATURE_STATE',   r'\bcreatureState\b'),
    ('LEGENDARY',        r'\blegendary\b'),
    ('SCRY',             r'\bscry\b'),
    ('REVEAL',           r'\breveal\b'),
    ('TRIGGER',          r'\btrigger\b'),
    ('IN_RESPONSE',      r'\binResponse\b'),
    ('SILENCE',          r'\bsilence\b'),
    ('WHENEVER',         r'\bwhenever\b'),
    ('UNTIL_NEXT',       r'\buntilNext\b'),
    ('COST',             r'\bcost\b'),
    ('CLASH_LESS_EQUALS',r'\bclashLessEquals\b'),
    ('CLASH_MORE_EQUALS',r'\bclashMoreEquals\b'),
    ('CLASH_LESS',       r'\bclashLess\b'),
    ('CLASH_MORE',       r'\bclashMore\b'),
    ('CLASH',            r'\bclash\b'),
    ('CASCADE',          r'\bcascade\b'),
    ('MAY',              r'\bmay\b'),
    ('FLIP',             r'\bflip\b'),
    ('DRAW',             r'\bdraw\b'),
    ('DISCARD',          r'\bdiscard\b'),
    ('KRENKSTORM',       r'\bkrenkStorm\b'),
    ('WIPE',             r'\bwipe\b'),
    ('PROLIFERATE',      r'\bproliferate\b'),
    ('BLIGHT',           r'\bblight\b'),
    ('ALIVE',            r'\balive\b'),
    ('DEAD',             r'\bdead\b'),
    ('FLAVOUR_TEXT',     r'\bFlavour Text:'),
    # Símbolos
    ('END_LINE',         r'!!!'),
    ('EPAREN',           r'\('),
    ('DPAREN',           r'\)'),
    ('ECURLY',           r'\{'),
    ('DCURLY',           r'\}'),
    # Literais
    ('TEXT',             r'"[^"]*"'),
    ('NUM',              r'\d+\.\d+|\d+'),
    ('ID',               r'[a-zA-Z_][a-zA-Z0-9_]*'),
    # Ignorados
    ('NEWLINE',          r'\n'),
    ('SKIP',             r'[ \t\r]+'),
    ('MISMATCH',         r'.'),
]

TOKEN_RE = re.compile(
    '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_TYPES)
)

class Token:
    def __init__(self, type_, value, line):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, linha={self.line})'


class LexerError(Exception):
    pass


def tokenize(source_code: str) -> list[Token]:
    tokens = []
    line   = 1

    for mo in TOKEN_RE.finditer(source_code):
        kind  = mo.lastgroup
        value = mo.group()

        if kind == 'NEWLINE':
            line += 1
            continue
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise LexerError(
                f'[ERRO LÉXICO] Caractere inesperado {value!r} na linha {line}'
            )
        else:
            tokens.append(Token(kind, value, line))

    return tokens


def print_tokens(tokens: list[Token]):
    print(f"\n{'─'*50}")
    print(f"{'TIPO':<25} {'VALOR':<20} {'LINHA'}")
    print(f"{'─'*50}")
    for tok in tokens:
        print(f"{tok.type:<25} {tok.value:<20} {tok.line}")
    print(f"{'─'*50}\n")
