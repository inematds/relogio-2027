# ⏰ Relógio 2027 — Prepare-se: a IA vai superar humanos

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Relógio 2027](guia/assets/banner.jpg)](https://inematds.github.io/relogio-2027/guia/)

## O que é

O Relógio 2027 é um kit gratuito de três scripts em Python para quem quer entender a velocidade da IA e se preparar sem pânico. O primeiro refaz as projeções da atualização de novembro de 2026 do AI 2027 e deixa você mudar as hipóteses. O segundo pega a lista das suas tarefas, dá um nível de automação de 1 a 5 a cada uma e mostra quanto da sua semana a IA já lidera, com um plano para o mês. O terceiro guarda os sinais que você acompanha mês a mês. Só precisa de Python 3; nada sai da sua máquina.

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/relogio-2027/guia/**

## Vídeo

[Assista no YouTube](https://www.youtube.com/watch?v=PoPJ2SLFjsM) · [Short 9:16](https://youtube.com/shorts/ukmrqSJVL1k) · [Player com legendas e capítulos](https://inematds.github.io/relogio-2027/videos/)

## A tese em 5 linhas

1. Em 10/11/2026 o AI Futures Project (autores do cenário AI 2027) publicou que a aceleração causada pela IA já está cerca de cinco meses à frente do cenário.
2. Base: o METR estimou que a Anthropic progride perto de 2x o ritmo histórico (faixa 1,3x a 3x).
3. Cerca de 80% dessa aceleração viria da própria IA: aproximadamente 1,7x de aceleração causada pela IA.
4. Com isso, todos os autores passaram a prever o Pesquisador de IA Sobre-humano (SAR) como provável em 2027.
5. E dão de 35% a 65% de chance de uma IA que automatiza todo o trabalho de escritório (TED-AI) antes de 2028.

Fonte: "Q3.5 Timelines Update", AI Futures Project, 10/11/2026 (números conferidos no texto publicado). São estimativas e extrapolações, não fatos futuros garantidos.

## Rode na sua máquina

Na pasta do projeto:

```sh
python3 kit/scripts/projecao.py
python3 kit/scripts/minha-escada.py
python3 kit/scripts/sinais.py
python3 kit/testes/run.py
```

Leia [COMECE-AQUI](kit/COMECE-AQUI.md). Edite os CSVs em `kit/exemplos/`. A escada grava `kit/relatorio.md`. Os valores de sinais são fictícios e servem apenas para demonstrar o painel.

Parâmetros da projeção:

```sh
python3 kit/scripts/projecao.py --dobra-meses 3.4 --ganho-hoje 12 --data-hoje 2026-09-30 --cenario base
python3 kit/scripts/projecao.py --cenario rapido
python3 kit/scripts/projecao.py --ponto-logistico 2027-06-01:50 --ponto-logistico 2027-11-01:95
python3 kit/scripts/minha-escada.py --data 2026-11-11 --saida kit/relatorio.md
```

## Como as contas funcionam

As constantes e seus comentários de fonte estão em `kit/scripts/comum.py`.

**Produtividade:** ganho autodeclarado de cerca de 1,2x no início de 2025, com Claude 3.7 Sonnet, para 12x com Model 4 em setembro de 2026. O modelo simples usa `ganho(t) = 1 + (ganho_inicial − 1) × 2^(t / dobra)`, com tempo em meses de 30,436875 dias. A dobra padrão é 3,4 meses. O ponto de 1,2x é contexto, não um segundo ponto de ajuste, pois não temos sua data exata.

O relatório citado indica aproximadamente 30x em março de 2027, 100x em setembro de 2027 e 1.000x em agosto de 2028. Com 12x em **30/09/2026**, convenção usada para o mês sem dia informado, a conta simples chega a fevereiro/2027, agosto/2027 e agosto/2028. Os dois primeiros marcos diferem em um mês. Não temos os dados completos do ajuste original. A saída mostra os resultados e as referências lado a lado.

**Automação:** AL1 humano sozinho; AL2 IA assiste; AL3 IA colabora; AL4 IA lidera com revisão; AL5 automação total. Os pontos observados informados de AL4 são 1% em março, 12% em maio, 14% em junho, 22% em julho e 26% em agosto de 2026. Nenhuma tarefa estava em AL5. Isso não permite inferir sozinho a curva AL5.

A logística AL5 deste kit é uma **reconstrução calibrada nos marcos projetados**: 50% em 01/06/2027 e 95% em 01/11/2027. Ajustamos uma reta em `log(p/(1−p))` pelo tempo. Com pontos personalizados, usamos mínimos quadrados. Não alegamos reproduzir a metodologia completa do relatório. Os pontos observados AL4 permanecem separados. A escada pessoal reutiliza só a inclinação dessa curva, como hipótese ilustrativa para sua parcela de horas AL4+AL5. Não prevê promoção individual de tarefas nem transformação automática de AL4 em AL5.

Os cenários lento, base e rapido multiplicam a velocidade por 0,75, 1 e 1,25. São escolhas de sensibilidade do kit, não intervalos de confiança do relatório. Na produtividade, a âncora é o ganho inicial. Na logística, a âncora é o valor ajustado na primeira data; com os pontos padrão, o marco de 50% fica fixo.

**O carro na subida:** o motor melhora cerca de 5x, como o ganho de P&D de software. A velocidade só sobe 1,7x. A ladeira fica mais íngreme e o compute, isto é, a capacidade de computação, não acelerou junto. Ganho numa tarefa não vira automaticamente o mesmo ganho no progresso total.

O painel mensal compara valores positivos, na mesma unidade, do mesmo indicador e de meses consecutivos. A média de dobra é `ln(2) / média(ln(valor_atual/valor_anterior))`, quando a taxa média é positiva. Não é média aritmética dos tempos de dobra. Uma seta não prova que o cenário adiantou ou atrasou: é um sinal simplificado. Receita não equivale a capacidade; benchmarks e percentuais têm teto.

## Combina com

- [negocios-com-ia](https://github.com/inematds/negocios-com-ia)
- [esforco-certo](https://github.com/inematds/esforco-certo)
- [audite-seu-claude](https://github.com/inematds/audite-seu-claude)
- [agente-que-aprende](https://github.com/inematds/agente-que-aprende)
- [caixa-do-agente](https://github.com/inematds/caixa-do-agente)
- [agente-blindado](https://github.com/inematds/agente-blindado)

Licença MIT, inematds.

Mais em inema.club
