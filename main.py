#!/usr/bin/env python3
# ============================================================
# COMPILADOR MTG-Lang → C#
# Uso: python main.py <arquivo.mtg> [--tokens] [--arvore]
# ============================================================

import sys
import os
from lexer      import tokenize, print_tokens, LexerError
from parser     import parse, ParseError
from translator import translate, TranslatorError


def main():
    args       = sys.argv[1:]
    show_tokens = '--tokens' in args
    show_tree   = '--arvore' in args
    files       = [a for a in args if not a.startswith('--')]

    if not files:
        print('Uso: python main.py <arquivo.mtg> [--tokens] [--arvore]')
        print()
        print('  --tokens   Exibe a lista de tokens reconhecidos')
        print('  --arvore   Exibe a árvore de derivação')
        sys.exit(1)

    input_file = files[0]

    if not os.path.exists(input_file):
        print(f'[ERRO] Arquivo não encontrado: {input_file}')
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        source = f.read()

    # ---- Análise Léxica ----
    print(f'\n{"="*55}')
    print(f'  Compilador MTG-Lang → C#')
    print(f'  Arquivo: {input_file}')
    print(f'{"="*55}')

    try:
        tokens = tokenize(source)
        print(f'[✓] Análise léxica concluída. {len(tokens)} token(s) encontrado(s).')
    except LexerError as e:
        print(e)
        sys.exit(1)

    if show_tokens:
        print_tokens(tokens)

    # ---- Análise Sintática ----
    try:
        tree = parse(tokens)
        print('[✓] Análise sintática concluída.')
    except ParseError as e:
        print(e)
        sys.exit(1)

    if show_tree:
        print('\n── Árvore de Derivação ──')
        print(tree)
        print()

    # ---- Tradução ----
    try:
        csharp_code = translate(tree)
        print('[✓] Tradução para C# concluída.')
    except TranslatorError as e:
        print(e)
        sys.exit(1)

    # ---- Escrita do arquivo de saída ----
    base        = os.path.splitext(input_file)[0]
    output_file = base + '.cs'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(csharp_code)

    print(f'[✓] Arquivo gerado: {output_file}')
    print(f'{"="*55}\n')
    print('── Código C# gerado ──')
    print(csharp_code)


if __name__ == '__main__':
    main()
