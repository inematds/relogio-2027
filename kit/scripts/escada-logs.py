#!/usr/bin/env python3
"""Transforme o resumo dos logs (de-logs.py) na sua escada AL1–AL5, num relatório executivo e na missão do dia.

A parte conduzida pela IA = minutos feitos em AL4/AL5 sobre o total de minutos.
O nível vem do comportamento registrado no log (não de opinião):
  sessão que rodou sozinha (1 pedido, sem conversa) → AL5
  conversa: ações da IA por mensagem sua ≥ 15 → AL4 · ≥ 5 → AL3 · menos → AL2
O nome da tarefa vem de um modelo barato (--motor codex|ollama) ou de palavras-chave (--motor palavras).
"""
import argparse
import collections
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path

from comum import PONTOS_AL5, curva, data, logit, math

SEMANAS_POR_DIA = 1 / 7
ANTHROPIC = 26
BASTIDORES = ('claude-mem', 'observer tool', 'you are a claude-mem')
PALAVRAS = [  # reserva sem IA: (tarefa, crítica, palavras)
    ('Traduzir conteúdo', False, ['traduz', 'translate', 'spanish', 'english', 'espanhol', 'inglês']),
    ('Produzir vídeos', False, ['vídeo', 'video', 'reel', 'short', 'avatar', 'heygen', 'roteiro', 'youtu']),
    ('Publicar conteúdo', True, ['publica', 'telegram', 'metricool', 'postar', 'portal', 'yt-pubx']),
    ('Criar cursos', False, ['curso', 'aula', 'trilha', 'módulo']),
    ('Criar guias e projetos', False, ['guia', 'kit', 'repo', 'projeto', 'landing', 'site', 'página']),
    ('Pesquisar e resumir', False, ['resum', 'pesquis', 'analis', 'notícia', 'artigo', 'relatório', 'classifi']),
    ('Manter sistemas e bots', True, ['bot', 'servidor', 'vps', 'timer', 'painel', 'erro', 'falha', 'deploy']),
]


def chave(texto):
    t = re.sub(r'\d+', '#', texto.lower())
    return re.sub(r'\s+', ' ', t)[:60].strip() or '(vazio)'


def nivel(s):
    if s['automatica']:
        return 'AL5'
    k = s['acoes'] / max(s['humanos'], 1)
    return 'AL4' if k >= 15 else 'AL3' if k >= 5 else 'AL2'


# ---------------- modelos baratos ----------------
def pedir_codex(prompt, modelo, esforco):
    if not shutil.which('codex'):
        raise RuntimeError('codex não encontrado no PATH')
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / 'resposta.txt'
        cmd = ['codex', 'exec', '-m', modelo, '-c', f'model_reasoning_effort="{esforco}"', '-s', 'read-only',
               '--skip-git-repo-check', '--ephemeral', '-C', tmp, '-o', str(saida), '-']
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=900)
        if r.returncode != 0 or not saida.exists():
            raise RuntimeError('codex falhou: ' + (r.stderr or r.stdout)[-400:])
        return saida.read_text(encoding='utf-8')


def pedir_ollama(prompt, modelo):
    import urllib.request
    req = urllib.request.Request('http://127.0.0.1:11434/api/generate', method='POST',
                                 data=json.dumps({'model': modelo, 'prompt': prompt, 'stream': False, 'format': 'json'}).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())['response']


def json_da_resposta(texto):
    """Primeiro objeto JSON válido da resposta (o modelo às vezes manda mais de um, ou texto em volta)."""
    dec = json.JSONDecoder()
    for i, ch in enumerate(texto):
        if ch == '{':
            try:
                obj, _ = dec.raw_decode(texto, i)
                if isinstance(obj, dict):
                    return obj
            except ValueError:
                continue
    raise ValueError('resposta sem JSON')


class Motor:
    def __init__(self, a):
        self.a = a

    def pede(self, prompt):
        if self.a.motor == 'codex':
            return json_da_resposta(pedir_codex(prompt, self.a.modelo, self.a.esforco))
        return json_da_resposta(pedir_ollama(prompt, self.a.modelo))

    @property
    def nome(self):
        return 'palavras-chave (sem IA)' if self.a.motor == 'palavras' else f'{self.a.motor} {self.a.modelo}' + (f' ({self.a.esforco})' if self.a.motor == 'codex' else '')


# ---------------- tarefas ----------------
def tarefas_por_palavras(grupos):
    mapa, crit = {}, {}
    for k in grupos:
        texto = grupos[k].lower()
        for nome, c, pal in PALAVRAS:
            if any(p in texto for p in pal):
                mapa[k] = nome; crit[nome] = c
                break
        else:
            mapa[k] = 'Outras tarefas'; crit['Outras tarefas'] = False
    return mapa, crit


