#!/usr/bin/env python3
"""Leia suas tarefas e gere um plano local."""
import argparse
from comum import *


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=RAIZ / 'exemplos/minhas-tarefas.csv')
    parser.add_argument('--saida', type=Path, default=RAIZ / 'relatorio.md')
    parser.add_argument('--data', default=date.today().isoformat())
    parser.add_argument('--cenario', choices=CENARIOS, default='base')
    args = parser.parse_args()
    inicio = data(args.data)
    tarefas = ler_csv(args.csv, ['tarefa', 'horas_semana', 'nivel', 'critico'])
    for i, t in enumerate(tarefas, 2):
        t['horas'] = positivo(t['horas_semana'])
        if t['nivel'] not in ['AL1', 'AL2', 'AL3', 'AL4', 'AL5']:
            raise ValueError(f'linha {i}: nível deve ser AL1..AL5')
        if t['critico'] not in ('s', 'n'):
            raise ValueError(f'linha {i}: critico deve ser s ou n')
    total = sum(t['horas'] for t in tarefas)
    parcela = 100 * sum(t['horas'] for t in tarefas if t['nivel'] in ('AL4', 'AL5')) / total
    k = curva([(data(d), p) for d, p in PONTOS_AL5])[2] * CENARIOS[args.cenario]
    linhas = ['# Minha escada', '', f'Data: {inicio}. Cenário: {args.cenario}.',
              f'Total: {total:g} horas/semana. IA lidera (AL4+AL5): {parcela:.1f}%.',
              f'Anthropic em ago/2026: 26% em AL4. Diferença: {parcela - 26:+.1f} pontos percentuais.',
              'Comparação ilustrativa: sua rotina não é a mesma amostra de P&D de modelos.', '',
              '## Projeção da parcela de horas em AL4+AL5', '', 'É extrapolação, não profecia.',
              'Usa a inclinação logística dos marcos AL5 do relatório, ancorada na sua parcela atual.',
              'Transferir essa velocidade para sua rotina é uma hipótese, não uma previsão de AL5.', '']
    if parcela in (0, 100):
        linhas += ['Com 0% ou 100%, a logística não estima uma trajetória finita. Não inventamos um ponto inicial.']
    else:
        linhas += ['Meses à frente | Parcela ilustrativa', '--- | ---']
        for meses in (0, 1, 3, 6, 12):
            z = logit(parcela) + k * meses
            p = 100 / (1 + math.exp(-z)) if z >= 0 else 100 * math.exp(z) / (1 + math.exp(z))
            linhas.append(f'{meses} | {p:.1f}%')
        for alvo in (50, 95):
            linhas.append(f'{alvo}%: ' + ('já alcançado.' if parcela >= alvo else str(deslocar(inicio, (logit(alvo) - logit(parcela)) / k))))
    elegiveis = sorted((t for t in tarefas if t['critico'] == 'n' and t['nivel'] != 'AL5'), key=lambda t: -t['horas'])[:3]
    linhas += ['', '## Subir um nível neste mês', '']
    linhas += [f"- {t['tarefa']}: {t['horas']:g} h/semana; {t['nivel']} → AL{int(t['nivel'][-1])+1}. Teste em amostra e confira a qualidade antes de ampliar." for t in elegiveis] or ['Nenhuma tarefa elegível.']
    linhas += ['', '## Manter revisão humana', '', 'Em tarefas críticas, AL4 é o teto sugerido: humano confere e aprova antes de usar.', '']
    linhas += [f"- {t['tarefa']} ({t['nivel']}): " + ('retire a automação sem revisão; volte a AL4 com checagem.' if t['nivel'] == 'AL5' else ('já está no teto sugerido (AL4): mantenha a conferência de dados, exceções e resultado.' if t['nivel'] == 'AL4' else 'pode subir até AL4, sempre com conferência humana de dados, exceções e resultado.')) for t in tarefas if t['critico'] == 's'] or ['Nenhuma tarefa marcada como crítica.']
    args.saida.write_text('\n'.join(linhas) + '\n', encoding='utf-8')
    print('\n'.join(linhas))
    print(f'\nArquivo gerado: {args.saida}')


if __name__ == '__main__':
    executar(main)
