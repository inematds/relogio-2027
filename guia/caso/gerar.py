#!/usr/bin/env python3
"""Gera guia/caso/index.html (PT) com o caso real do Nei a partir de dados.json (fotografia de um dia).
Uso: python3 guia/caso/gerar.py [--de ~/.local/share/minha-escada/escada.json]  (--de atualiza a fotografia)"""
import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / 'kit' / 'scripts'))
from comum import PONTOS_AL5, curva, data, deslocar, logit, math  # noqa: E402

NIV = ['AL2', 'AL3', 'AL4', 'AL5']
COR = {'AL2': 'var(--l2)', 'AL3': 'var(--l3)', 'AL4': 'var(--l4)', 'AL5': 'var(--l5)'}
MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
e = html.escape


def br(x, casas=1):
    return f'{x:.{casas}f}'.replace('.', ',')


def mil(n):
    return f'{n:,}'.replace(',', '.')


def mes_ano(d):
    return f'{MES[d.month - 1]}/{d.year}'


def sig(z):
    return 100 / (1 + math.exp(-z))


def calcula(esc):
    T = esc['tarefas']
    horas = {n: 0.0 for n in NIV}
    for t in T:
        for k, v in t['mix'].items():
            if k in horas:
                horas[k] += t['horas_semana'] * v / 100
    tot = sum(horas.values())
    dist = {n: round(horas[n] / tot * 100, 1) for n in NIV}
    k = curva([(data(d), p) for d, p in PONTOS_AL5])[2]
    hoje = date.fromisoformat(esc['periodo']['fim'])
    p45, p5 = esc['parcela_ia'], dist['AL5']
    serie = lambda p0: [(m, round(sig(logit(p0) + k * m), 1)) for m in range(0, 13)]
    quando = lambda p0, alvo: None if p0 >= alvo else deslocar(hoje, (logit(alvo) - logit(p0)) / k)
    por_tarefa = []
    for t in T:
        a5 = t['mix'].get('AL5', 0)
        a45 = a5 + t['mix'].get('AL4', 0)
        if t['critico']:
            alvo = quando(a45, 95) if 0 < a45 < 95 else None
            fim = 'teto AL4 (crítica)' + (f' · 95% em AL4+ em {mes_ano(alvo)}' if alvo else '')
        elif a5 <= 0:
            fim = 'ainda sem AL5 medido'
        else:
            q = quando(a5, 50)
            fim = (f'50% em AL5 em {mes_ano(q)}' if q else 'já passou de 50% em AL5')
        por_tarefa.append({**t, 'al5': a5, 'al45': a45, 'fim': fim})
    return {'dist': dist, 'k': k, 'hoje': hoje, 'serie45': serie(p45), 'serie5': serie(p5),
            'q45_95': quando(p45, 95), 'q5_50': quando(p5, 50), 'q5_95': quando(p5, 95), 'tarefas': por_tarefa,
            'horas_total': round(sum(t['horas_semana'] for t in T), 1)}


# ---------------- gráficos SVG ----------------
def svg_barra_total(dist):
    x, out = 0.0, []
    for n in NIV:
        w = dist[n] * 9.2
        out.append(f'<rect x="{x:.1f}" y="10" width="{w:.1f}" height="46" fill="{COR[n]}"/>')
        if dist[n] >= 8:
            out.append(f'<text x="{x + w / 2:.1f}" y="39" text-anchor="middle" class="sv-in">{n} {br(dist[n])}%</text>')
        x += w
    return (f'<svg viewBox="0 0 920 66" class="sv" role="img" aria-label="Divisão das horas por nível: '
            + ', '.join(f'{n} {br(dist[n])}%' for n in NIV) + '">' + ''.join(out) + '</svg>')


def svg_tarefas(T):
    mx = max(t['horas_semana'] for t in T)
    H, out = 34, []
    for i, t in enumerate(T):
        y = i * H + 6
        out.append(f'<text x="0" y="{y + 17}" class="sv-lb">{e(t["tarefa"])}{" ⚠" if t["critico"] else ""}</text>')
        x = 330.0
        for n in NIV:
            w = t['horas_semana'] / mx * 520 * t['mix'].get(n, 0) / 100
            if w > 0:
                out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="22" fill="{COR[n]}"><title>{n}: {t["mix"].get(n, 0)}%</title></rect>')
            x += w
        out.append(f'<text x="{x + 8:.1f}" y="{y + 16}" class="sv-v">{br(t["horas_semana"])} h · {t["nivel"]}</text>')
    h = len(T) * H + 10
    return f'<svg viewBox="0 0 980 {h}" class="sv" role="img" aria-label="Horas por semana de cada tarefa, divididas por nível">{"".join(out)}</svg>'


