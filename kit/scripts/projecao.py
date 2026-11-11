#!/usr/bin/env python3
"""Duas extrapolações simples e configuráveis."""
import argparse
from comum import *


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dobra-meses', default='3.4')
    parser.add_argument('--ganho-hoje', default='12')
    parser.add_argument('--data-hoje', default=DATA_GANHO.isoformat(), help='data do ganho, AAAA-MM-DD')
    parser.add_argument('--cenario', choices=CENARIOS, default='base')
    parser.add_argument('--ponto-logistico', action='append', help='AAAA-MM-DD:percentual; repita ao menos duas vezes; substitui pontos AL5 padrão')
    args = parser.parse_args()
    dobra, ganho = positivo(args.dobra_meses), positivo(args.ganho_hoje)
    inicio = data(args.data_hoje)
    pontos = [ponto(p) for p in args.ponto_logistico] if args.ponto_logistico else [(data(d), p) for d, p in PONTOS_AL5]
    origem, b, k = curva(pontos)
    velocidade = CENARIOS[args.cenario]
    print('É extrapolação, não profecia. Cenário:', args.cenario)
    print(f'Ganho inicial: {ganho:g}x em {inicio}; dobra de (ganho − 1): {dobra:g} meses.')
    print('Alvo de ganho | Data calculada | Referência aproximada do relatório')
    for alvo, referencia in REFERENCIAS_GANHO.items():
        print(f'{alvo}x | {cruzamento_ganho(alvo, ganho, dobra, inicio, velocidade)} | {referencia}')
    print('\nParcela AL5 | Data calculada')
    for alvo in (50, 95):
        print(f'{alvo}% | {deslocar(origem, (logit(alvo) - b) / (k * velocidade))}')
    print('\nAL5: por padrão, curva calibrada nos marcos projetados de jun/2027 e nov/2027, não nos dados AL4.')
    print('Pontos usados:', '; '.join(f'{d}: {p:g}%' for d, p in pontos))
    print('AL4 observado: mar 1%, mai 12%, jun 14%, jul 22%, ago/2026 26%; AL5 observado: 0%.')
    print('Os números arredondados não reproduzem exatamente o ajuste original: datas podem diferir.')
    print('Cenários são sensibilidades escolhidas para este kit: velocidade lento 0,75x; base 1x; rapido 1,25x.')
    print('A logística muda a inclinação e mantém o valor ajustado na primeira data como âncora.')
    print('Produtividade autodeclarada não mede sozinha progresso real ou empregos.')


if __name__ == '__main__':
    executar(main)
