#!/usr/bin/env python3
"""Leia os logs locais do Claude Code e do Codex e resuma cada sessão (sem IA, nada sai da máquina)."""
import argparse
import glob
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

PAUSA = 10 * 60  # intervalo maior que 10 min não conta como tempo ativo
SEGREDO = re.compile(r'(sk-[A-Za-z0-9_\-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[abp]-[A-Za-z0-9\-]{10,}|AIza[0-9A-Za-z_\-]{20,}'
                     r'|[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[a-z]{2,}|\b\d{9,}\b)')


def limpa(texto):
    """Primeiro pedido, curto e sem segredo, e-mail ou número longo."""
    t = SEGREDO.sub('[oculto]', ' '.join(str(texto).split()))
    return t[:240]


def epoch(s):
    try:
        return datetime.fromisoformat(str(s).replace('Z', '+00:00')).timestamp()
    except ValueError:
        return None


def ativo(tempos):
    tempos.sort()
    return sum(b - a for a, b in zip(tempos, tempos[1:]) if b - a <= PAUSA) / 60


def ler_claude(caminho):
    """Uma sessão do Claude Code (~/.claude/projects/*/*.jsonl)."""
    humanos = acoes = 0
    tempos, primeiro, pasta, origem = [], '', '', ''
    try:
        with open(caminho, 'rb') as fh:
            for bruto in fh:
                if b'"user"' not in bruto[:400] and b'"assistant"' not in bruto:  # filtro rápido; o tipo é conferido abaixo
                    continue
                try:
                    d = json.loads(bruto)
                except ValueError:
                    continue
                tipo = d.get('type')
                if tipo not in ('user', 'assistant') or d.get('isSidechain'):
                    continue
                pasta = pasta or d.get('cwd') or ''
                origem = origem or d.get('entrypoint') or ''
                x = epoch(d.get('timestamp'))
                if x:
                    tempos.append(x)
                c = (d.get('message') or {}).get('content')
                if tipo == 'user':
                    texto = c if isinstance(c, str) else ''
                    if isinstance(c, list) and not any(isinstance(b, dict) and b.get('type') == 'tool_result' for b in c):
                        texto = ' '.join(str(b.get('text', '')) for b in c if isinstance(b, dict) and b.get('type') == 'text')
                    if texto and (not texto.startswith('<') or '<command-name>' in texto):
                        humanos += 1
                        primeiro = primeiro or texto
                elif isinstance(c, list):
                    acoes += sum(1 for b in c if isinstance(b, dict) and b.get('type') == 'tool_use')
    except OSError:
        return None
    if not tempos:
        return None
    return dict(fonte='claude', pasta=pasta, automatica=humanos <= 1, humanos=humanos, acoes=acoes,
                primeiro=limpa(primeiro), inicio=min(tempos), minutos=round(ativo(tempos), 1))


def ler_codex(caminho):
    """Uma sessão do Codex (~/.codex/sessions/AAAA/MM/DD/*.jsonl)."""
    humanos = acoes = 0
    tempos, primeiro, pasta, origem = [], '', '', ''
    try:
        with open(caminho, 'rb') as fh:
            for bruto in fh:
                try:
                    d = json.loads(bruto)
                except ValueError:
                    continue
                p = d.get('payload') or {}
                x = epoch(d.get('timestamp'))
                if d.get('type') == 'session_meta':
                    pasta, origem = p.get('cwd') or '', p.get('originator') or ''
                    continue
                if d.get('type') != 'response_item':
                    continue
                if x:
                    tempos.append(x)
                if p.get('type') == 'function_call':
                    acoes += 1
                elif p.get('type') == 'message' and p.get('role') == 'user':
                    texto = ' '.join(str(b.get('text', '')) for b in p.get('content') or [] if isinstance(b, dict))
                    if texto and not texto.lstrip().startswith('<'):
                        humanos += 1
                        primeiro = primeiro or texto
    except OSError:
        return None
    if not tempos:
        return None
    return dict(fonte='codex', pasta=pasta, automatica=origem == 'codex_exec' or humanos <= 1, humanos=humanos, acoes=acoes,
                primeiro=limpa(primeiro), inicio=min(tempos), minutos=round(ativo(tempos), 1))


def ler(item):
    fonte, caminho = item
    return ler_claude(caminho) if fonte == 'claude' else ler_codex(caminho)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dias', type=int, default=30)
    p.add_argument('--saida', type=Path, default=Path('sessoes.json'))
    p.add_argument('--claude', type=Path, default=Path.home() / '.claude/projects')
    p.add_argument('--codex', type=Path, default=Path.home() / '.codex/sessions')
    a = p.parse_args()
    corte = time.time() - a.dias * 86400
    itens = [('claude', c) for c in glob.glob(str(a.claude / '*/*.jsonl')) if os.path.getmtime(c) >= corte]
    itens += [('codex', c) for c in glob.glob(str(a.codex / '**/*.jsonl'), recursive=True) if os.path.getmtime(c) >= corte]
    with Pool(max(2, (os.cpu_count() or 4) // 2)) as pool:
        sessoes = [s for s in pool.imap_unordered(ler, itens, chunksize=16) if s and s['inicio'] >= corte]
    fim = datetime.now(timezone.utc)
    resumo = dict(gerado_em=fim.isoformat(timespec='seconds'), dias=a.dias, sessoes=sessoes)
    a.saida.write_text(json.dumps(resumo, ensure_ascii=False), encoding='utf-8')
    n = lambda f: sum(1 for s in sessoes if s['fonte'] == f)
    print(f'{len(sessoes)} sessões ({n("claude")} Claude Code, {n("codex")} Codex) em {a.dias} dias → {a.saida}')
    # aviso: a fonte cujos registros começam bem depois do início pedido (o Claude Code apaga logs com mais de 30 dias)
    for f, nome in (('claude', 'Claude Code'), ('codex', 'Codex')):
        ts = [s['inicio'] for s in sessoes if s['fonte'] == f]
        if ts and (time.time() - min(ts)) / 86400 < a.dias - 3:
            dias = int((time.time() - min(ts)) // 86400) + 1
            desde = datetime.fromtimestamp(min(ts)).date().isoformat()
            print(f'AVISO: você pediu {a.dias} dias, mas os registros do {nome} só cobrem {dias} dias (desde {desde}). '
                  'O Claude Code apaga registros com mais de 30 dias, a não ser que você aumente o cleanupPeriodDays; '
                  'o que já foi apagado não volta.', file=sys.stderr)


if __name__ == '__main__':
    main()
