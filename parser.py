# ============================================================
# PARSER - Analisador Sintático (Descendente Recursivo)
# Linguagem: MTG-Lang → C#
# ============================================================

from lexer import Token, tokenize


class ParseError(Exception):
    pass


# ---------- Nós da Árvore de Derivação ----------
class Node:
    def __init__(self, name, children=None, value=None):
        self.name     = name
        self.children = children or []
        self.value    = value        # para folhas (tokens)

    def __repr__(self, level=0):
        indent = '  ' * level
        if self.value is not None:
            return f"{indent}{self.name}({self.value!r})"
        lines = [f"{indent}{self.name}"]
        for c in self.children:
            lines.append(c.__repr__(level + 1))
        return '\n'.join(lines)


# ---------- Parser ----------
class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos    = 0

    # ------ helpers ------
    def current(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek_type(self) -> str | None:
        tok = self.current()
        return tok.type if tok else None

    def consume(self, expected_type: str) -> Token:
        tok = self.current()
        if tok is None:
            raise ParseError(
                f'[ERRO SINTÁTICO] Esperado {expected_type!r} mas chegou ao fim do arquivo'
            )
        if tok.type != expected_type:
            raise ParseError(
                f'[ERRO SINTÁTICO] Esperado {expected_type!r} mas encontrou '
                f'{tok.type!r} ({tok.value!r}) na linha {tok.line}'
            )
        self.pos += 1
        return tok

    def match(self, *types) -> bool:
        return self.peek_type() in types

    # ------ regras ------

    def parse_prog(self) -> Node:
        self.consume('UPKEEP')
        bloco = self.parse_bloco()
        self.consume('ENDSTEP')
        return Node('prog', [bloco])

    # bloco -> item bloco | item
    def parse_bloco(self) -> Node:
        items = []
        while self.peek_type() not in ('ENDSTEP', 'DCURLY', None):
            items.append(self.parse_item())
        return Node('bloco', items)

    # item -> cmd | COMMENT
    def parse_item(self) -> Node:
        if self.match('FLAVOUR_TEXT'):
            return self.parse_comment()
        return self.parse_cmd()

    # COMMENT -> FlavourText TEXTO endLine
    def parse_comment(self) -> Node:
        self.consume('FLAVOUR_TEXT')
        tok = self.consume('TEXT')
        self.consume('END_LINE')
        return Node('COMMENT', [Node('TEXT', value=tok.value)])

    # cmd -> cmdSimp endLine | cmdEstr
    def parse_cmd(self) -> Node:
        if self.match('TRIGGER', 'WHENEVER', 'UNTIL_NEXT'):
            return Node('cmd', [self.parse_cmd_estr()])
        node = self.parse_cmd_simp()
        self.consume('END_LINE')
        return Node('cmd', [node])

    # cmdSimp -> cmdInput | cmdPrint | cmdExpr | declara | declaraValor
    def parse_cmd_simp(self) -> Node:
        t = self.peek_type()
        if t == 'SCRY':
            return self.parse_cmd_input()
        elif t == 'REVEAL':
            return self.parse_cmd_print()
        elif t in ('LAND', 'ARTIFACT', 'CREATURE_STATE', 'LEGENDARY'):
            return self.parse_declara()
        elif t == 'ID':
            return self.parse_cmd_expr()
        else:
            tok = self.current()
            raise ParseError(
                f'[ERRO SINTÁTICO] Comando inválido {tok.value!r} na linha {tok.line}'
            )

    # cmdEstr -> cmdSe | cmdEnquanto | cmdFor
    def parse_cmd_estr(self) -> Node:
        t = self.peek_type()
        if t == 'TRIGGER':
            return self.parse_cmd_se()
        elif t == 'WHENEVER':
            return self.parse_cmd_enquanto()
        elif t == 'UNTIL_NEXT':
            return self.parse_cmd_for()

    # cmdInput -> scry ( ID )
    def parse_cmd_input(self) -> Node:
        self.consume('SCRY')
        self.consume('EPAREN')
        tok = self.consume('ID')
        self.consume('DPAREN')
        return Node('cmdInput', [Node('ID', value=tok.value)])

    # cmdPrint -> reveal ( CONTEUDO )
    def parse_cmd_print(self) -> Node:
        self.consume('REVEAL')
        self.consume('EPAREN')
        conteudo = self.parse_conteudo()
        self.consume('DPAREN')
        return Node('cmdPrint', [conteudo])

    # CONTEUDO -> FATOR | TEXTO
    def parse_conteudo(self) -> Node:
        if self.match('TEXT'):
            tok = self.consume('TEXT')
            return Node('CONTEUDO', [Node('TEXT', value=tok.value)])
        return Node('CONTEUDO', [self.parse_fator()])

    # declara -> tipo ID  |  declaraValor -> tipo ID cost EXPRESSAO
    def parse_declara(self) -> Node:
        tipo = self.parse_tipo()
        tok  = self.consume('ID')
        id_node = Node('ID', value=tok.value)
        if self.match('COST'):
            self.consume('COST')
            expr = self.parse_expressao()
            return Node('declaraValor', [tipo, id_node, expr])
        return Node('declara', [tipo, id_node])

    # tipo -> (land | artifact | creatureState | legendary)+
    def parse_tipo(self) -> Node:
        tipos = []
        while self.match('LAND', 'ARTIFACT', 'CREATURE_STATE', 'LEGENDARY'):
            tok = self.current()
            self.pos += 1
            tipos.append(Node(tok.type, value=tok.value))
        if not tipos:
            tok = self.current()
            raise ParseError(
                f'[ERRO SINTÁTICO] Esperado tipo de variável na linha {tok.line}'
            )
        return Node('tipo', tipos)

    # cmdExpr -> ID cost EXPRESSAO | ID proliferate | ID blight
    def parse_cmd_expr(self) -> Node:
        tok = self.consume('ID')
        id_node = Node('ID', value=tok.value)
        if self.match('COST'):
            self.consume('COST')
            expr = self.parse_expressao()
            return Node('cmdExpr', [id_node, Node('COST'), expr])
        elif self.match('PROLIFERATE'):
            self.consume('PROLIFERATE')
            return Node('cmdExpr', [id_node, Node('PROLIFERATE')])
        elif self.match('BLIGHT'):
            self.consume('BLIGHT')
            return Node('cmdExpr', [id_node, Node('BLIGHT')])
        else:
            tok2 = self.current()
            raise ParseError(
                f'[ERRO SINTÁTICO] Esperado cost/proliferate/blight após ID na linha {tok2.line if tok2 else "?"}'
            )

    # cmdSe -> trigger ( comparacao ) { bloco } cmdS
    def parse_cmd_se(self) -> Node:
        self.consume('TRIGGER')
        self.consume('EPAREN')
        comp = self.parse_comparacao()
        self.consume('DPAREN')
        self.consume('ECURLY')
        bloco = self.parse_bloco()
        self.consume('DCURLY')
        cmds = self.parse_cmds()
        return Node('cmdSe', [comp, bloco, cmds])

    # cmdS -> inResponse ( comparacao ) { bloco } cmdS | silence { bloco } | VAZIO
    def parse_cmds(self) -> Node:
        if self.match('IN_RESPONSE'):
            self.consume('IN_RESPONSE')
            self.consume('EPAREN')
            comp = self.parse_comparacao()
            self.consume('DPAREN')
            self.consume('ECURLY')
            bloco = self.parse_bloco()
            self.consume('DCURLY')
            rest = self.parse_cmds()
            return Node('cmdS_elif', [comp, bloco, rest])
        elif self.match('SILENCE'):
            self.consume('SILENCE')
            self.consume('ECURLY')
            bloco = self.parse_bloco()
            self.consume('DCURLY')
            return Node('cmdS_else', [bloco])
        return Node('VAZIO')

    # cmdEnquanto -> whenever ( comparacao ) { bloco }
    def parse_cmd_enquanto(self) -> Node:
        self.consume('WHENEVER')
        self.consume('EPAREN')
        comp = self.parse_comparacao()
        self.consume('DPAREN')
        self.consume('ECURLY')
        bloco = self.parse_bloco()
        self.consume('DCURLY')
        return Node('cmdEnquanto', [comp, bloco])

    # cmdFor -> untilNext ( declaraValor !!! comparacao !!! cmdExpr ) { bloco }
    def parse_cmd_for(self) -> Node:
        self.consume('UNTIL_NEXT')
        self.consume('EPAREN')
        decl = self.parse_declara()
        self.consume('END_LINE')
        comp = self.parse_comparacao()
        self.consume('END_LINE')
        expr = self.parse_cmd_expr()
        self.consume('DPAREN')
        self.consume('ECURLY')
        bloco = self.parse_bloco()
        self.consume('DCURLY')
        return Node('cmdFor', [decl, comp, expr, bloco])

    # comparacao -> comp (cpJunc comparacao)?
    def parse_comparacao(self) -> Node:
        comp = self.parse_comp()
        if self.match('CASCADE', 'MAY', 'FLIP'):
            tok = self.current()
            self.pos += 1
            rest = self.parse_comparacao()
            return Node('comparacao', [comp, Node(tok.type, value=tok.value), rest])
        return Node('comparacao', [comp])

    # comp -> EXPRESSAO cpRel EXPRESSAO | ID | BOOL
    def parse_comp(self) -> Node:
        # tenta EXPRESSAO cpRel EXPRESSAO
        saved = self.pos
        try:
            expr1 = self.parse_expressao()
            if self.match('CLASH_LESS_EQUALS', 'CLASH_MORE_EQUALS',
                          'CLASH_LESS', 'CLASH_MORE', 'CLASH'):
                tok = self.current()
                self.pos += 1
                expr2 = self.parse_expressao()
                return Node('comp', [expr1, Node(tok.type, value=tok.value), expr2])
            # sem operador relacional: pode ser ID ou BOOL sozinho
            return Node('comp', [expr1])
        except ParseError:
            self.pos = saved
            raise

    # EXPRESSAO -> FATOR EXPR
    def parse_expressao(self) -> Node:
        fator = self.parse_fator()
        expr  = self.parse_expr()
        return Node('EXPRESSAO', [fator, expr])

    # EXPR -> cpArit FATOR EXPR | VAZIO
    def parse_expr(self) -> Node:
        if self.match('DRAW', 'DISCARD', 'KRENKSTORM', 'WIPE'):
            tok = self.current()
            self.pos += 1
            fator = self.parse_fator()
            rest  = self.parse_expr()
            return Node('EXPR', [Node(tok.type, value=tok.value), fator, rest])
        return Node('VAZIO')

    # FATOR -> NUM | ID | ( EXPRESSAO ) | BOOL
    def parse_fator(self) -> Node:
        t = self.peek_type()
        if t == 'NUM':
            tok = self.consume('NUM')
            return Node('FATOR', [Node('NUM', value=tok.value)])
        elif t == 'ID':
            tok = self.consume('ID')
            return Node('FATOR', [Node('ID', value=tok.value)])
        elif t in ('ALIVE', 'DEAD'):
            tok = self.current()
            self.pos += 1
            return Node('FATOR', [Node('BOOL', value=tok.value)])
        elif t == 'EPAREN':
            self.consume('EPAREN')
            expr = self.parse_expressao()
            self.consume('DPAREN')
            return Node('FATOR', [Node('EPAREN'), expr, Node('DPAREN')])
        else:
            tok = self.current()
            info = f'{tok.value!r} na linha {tok.line}' if tok else 'fim do arquivo'
            raise ParseError(f'[ERRO SINTÁTICO] Fator inválido: {info}')


def parse(tokens: list[Token]) -> Node:
    p = Parser(tokens)
    tree = p.parse_prog()
    if p.pos < len(tokens):
        tok = p.current()
        raise ParseError(
            f'[ERRO SINTÁTICO] Token inesperado {tok.value!r} na linha {tok.line}'
        )
    return tree
