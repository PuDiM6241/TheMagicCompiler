# ============================================================
# TRANSLATOR - Geração de Código C#
# Linguagem: MTG-Lang → C#
# ============================================================

from parser import Node

# Mapeamento de tipos da linguagem para C#
# legendary + tipo = versão "long" do tipo
TYPE_MAP = {
    ('LAND',):                  'int',
    ('ARTIFACT',):              'float',
    ('CREATURE_STATE',):        'bool',
    ('LEGENDARY',):             'long',
    ('LEGENDARY', 'LAND'):      'long',
    ('LEGENDARY', 'ARTIFACT'):  'double',
    ('LEGENDARY', 'CREATURE_STATE'): 'long',   # não existe bool longa, usa long
}

# Operadores aritméticos
ARIT_MAP = {
    'DRAW':       '+',
    'DISCARD':    '-',
    'KRENKSTORM': '*',
    'WIPE':       '/',
}

# Operadores relacionais
REL_MAP = {
    'CLASH':             '==',
    'CLASH_MORE':        '>',
    'CLASH_LESS':        '<',
    'CLASH_MORE_EQUALS': '>=',
    'CLASH_LESS_EQUALS': '<=',
}

# Operadores lógicos
JUNC_MAP = {
    'CASCADE': '&&',
    'MAY':     '||',
    'FLIP':    '!',
}

# Mapa para leitura por tipo C#
READ_MAP = {
    'int':    'int.Parse(Console.ReadLine())',
    'float':  'float.Parse(Console.ReadLine())',
    'double': 'double.Parse(Console.ReadLine())',
    'long':   'long.Parse(Console.ReadLine())',
    'bool':   'bool.Parse(Console.ReadLine())',
}


class TranslatorError(Exception):
    pass