def tarefas_por_ia(motor, grupos, minutos):
    chaves = sorted(grupos, key=lambda k: -minutos[k])
    amostra = chaves[:200]
    linhas = '\n'.join(f'- ({minutos[k]:.0f} min) {grupos[k][:140]}' for k in amostra)
    base = motor.pede(
        'Abaixo estão os primeiros pedidos de sessões de trabalho de uma pessoa com assistentes de IA, com o tempo gasto.\n'
        'Agrupe em NO MÁXIMO 9 tarefas de trabalho, com nomes curtos em português do Brasil (2 a 5 palavras, ex.: "Produzir vídeos"),\n'
        'pensando no que a pessoa entrega (não na ferramenta). Marque critica=true quando um erro pode causar prejuízo público, financeiro ou de segurança\n'
        '(ex.: publicar, mexer em servidor, dinheiro). Responda SÓ JSON: {"tarefas":[{"nome":"...","critica":false}]}\n\n' + linhas)
    nomes = [t['nome'].strip() for t in base.get('tarefas', []) if t.get('nome')][:9]
    crit = {t['nome'].strip(): bool(t.get('critica')) for t in base.get('tarefas', []) if t.get('nome')}
    if not nomes:
        raise ValueError('o modelo não devolveu tarefas')
    lista = '\n'.join(f'{i}. {n}' for i, n in enumerate(nomes, 1))
    mapa = {}
    for ini in range(0, len(chaves), 250):
        lote = chaves[ini:ini + 250]
        corpo = '\n'.join(f'{j}|{grupos[k][:140]}' for j, k in enumerate(lote))
        r = motor.pede(
            f'Tarefas possíveis:\n{lista}\n0. Outras tarefas\n\nPara cada pedido abaixo (formato id|texto), diga o número da tarefa.\n'
            'Responda SÓ JSON: {"r":{"id":numero,...}} com todos os ids.\n\n' + corpo)
        for j, k in enumerate(lote):
            n = r.get('r', {}).get(str(j))
            try:
                n = int(n)
            except (TypeError, ValueError):
                n = 0
            mapa[k] = nomes[n - 1] if 1 <= n <= len(nomes) else 'Outras tarefas'
    crit.setdefault('Outras tarefas', False)
    return mapa, crit


# ---------------- relatório ----------------
def projecao(parcela, k):
    if not 0 < parcela < 100:
        return []
    out = []
    for meses in (0, 1, 3, 6):
        z = logit(parcela) + k * meses
        out.append({'meses': meses, 'pct': round(100 / (1 + math.exp(-z)), 1)})
    return out


def executivo(motor, ctx):
    tabela = '\n'.join(f"- {t['tarefa']}: {t['horas_semana']} h/sem, {t['nivel']}{' (crítica)' if t['critico'] else ''}, mistura {t['mix']}"
                       for t in ctx['tarefas'])
    return motor.pede(
        'Você escreve um relatório executivo curto, em português do Brasil, simples, para o dono do trabalho (não técnico).\n'
        f"Hoje é {ctx['hoje']}. Medido nos logs dos últimos {ctx['dias']} dias: a IA conduz {ctx['parcela_ia']}% das horas (AL4+AL5). "
        f"Antes: {ctx['parcela_anterior']}. Na Anthropic eram {ANTHROPIC}% (ago/2026).\n"
        'Escala: AL2 IA ajuda; AL3 colabora; AL4 IA conduz e a pessoa revisa; AL5 roda sozinho. Tarefa crítica para em AL4.\n'
        f'Tarefas:\n{tabela}\n\nMissões dos últimos dias (não repita): {ctx["missoes_anteriores"]}\n\n'
        'Responda SÓ JSON: {"leitura":"2-3 frases com o que os números dizem","acoes":["3 ações concretas, uma frase cada"],'
        '"missao_do_dia":{"titulo":"até 8 palavras, verbo no imperativo","texto":"2-3 frases: o que fazer hoje, em qual tarefa, e como saber que deu certo"}}.\n'
        'A missão do dia é UMA coisa que só a pessoa pode fazer hoje: decidir, conferir, ensinar a IA, criar algo novo ou cuidar de pessoas. '
        'Nada de prometer economia de horas. Não invente números.')