def svg_projecao(c):
    W, H, L, R, TOP, BOT = 920, 340, 56, 44, 26, 44
    px = lambda m: L + m / 12 * (W - L - R)
    py = lambda p: TOP + (100 - p) / 100 * (H - TOP - BOT)
    out = []
    for p in (0, 25, 50, 75, 95, 100):
        cls = 'sv-ref' if p in (50, 95) else 'sv-grid'
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{py(p):.1f}" y2="{py(p):.1f}" class="{cls}"/>'
                   f'<text x="{L - 8}" y="{py(p) + 4:.1f}" text-anchor="end" class="sv-ax">{p}%</text>')
    for m in range(0, 13, 2):
        d = deslocar(c['hoje'], m)
        out.append(f'<text x="{px(m):.1f}" y="{H - 18}" text-anchor="middle" class="sv-ax">{mes_ano(d)}</text>')
    for chave, cor, nome in (('serie45', 'var(--l4)', 'AL4+AL5'), ('serie5', 'var(--l5)', 'AL5')):
        pts = ' '.join(f'{px(m):.1f},{py(p):.1f}' for m, p in c[chave])
        out.append(f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="3.5"/>')
        for m, p in c[chave]:
            if m in (0, 1, 3, 6, 12):
                out.append(f'<circle cx="{px(m):.1f}" cy="{py(p):.1f}" r="4.5" fill="{cor}"><title>{nome}: {br(p)}%</title></circle>'
                           f'<text x="{px(m):.1f}" y="{py(p) - 10:.1f}" text-anchor="middle" class="sv-v">{br(p, 0)}%</text>')
    return (f'<svg viewBox="0 0 {W} {H}" class="sv" role="img" aria-label="Projeção de 12 meses: parte conduzida pela IA (AL4+AL5) e parte que roda sozinha (AL5)">'
            + ''.join(out) + '</svg>')


def svg_comparacao(esc, dist):
    linhas = [('Nei: IA conduz (AL4+AL5)', esc['parcela_ia'], 'var(--l4)'), ('Anthropic ago/2026: IA lidera (AL4)', 26, 'var(--old)'),
              ('Nei: roda sozinho (AL5)', dist['AL5'], 'var(--l5)'), ('Anthropic ago/2026: roda sozinho (AL5)', 0, 'var(--old)')]
    out = []
    for i, (nome, v, cor) in enumerate(linhas):
        y = i * 40 + 6
        out.append(f'<text x="0" y="{y + 17}" class="sv-lb">{e(nome)}</text>'
                   f'<rect x="330" y="{y}" width="{max(v * 5.4, 3):.1f}" height="24" fill="{cor}"/>'
                   f'<text x="{338 + v * 5.4:.1f}" y="{y + 17}" class="sv-v">{br(v)}%</text>')
    return f'<svg viewBox="0 0 920 166" class="sv" role="img" aria-label="Comparação com a Anthropic">{"".join(out)}</svg>'


# ---------------- página ----------------
def pagina(esc, c):
    f, d, T = esc['fontes'], c['dist'], c['tarefas']
    linhas_tab = ''.join(
        f'<tr><td>{e(t["tarefa"])}{" <span class=crit>crítica</span>" if t["critico"] else ""}</td><td>{br(t["horas_semana"])}</td>'
        f'<td><b>{t["nivel"]}</b></td><td>{br(t["al45"], 0)}%</td><td>{br(t["al5"], 0)}%</td><td>{e(t["fim"])}</td></tr>' for t in T)
    proj_tab = ''.join(f'<tr><td>{m}</td><td>{mes_ano(deslocar(c["hoje"], m))}</td><td>{br(p45)}%</td><td>{br(p5)}%</td></tr>'
                       for (m, p45), (_, p5) in zip(c['serie45'], c['serie5']) if m in (0, 1, 2, 3, 6, 9, 12))
    q = lambda x: mes_ano(x) if x else 'já alcançado'
    leg = ''.join(f'<span><i style="background:{COR[n]}"></i>{n} {lbl}</span>' for n, lbl in
                  (('AL2', 'a IA ajuda'), ('AL3', 'a IA colabora'), ('AL4', 'a IA conduz, você revisa'), ('AL5', 'roda sozinho')))
    return f'''
<header class="cz-hero" id="top"><div class="wrap">
  <span class="chip">Caso real · medido em {d_br(esc['periodo']['fim'])}</span>
  <h1>A escada do Nei: <span class="amb">a IA já conduz {br(esc['parcela_ia'])}%</span> do trabalho</h1>
  <p class="lead">Este é o resultado do kit rodado nos logs reais de um mês de trabalho do Nei Maldaner (INEMA) com o Claude Code e o Codex. Serve de exemplo de como ler a sua própria escada e de para onde ela aponta.</p>
  <div class="kpis">
    <div class="kpi"><b>{br(esc['parcela_ia'])}%</b><span>das horas a IA conduz (AL4+AL5)</span></div>
    <div class="kpi"><b>{br(d['AL5'])}%</b><span>já roda sozinho (AL5)</span></div>
    <div class="kpi"><b>26%</b><span>Anthropic, ago/2026 (AL4)</span></div>
    <div class="kpi"><b>{q(c['q45_95'])}</b><span>projeção: 95% conduzido pela IA</span></div>
  </div>
</div></header>

<section id="medida"><div class="wrap">
  <span class="chip">Como foi medido</span>
  <h2>Um mês de logs, <span class="amb">lido na própria máquina</span></h2>
  <p class="sub">De {d_br(esc['periodo']['inicio'])} a {d_br(esc['periodo']['fim'])}. O kit leu {mil(f['claude_sessoes'])} sessões do Claude Code e {mil(f['codex_sessoes'])} do Codex: {mil(f['conversas'])} conversas com o Nei e {mil(f['automaticas'])} sessões que rodaram sozinhas (scripts, timers, bots). A IA fez {mil(f['acoes'])} ações (comandos, edições, leituras). Um modelo barato ({e(esc['motor'])}) só agrupou os pedidos em tarefas; o nível de cada sessão vem do comportamento registrado, não de opinião.</p>
  <div class="regra">
    <div><b>Rodou sozinha</b><span>um pedido, sem conversa → AL5</span></div>
    <div><b>Conversa com muita ação</b><span>15+ ações da IA por mensagem → AL4</span></div>
    <div><b>Conversa média</b><span>5 a 15 ações por mensagem → AL3</span></div>
    <div><b>Conversa curta</b><span>menos de 5 → AL2</span></div>
  </div>
</div></section>

<section id="escada"><div class="wrap">
  <span class="chip">A escada</span>
  <h2>Onde estão as horas, <span class="amb">nível por nível</span></h2>
  <p class="sub">A barra é o total de horas de trabalho com IA no mês, dividido pelos quatro níveis. Metade já está na parte de cima da escada.</p>
  <div class="chart">{svg_barra_total(d)}<div class="leg">{leg}</div></div>
  <h3 class="h3o" style="margin-top:34px">Por tarefa</h3>
  <p class="sub">Cada barra é uma tarefa: o comprimento são as horas por semana e as cores mostram em que nível elas foram feitas. ⚠ = tarefa crítica (vai a público ou mexe em sistema), que o kit segura no AL4.</p>
  <div class="chart rolar">{svg_tarefas(T)}<div class="leg">{leg}</div></div>
  <div class="tw"><table class="n cz-t"><tr><th>Tarefa</th><th>h/sem*</th><th>Nível</th><th>IA conduz</th><th>Roda sozinho</th><th>Para onde vai</th></tr>{linhas_tab}</table></div>
  <p class="nota">* Horas de trabalho COM a IA: somam sessões em paralelo e o tempo da máquina (por isso o total, {br(c['horas_total'])} h/semana, passa de uma semana real). Servem para comparar tarefas, não para contar o tempo da pessoa. O que é feito sem IA (gravar, reuniões, ligações) não aparece nos logs.</p>
</div></section>

<section id="comparacao"><div class="wrap">
  <span class="chip">Comparação</span>
  <h2>Mais adiantado que <span class="amb">o laboratório de ponta</span></h2>
  <p class="sub">No relatório de novembro de 2026, a IA liderava 26% da pesquisa da Anthropic e nenhuma tarefa estava totalmente automática. No caso do Nei, a IA conduz o dobro disso e quase um quinto já roda sozinho, principalmente traduções e as rotinas de vídeo.</p>
  <div class="chart">{svg_comparacao(esc, d)}</div>
  <p class="nota">Comparação ilustrativa: a rotina de um criador de conteúdo não é a mesma coisa que pesquisa de modelos de IA. O ponto é o ritmo, não a régua exata.</p>
</div></section>

<section id="projecao"><div class="wrap">
  <span class="chip">Projeção</span>
  <h2>Quando chega <span class="amb">no AL5</span></h2>
  <p class="sub">A curva usa a mesma velocidade que os autores do AI 2027 projetam para a pesquisa automática (de 50% em jun/2027 para 95% em nov/2027), aplicada ao ponto de partida do Nei. Linha âmbar: parte conduzida pela IA (AL4+AL5). Linha laranja: parte que roda sozinha (AL5).</p>
  <div class="chart rolar">{svg_projecao(c)}<div class="leg"><span><i style="background:var(--l4)"></i>IA conduz (AL4+AL5)</span><span><i style="background:var(--l5)"></i>roda sozinho (AL5)</span><span><i class="tracejado"></i>marcas de 50% e 95%</span></div></div>
  <div class="cz-cols">
    <div class="tw"><table class="n"><tr><th>Mês</th><th>Data</th><th>IA conduz</th><th>Roda sozinho</th></tr>{proj_tab}</table></div>
    <div class="marcos">
      <div><b>{q(c['q45_95'])}</b><span>95% do trabalho conduzido pela IA</span></div>
      <div><b>{q(c['q5_50'])}</b><span>metade rodando sozinha (50% em AL5)</span></div>
      <div><b>{q(c['q5_95'])}</b><span>quase tudo rodando sozinho (95% em AL5)</span></div>
    </div>
  </div>
  <p class="nota">É extrapolação, não profecia. Ela supõe que a rotina do Nei acelera no mesmo ritmo do laboratório, e ignora o teto das tarefas críticas: na prática, publicar e mexer em servidores continuam com revisão humana, então o AL5 total não chega a 100%.</p>
</div></section>

<section id="papel"><div class="wrap">
  <span class="chip">O que isso quer dizer</span>
  <h2>Se a IA faz quase tudo, <span class="amb">o que sobra para a pessoa?</span></h2>
  <p class="sub">Os números mostram que o Nei já não executa a maior parte do trabalho: ele dirige. Em um mês foram {mil(f['automaticas'])} sessões automáticas e só {mil(f['conversas'])} conversas. O trabalho diário vira cinco coisas que a IA não faz por ele.</p>
  <div class="papeis">
    <div><b>1. Escolher</b><span>o que vale fazer, para quem e o que fica de fora.</span></div>
    <div><b>2. Conferir e assinar</b><span>abrir de verdade uma entrega por dia; publicar fica no AL4.</span></div>
    <div><b>3. Ensinar o sistema</b><span>cada correção vira regra, e o erro não volta.</span></div>
    <div><b>4. Estar com gente</b><span>comunidade, alunos, lives: a confiança é com a pessoa real.</span></div>
    <div><b>5. Experimentar</b><span>testar o novo antes dos outros; a IA acelera o que já existe.</span></div>
  </div>
  <div class="aj-em" style="margin-top:22px"><b>Missão do dia (gerada pelo kit no dia da medição):</b> {e(esc['missao_do_dia']['titulo'])}. {e(esc['missao_do_dia']['texto'])}</div>
</div></section>

<section id="faca"><div class="wrap">
  <span class="chip">Faça o seu</span>
  <h2>Meça a sua escada <span class="amb">pelos seus logs</span></h2>
  <p class="sub">Se você usa Claude Code ou Codex, dois comandos geram o mesmo relatório para você. Nada sai da sua máquina, exceto os pedidos resumidos (sem segredos) para o modelo barato que agrupa as tarefas; com <code>--motor palavras</code> nem isso.</p>
<pre><span class="k">python3 kit/scripts/de-logs.py --dias 30</span>            <span class="c"># lê os logs → sessoes.json</span>
<span class="k">python3 kit/scripts/escada-logs.py --motor codex</span>   <span class="c"># ou --motor ollama / palavras</span></pre>
  <p class="mut" style="margin-top:12px"><a href="../#tecnico">Parte técnica do kit ↗</a> · <a href="../">Voltar ao guia Relógio 2027</a></p>
</div></section>
'''


def d_br(iso):
    a, m, d = iso.split('-')
    return f'{d}/{m}/{a}'


CSS = '''
  /* página do caso real */
  :root{--l2:#64748b;--l3:#38bdf8;--l4:#E2A23B;--l5:#f97316;--old:#4D8FE0}
  body.light{--l2:#94a3b8;--l3:#0284c7;--l4:#b9791d;--l5:#ea580c;--old:#2F6FC4}
  .cz-hero{padding:70px 0 46px;border-bottom:1px solid var(--line)} .cz-hero .lead{color:var(--mut);font-size:1.12rem;max-width:62ch} .cz-hero h1{font-family:Sora;font-size:clamp(2rem,4.4vw,3.1rem);line-height:1.1;margin:.3em 0}
  .kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:26px}
  .kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
  .kpi b{display:block;font:800 1.7rem Sora,sans-serif;color:var(--amb)} .kpi span{color:var(--mut);font-size:.86rem}
  .regra,.papeis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
  .papeis{grid-template-columns:repeat(5,minmax(0,1fr))}
  .regra>div,.papeis>div,.marcos>div{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:4px}
  .regra b,.papeis b{font-family:Sora} .regra span,.papeis span,.marcos span{color:var(--mut);font-size:.86rem}
  .sv{width:100%;height:auto;display:block}
  .chart.rolar{overflow-x:auto} .chart.rolar .sv{min-width:720px}
  .sv-in{fill:#111;font:700 15px Inter,sans-serif} .sv-lb{fill:var(--txt);font:500 14px Inter,sans-serif}
  .sv-v{fill:var(--txt);font:700 13px Inter,sans-serif} .sv-ax{fill:var(--mut);font:12px Inter,sans-serif}
  .sv-grid{stroke:var(--line);stroke-width:1} .sv-ref{stroke:var(--mut);stroke-dasharray:6 5;stroke-width:1.3}
  .leg .tracejado{background:repeating-linear-gradient(90deg,var(--mut) 0 5px,transparent 5px 9px)!important;height:3px!important;vertical-align:3px!important}
  .tw{overflow-x:auto;margin-top:18px} .cz-t td:nth-child(n+2),.cz-t th:nth-child(n+2){white-space:nowrap}
  .crit{font-size:.7rem;color:var(--l5);border:1px solid var(--l5);border-radius:6px;padding:0 5px;margin-left:6px}
  .nota{color:var(--mut);font-size:.84rem;margin-top:12px}
  .cz-cols{display:grid;grid-template-columns:1.2fr 1fr;gap:18px;align-items:start}
  .marcos{display:flex;flex-direction:column;gap:10px;margin-top:18px} .marcos b{font:800 1.3rem Sora,sans-serif;color:var(--amb)}
  @media(max-width:900px){.kpis,.regra{grid-template-columns:1fr 1fr}.papeis{grid-template-columns:1fr 1fr}.cz-cols{grid-template-columns:1fr}}
  @media(max-width:520px){.papeis{grid-template-columns:1fr}}
'''


def montar(esc):
    c = calcula(esc)
    guia = (AQUI.parent / 'index.html').read_text(encoding='utf-8')
    head = guia[:guia.index('</head>')]
    head = re.sub(r'<title>.*?</title>', '<title>Caso real: a escada do Nei — Relógio 2027</title>', head, 1)
    head = re.sub(r'(<meta name="description" content=")[^"]*"', r'\1Um mês de logs reais do Nei Maldaner (INEMA): quanto do trabalho a IA já conduz, por tarefa, e a projeção até o AL5."', head, 1)
    head = head.replace('</style>', CSS + '</style>', 1)
    nav = guia[guia.index('<nav>'):guia.index('</nav>') + 6]
    nav = re.sub(r'<div class="links">.*?<span class="lang">',
                 '<div class="links">\n    <a class="sec" href="#escada">A escada</a>\n    <a class="sec" href="#projecao">Projeção</a>\n'
                 '    <a class="sec" href="#papel">O papel</a>\n    <a class="sec" href="../">Guia</a>\n    <span class="lang">', nav, 1, flags=re.S)
    nav = nav.replace('href="#top"', 'href="../"')
    rodape = guia[guia.index('<footer>'):]
    corpo = pagina(esc, c)
    return head + '</head>\n<body>\n\n' + nav + '\n' + corpo + '\n' + rodape, c


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--de', type=Path, help='escada.json para atualizar a fotografia (dados.json)')
    a = p.parse_args()
    dados = AQUI / 'dados.json'
    if a.de:
        esc = json.loads(a.de.expanduser().read_text(encoding='utf-8'))
        for k in ('relatorio_md',):
            esc.pop(k, None)
        dados.write_text(json.dumps(esc, ensure_ascii=False, indent=1), encoding='utf-8')
    esc = json.loads(dados.read_text(encoding='utf-8'))
    pg, c = montar(esc)
    (AQUI / 'index.html').write_text(pg, encoding='utf-8')
    print('ok', AQUI / 'index.html', {k: (str(v) if isinstance(v, date) else v) for k, v in c.items() if k.startswith('q') or k == 'dist'})


if __name__ == '__main__':
    main()
