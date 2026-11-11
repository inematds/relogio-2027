#!/usr/bin/env python3
"""Compare sinais mensais preenchidos à mão. Nenhuma consulta externa."""
import argparse
from comum import *


def mes(texto):
    if len(texto) != 7:
        raise ValueError('mes deve usar AAAA-MM')
    d = data(texto + '-01')
    return d.year * 12 + d.month


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=RAIZ / 'exemplos/sinais.csv')
    args = parser.parse_args()
    linhas = ler_csv(args.csv, ['mes', 'indicador', 'valor'])
    grupos = {}
    for l in linhas:
        m, v = mes(l['mes']), positivo(l['valor'])
        grupo = grupos.setdefault(l['indicador'], {})
        if m in grupo:
            raise ValueError(f"registro duplicado: {l['mes']} / {l['indicador']}")
        grupo[m] = (l['mes'], v)
    taxas = {}
    print('Painel de sinais — é extrapolação, não profecia.')
    print('↑ adiantou; ↓ atrasou; → estável. Leitura indicativa, sem medir meses reais do relógio.')
    print('Todos os indicadores devem usar uma medida em que maior significa avanço.')
    print('Mês | Indicador | Valor | Comparação com mês anterior | Dobra em meses')
    for indicador, registros in sorted(grupos.items()):
        for m, (rotulo, valor) in sorted(registros.items()):
            if m - 1 not in registros:
                print(f'{rotulo} | {indicador} | {valor:g} | sem mês anterior | —')
                continue
            anterior = registros[m - 1][1]
            taxa = math.log(valor) - math.log(anterior)
            seta = '↑' if taxa > 0 else '↓' if taxa < 0 else '→'
            dobra = f'{math.log(2)/taxa:.2f}' if taxa > 0 else 'sem dobra (queda ou estabilidade)'
            print(f'{rotulo} | {indicador} | {valor:g} | {seta} | {dobra}')
            taxas.setdefault(m, []).append(taxa)
    print('\nMédia de dobra: primeiro calculamos a média das taxas logarítmicas mensais, com peso igual.')
    for m, valores in sorted(taxas.items()):
        taxa = sum(valores) / len(valores)
        ano, mm = divmod(m - 1, 12)
        seta = '↑ adiantou' if taxa > 0 else '↓ atrasou' if taxa < 0 else '→ estável'
        dobra = f'{math.log(2)/taxa:.2f} meses' if taxa > 0 else 'sem dobra finita de crescimento'
        print(f'{ano:04}-{mm+1:02}: {seta}; média de dobra: {dobra}; {len(valores)} indicador(es) comparáveis.')
    if not taxas:
        print('Sem pares de meses consecutivos; média indisponível.')
    print('A cesta pode mudar entre meses. Compare a mesma cesta antes de concluir algo.')
    print('Receita e benchmarks são pistas diferentes; esta média não prova aceleração de pesquisa.')
    print('Percentuais e benchmarks têm teto: dobrá-los indefinidamente não faz sentido.')


if __name__ == '__main__':
    executar(main)