def executivo_sem_ia(ctx):
    alvo = next((t for t in ctx['tarefas'] if not t['critico'] and t['nivel'] in ('AL2', 'AL3')), ctx['tarefas'][0])
    return {'leitura': f"A IA conduz {ctx['parcela_ia']}% das horas medidas. A tarefa com mais espaço para subir é {alvo['tarefa']}.",
            'acoes': [f"{t['tarefa']}: testar {t['nivel']} → {t['proximo']} numa amostra." for t in ctx['tarefas'] if t['proximo']][:3],
            'missao_do_dia': {'titulo': f"Passe uma etapa de {alvo['tarefa'].lower()} para a IA",
                              'texto': 'Escolha uma etapa repetitiva, deixe a IA fazer do começo ao fim e só confira. Anote o que precisou corrigir.'}}


def markdown(ctx, ex):
    L = [f"# Relatório executivo · Minha escada", '', f"{ctx['hoje']} · últimos {ctx['dias']} dias · motor: {ctx['motor']}", '',
         f"## A IA conduz **{ctx['parcela_ia']}%** do seu trabalho", '']
    if ctx['parcela_anterior'] is not None:
        L.append(f"Antes: {ctx['parcela_anterior']}% ({ctx['parcela_ia'] - ctx['parcela_anterior']:+.1f} pontos). ")
    L += [f"Anthropic em ago/2026: {ANTHROPIC}%. Diferença: {ctx['parcela_ia'] - ANTHROPIC:+.1f} pontos.", '', ex['leitura'], '',
          f"## Missão de hoje: {ex['missao_do_dia']['titulo']}", '', ex['missao_do_dia']['texto'], '', '## Três ações', '']
    L += [f'{i}. {a}' for i, a in enumerate(ex['acoes'][:3], 1)]
    L += ['', '## Suas tarefas', '', 'Tarefa | h/sem* | Nível | Próximo | Mistura', '--- | --- | --- | --- | ---']
    L += [f"{t['tarefa']}{' ⚠️' if t['critico'] else ''} | {t['horas_semana']} | {t['nivel']} | {t['proximo'] or 'teto'} | "
          + ' · '.join(f'{k} {v}%' for k, v in t['mix'].items()) for t in ctx['tarefas']]
    L += ['', '## Projeção (esticar a curva, não é profecia)', '', 'Meses | Parte conduzida pela IA', '--- | ---']
    L += [f"{p['meses']} | {p['pct']}%" for p in ctx['projecao']]
    f = ctx['fontes']
    L += ['', '## De onde vêm os números', '',
          f"{f['claude_sessoes']} sessões do Claude Code e {f['codex_sessoes']} do Codex; {f['conversas']} conversas com você e "
          f"{f['automaticas']} automáticas; {f['acoes']} ações da IA. Lido só na sua máquina.",
          '* Horas de trabalho COM a IA, somando sessões em paralelo e tempo da máquina: servem para comparar tarefas, não para contar o seu tempo.',
          'O que você faz sem IA (reuniões, gravações, ligações) não aparece nos logs.']
    return '\n'.join(L) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--entrada', type=Path, default=Path('sessoes.json'))
    p.add_argument('--pasta', type=Path, default=Path.home() / '.local/share/minha-escada')
    p.add_argument('--motor', choices=['codex', 'ollama', 'palavras'], default='codex')
    p.add_argument('--modelo', default=os.environ.get('INEMA_CODEX_MENOR') or 'gpt-6-luna')
    p.add_argument('--esforco', default='low')
    a = p.parse_args()
    if a.motor == 'ollama' and a.modelo.startswith('gpt'):
        a.modelo = 'qwen3:8b'
    dados = json.loads(a.entrada.read_text(encoding='utf-8'))
    sess = [s for s in dados['sessoes'] if not any(b in s['primeiro'].lower() for b in BASTIDORES)]
    grupos, minutos = {}, collections.Counter()
    for s in sess:
        k = chave(s['primeiro']); grupos.setdefault(k, s['primeiro']); minutos[k] += s['minutos']
    motor = Motor(a)
    try:
        mapa, crit = tarefas_por_palavras(grupos) if a.motor == 'palavras' else tarefas_por_ia(motor, grupos, minutos)
    except Exception as e:  # sem modelo, não para: usa palavras-chave e avisa
        print(f'Aviso: {motor.nome} falhou ({e}); usando palavras-chave.')
        a.motor = 'palavras'; mapa, crit = tarefas_por_palavras(grupos)
    agg = collections.defaultdict(lambda: {'min': 0.0, 'niv': collections.Counter()})
    for s in sess:
        t = mapa[chave(s['primeiro'])]
        agg[t]['min'] += s['minutos']; agg[t]['niv'][nivel(s)] += s['minutos'] or 0.05
    semanas = dados['dias'] / 7
    tarefas = []
    for nome, g in sorted(agg.items(), key=lambda kv: -kv[1]['min']):
        h = round(g['min'] / 60 / semanas, 1)
        if h < 0.2:
            continue
        tot = sum(g['niv'].values())
        nv = g['niv'].most_common(1)[0][0]
        teto = 4 if crit.get(nome) else 5
        tarefas.append({'tarefa': nome, 'horas_semana': h, 'nivel': nv, 'critico': bool(crit.get(nome)),
                        'mix': {k: round(v / tot * 100) for k, v in g['niv'].most_common()},
                        'proximo': f'AL{int(nv[-1]) + 1}' if int(nv[-1]) < teto else None})
    if not tarefas:
        raise SystemExit('Erro: nenhuma sessão com tempo suficiente nos logs; aumente --dias ou confira as pastas.')
    # parcela = minutos realmente feitos em AL4/AL5 sobre o total (não o nível mais comum de cada tarefa)
    tot_min = sum(sum(g['niv'].values()) for g in agg.values()) or 1
    parcela = round(100 * sum(g['niv'][n] for g in agg.values() for n in ('AL4', 'AL5')) / tot_min, 1)
    a.pasta.mkdir(parents=True, exist_ok=True)
    hist_arq = a.pasta / 'historico.jsonl'
    hist = [json.loads(l) for l in hist_arq.read_text(encoding='utf-8').splitlines() if l.strip()] if hist_arq.exists() else []
    anterior = next((h['parcela_ia'] for h in reversed(hist) if h.get('data') != date.today().isoformat()), None)
    k = curva([(data(d), q) for d, q in PONTOS_AL5])[2]
    ctx = {'hoje': date.today().isoformat(), 'dias': dados['dias'], 'parcela_ia': parcela, 'parcela_anterior': anterior,
           'tarefas': tarefas, 'projecao': projecao(parcela, k), 'motor': motor.nome,
           'missoes_anteriores': [h.get('missao') for h in hist[-7:] if h.get('missao')],
           'fontes': {'claude_sessoes': sum(s['fonte'] == 'claude' for s in dados['sessoes']),
                      'codex_sessoes': sum(s['fonte'] == 'codex' for s in dados['sessoes']),
                      'conversas': sum(not s['automatica'] for s in sess), 'automaticas': sum(s['automatica'] for s in sess),
                      'acoes': sum(s['acoes'] for s in sess)}}
    try:
        ex = executivo_sem_ia(ctx) if a.motor == 'palavras' else executivo(motor, ctx)
        assert ex.get('missao_do_dia', {}).get('titulo') and ex.get('acoes')
    except Exception as e:
        print(f'Aviso: relatório pelo modelo falhou ({e}); usando o texto padrão.')
        ex = executivo_sem_ia(ctx)
    md = a.pasta / 'relatorio-executivo.md'
    md.write_text(markdown(ctx, ex), encoding='utf-8')
    with open(a.pasta / 'tarefas.csv', 'w', encoding='utf-8') as fh:
        fh.write('tarefa,horas_semana,nivel,critico\n')
        fh.writelines(f"\"{t['tarefa']}\",{t['horas_semana']},{t['nivel']},{'s' if t['critico'] else 'n'}\n" for t in tarefas)
    hoje = dados['gerado_em'][:10]
    escada = {'gerado_em': datetime.now().astimezone().isoformat(timespec='seconds'),
              'periodo': {'inicio': date.fromordinal(date.fromisoformat(hoje).toordinal() - dados['dias']).isoformat(), 'fim': hoje, 'dias': dados['dias']},
              'fontes': ctx['fontes'], 'parcela_ia': parcela, 'parcela_anterior': anterior, 'anthropic_ref': ANTHROPIC,
              'projecao': ctx['projecao'], 'tarefas': tarefas, 'leitura': ex['leitura'], 'acoes': ex['acoes'][:3],
              'missao_do_dia': ex['missao_do_dia'], 'relatorio_md': str(md), 'motor': motor.nome}
    tmp = a.pasta / 'escada.json.tmp'
    tmp.write_text(json.dumps(escada, ensure_ascii=False, indent=1), encoding='utf-8')
    tmp.replace(a.pasta / 'escada.json')
    hist = [h for h in hist if h.get('data') != date.today().isoformat()]
    hist.append({'data': date.today().isoformat(), 'parcela_ia': parcela, 'missao': ex['missao_do_dia']['titulo']})
    hist_arq.write_text(''.join(json.dumps(h, ensure_ascii=False) + '\n' for h in hist[-120:]), encoding='utf-8')
    print(md.read_text(encoding='utf-8'))
    print(f'Arquivos: {a.pasta}/escada.json, relatorio-executivo.md, tarefas.csv')


if __name__ == '__main__':
    main()