class Translator:
    def __init__(self):
        self.indent   = 0
        self.var_types: dict[str, str] = {}   # nome → tipo C#

    def ind(self) -> str:
        return '    ' * self.indent

    def translate(self, tree: Node) -> str:
        lines = [
            'using System;',
            '',
            'class Program {',
            '    static void Main() {',
        ]
        self.indent = 2
        self.var_types = {}
        body = self.t_bloco(tree.children[0])
        lines.append(body)
        lines.append('    }')
        lines.append('}')
        return '\n'.join(lines)

    # ---- bloco ----
    def t_bloco(self, node: Node) -> str:
        parts = []
        for child in node.children:
            parts.append(self.t_item(child))
        return '\n'.join(p for p in parts if p)

    def t_item(self, node: Node) -> str:
        if node.name == 'COMMENT':
            text = node.children[0].value
            return f'{self.ind()}// {text}'
        return self.t_cmd(node)

    # ---- cmd ----
    def t_cmd(self, node: Node) -> str:
        child = node.children[0]
        name  = child.name

        if name == 'cmdInput':
            return self.t_input(child)
        elif name == 'cmdPrint':
            return self.t_print(child)
        elif name == 'declara':
            return self.t_declara(child)
        elif name == 'declaraValor':
            return self.t_declara_valor(child)
        elif name == 'cmdExpr':
            return self.t_cmd_expr(child)
        elif name == 'cmdSe':
            return self.t_cmd_se(child)
        elif name == 'cmdEnquanto':
            return self.t_cmd_enquanto(child)
        elif name == 'cmdFor':
            return self.t_cmd_for(child)
        else:
            raise TranslatorError(f'[ERRO TRADUÇÃO] Nó desconhecido: {name}')

    # ---- scry ( ID ) ----
    def t_input(self, node: Node) -> str:
        var_name = node.children[0].value
        cs_type  = self.var_types.get(var_name, 'int')
        reader   = READ_MAP.get(cs_type, 'Console.ReadLine()')
        return f'{self.ind()}{var_name} = {reader};'

    # ---- reveal ( CONTEUDO ) ----
    def t_print(self, node: Node) -> str:
        conteudo = node.children[0]
        child    = conteudo.children[0]
        if child.name == 'TEXT':
            return f'{self.ind()}Console.WriteLine({child.value});'
        else:
            val = self.t_fator(child)
            return f'{self.ind()}Console.WriteLine({val});'

    # ---- declara ----
    def t_declara(self, node: Node) -> str:
        cs_type  = self.resolve_tipo(node.children[0])
        var_name = node.children[1].value
        self.var_types[var_name] = cs_type
        return f'{self.ind()}{cs_type} {var_name};'

    # ---- declaraValor ----
    def t_declara_valor(self, node: Node) -> str:
        cs_type  = self.resolve_tipo(node.children[0])
        var_name = node.children[1].value
        expr     = self.t_expressao(node.children[2])
        self.var_types[var_name] = cs_type
        return f'{self.ind()}{cs_type} {var_name} = {expr};'

    # ---- cmdExpr ----
    def t_cmd_expr(self, node: Node) -> str:
        id_node = node.children[0]
        op_node = node.children[1]
        var     = id_node.value

        if op_node.name == 'PROLIFERATE':
            return f'{self.ind()}{var}++;'
        elif op_node.name == 'BLIGHT':
            return f'{self.ind()}{var}--;'
        else:
            expr = self.t_expressao(node.children[2])
            return f'{self.ind()}{var} = {expr};'

    # ---- cmdSe ----
    def t_cmd_se(self, node: Node) -> str:
        comp  = self.t_comparacao(node.children[0])
        bloco = self.t_bloco_indented(node.children[1])
        cmds  = self.t_cmds(node.children[2])
        result = f'{self.ind()}if ({comp}) {{\n{bloco}\n{self.ind()}}}'
        if cmds:
            result += cmds
        return result

    def t_cmds(self, node: Node) -> str:
        if node.name == 'VAZIO':
            return ''
        elif node.name == 'cmdS_elif':
            comp  = self.t_comparacao(node.children[0])
            bloco = self.t_bloco_indented(node.children[1])
            rest  = self.t_cmds(node.children[2])
            result = f' else if ({comp}) {{\n{bloco}\n{self.ind()}}}'
            if rest:
                result += rest
            return result
        elif node.name == 'cmdS_else':
            bloco = self.t_bloco_indented(node.children[0])
            return f' else {{\n{bloco}\n{self.ind()}}}'
        return ''

    # ---- cmdEnquanto ----
    def t_cmd_enquanto(self, node: Node) -> str:
        comp  = self.t_comparacao(node.children[0])
        bloco = self.t_bloco_indented(node.children[1])
        return f'{self.ind()}while ({comp}) {{\n{bloco}\n{self.ind()}}}'

    # ---- cmdFor ----
    def t_cmd_for(self, node: Node) -> str:
        decl  = node.children[0]
        comp  = self.t_comparacao(node.children[1])
        expr  = node.children[2]
        bloco = node.children[3]

        # init
        if decl.name == 'declaraValor':
            cs_type  = self.resolve_tipo(decl.children[0])
            var_name = decl.children[1].value
            val      = self.t_expressao(decl.children[2])
            self.var_types[var_name] = cs_type
            init = f'{cs_type} {var_name} = {val}'
        else:
            cs_type  = self.resolve_tipo(decl.children[0])
            var_name = decl.children[1].value
            self.var_types[var_name] = cs_type
            init = f'{cs_type} {var_name}'

        # incremento
        inc  = self.t_cmd_expr_inline(expr)
        body = self.t_bloco_indented(bloco)
        return f'{self.ind()}for ({init}; {comp}; {inc}) {{\n{body}\n{self.ind()}}}'

    def t_cmd_expr_inline(self, node: Node) -> str:
        """cmdExpr sem ponto-e-vírgula, para usar no for."""
        id_node = node.children[0]
        op_node = node.children[1]
        var     = id_node.value
        if op_node.name == 'PROLIFERATE':
            return f'{var}++'
        elif op_node.name == 'BLIGHT':
            return f'{var}--'
        else:
            expr = self.t_expressao(node.children[2])
            return f'{var} = {expr}'

    # ---- comparacao ----
    def t_comparacao(self, node: Node) -> str:
        if len(node.children) == 1:
            return self.t_comp(node.children[0])
        comp  = self.t_comp(node.children[0])
        junc  = node.children[1]
        rest  = self.t_comparacao(node.children[2])
        if junc.name == 'FLIP':
            return f'!({rest})'
        op = JUNC_MAP.get(junc.name, '&&')
        return f'{comp} {op} {rest}'

    def t_comp(self, node: Node) -> str:
        children = node.children
        if len(children) == 1:
            # ID ou BOOL sozinho
            return self.t_expressao(children[0])
        expr1 = self.t_expressao(children[0])
        op    = REL_MAP.get(children[1].name, '==')
        expr2 = self.t_expressao(children[2])
        return f'{expr1} {op} {expr2}'

    # ---- EXPRESSAO ----
    def t_expressao(self, node: Node) -> str:
        if node.name == 'FATOR':
            return self.t_fator(node)
        fator = self.t_fator(node.children[0])
        expr  = node.children[1]
        if expr.name == 'VAZIO':
            return fator
        return fator + self.t_expr(expr)

    def t_expr(self, node: Node) -> str:
        if node.name == 'VAZIO':
            return ''
        op    = ARIT_MAP.get(node.children[0].name, '+')
        fator = self.t_fator(node.children[1])
        rest  = self.t_expr(node.children[2])
        return f' {op} {fator}{rest}'

    # ---- FATOR ----
    def t_fator(self, node: Node) -> str:
        child = node.children[0]
        if child.name == 'NUM':
            return child.value
        elif child.name == 'ID':
            return child.value
        elif child.name == 'BOOL':
            return 'true' if child.value == 'alive' else 'false'
        elif child.name == 'EPAREN':
            expr = self.t_expressao(node.children[1])
            return f'({expr})'
        return str(child.value)

    # ---- helpers ----
    def resolve_tipo(self, tipo_node: Node) -> str:
        names = tuple(c.name for c in tipo_node.children)
        cs_type = TYPE_MAP.get(names)
        if cs_type is None:
            # fallback: pega o último tipo reconhecido
            for name in reversed(names):
                cs_type = TYPE_MAP.get((name,))
                if cs_type:
                    break
            if cs_type is None:
                cs_type = 'int'
        return cs_type

    def t_bloco_indented(self, bloco: Node) -> str:
        self.indent += 1
        result = self.t_bloco(bloco)
        self.indent -= 1
        return result


def translate(tree: Node) -> str:
    t = Translator()
    return t.translate(tree)
