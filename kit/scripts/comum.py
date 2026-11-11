"""Contas locais. Apenas biblioteca padrão."""
import argparse
import csv
import math
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MES_DIAS = 365.2425 / 12
# Fonte: números do relatório AI Futures Project de 10/11/2026,
# fornecidos no pedido. Não houve consulta à rede nem verificação independente.
DOBRA_MESES = 3.4
GANHO_HOJE = 12.0
GANHO_INICIO_2025 = 1.2
# O relatório informa set/2026, sem dia. Convenção explícita: fim do mês.
DATA_GANHO = date(2026, 9, 30)
AL4_OBSERVADO = [('2026-03', 1), ('2026-05', 12), ('2026-06', 14),
                 ('2026-07', 22), ('2026-08', 26)]
AL5_OBSERVADO = 0
PONTOS_AL5 = [('2027-06-01', 50.0), ('2027-11-01', 95.0)]
PROGRESSO_TOTAL = 2.0
FAIXA_PROGRESSO = (1.3, 3.0)
PARCELA_ATRIBUIDA_IA = 0.80
ACELERACAO_IA = 1.7
MESES_A_FRENTE = 5
CHANCE_TED_ANTES_2028 = (35, 65)
MOTOR_SOFTWARE = 5
REFERENCIAS_GANHO = {30: '2027-03', 100: '2027-09', 1000: '2028-08'}
CENARIOS = {'lento': 0.75, 'base': 1.0, 'rapido': 1.25}


def numero(texto):
    try:
        n = float(texto)
    except (ValueError, TypeError):
        raise ValueError(f'número inválido: {texto!r}')
    if not math.isfinite(n):
        raise ValueError('o número precisa ser finito')
    return n


def positivo(texto):
    n = numero(texto)
    if n <= 0:
        raise ValueError('o valor precisa ser maior que zero')
    return n


def data(texto):
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ValueError(f'data inválida: {texto!r}; use AAAA-MM-DD')


def deslocar(inicio, meses):
    try:
        return inicio + timedelta(days=meses * MES_DIAS)
    except (OverflowError, ValueError):
        raise ValueError('projeção fora do calendário; ajuste os parâmetros')


def cruzamento_ganho(alvo, ganho=GANHO_HOJE, dobra=DOBRA_MESES,
                       inicio=DATA_GANHO, velocidade=1):
    if ganho <= 1:
        raise ValueError('ganho-hoje precisa ser maior que 1')
    return deslocar(inicio, dobra / velocidade * math.log2((alvo - 1) / (ganho - 1)))


def logit(p):
    if not 0 < p < 100:
        raise ValueError('percentual logístico precisa estar entre 0 e 100, sem os extremos')
    return math.log(p / (100 - p))


def curva(pontos):
    """Reta por mínimos quadrados em logit(p), com tempo em meses."""
    if len(pontos) < 2:
        raise ValueError('informe pelo menos dois pontos logísticos')
    origem = min(d for d, _ in pontos)
    xs = [(d - origem).days / MES_DIAS for d, _ in pontos]
    ys = [logit(p) for _, p in pontos]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    den = sum((x - mx)**2 for x in xs)
    if den == 0:
        raise ValueError('os pontos precisam ter datas diferentes')
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    if k <= 0:
        raise ValueError('os pontos precisam indicar crescimento logístico')
    return origem, my - k * mx, k


def ponto(texto):
    try:
        d, p = texto.split(':')
        return data(d), numero(p)
    except ValueError as exc:
        raise ValueError(f'ponto inválido; use AAAA-MM-DD:percentual ({exc})')


def ler_csv(caminho, campos):
    with Path(caminho).open(encoding='utf-8-sig', newline='') as f:
        leitor = csv.DictReader(f)
        if leitor.fieldnames != campos:
            raise ValueError('cabeçalho esperado: ' + ','.join(campos))
        linhas = list(leitor)
    if not linhas:
        raise ValueError('CSV vazio: inclua pelo menos uma linha')
    for i, linha in enumerate(linhas, 2):
        if None in linha or any(v is None or not v.strip() for v in linha.values()):
            raise ValueError(f'linha {i}: coluna ausente, vazia ou extra')
    return [{k: v.strip() for k, v in l.items()} for l in linhas]


def executar(funcao):
    try:
        funcao()
    except (ValueError, OSError, csv.Error) as exc:
        raise SystemExit(f'Erro: {exc}')
