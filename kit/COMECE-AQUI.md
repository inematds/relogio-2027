# Comece aqui — 10 minutos

Você precisa de Python 3. Não há instalação de pacotes. Abra o terminal na pasta `relogio-2027`. Os scripts funcionam sem rede e sem API.

## 1. Veja o relógio — 2 minutos

```sh
python3 kit/scripts/projecao.py
python3 kit/scripts/projecao.py --cenario lento
```

É extrapolação, não profecia. As datas são contas condicionais. Não são prazos garantidos.

## 2. Preencha sua escada — 5 minutos

Abra `kit/exemplos/minhas-tarefas.csv` num editor ou planilha. Preserve o cabeçalho. Salve em CSV com vírgulas e UTF-8. Use ponto decimal nas horas. Horas devem ser maiores que zero. Evite contar a mesma hora duas vezes. `critico` aceita `s` ou `n`.

AL1: humano faz sozinho. AL2: IA assiste. AL3: IA colabora. AL4: IA lidera e humano revisa. AL5: totalmente automatizado.

```sh
python3 kit/scripts/minha-escada.py
```

Leia `kit/relatorio.md`. Cada execução substitui esse arquivo. Para guardar outra versão, use `--saida kit/relatorio-novo.md`. A comparação com os 26% da Anthropic é ilustrativa. Sua rotina é diferente de P&D de modelos.

## 3. Registre os sinais — 3 minutos

Abra `kit/exemplos/sinais.csv`. **Todos os valores desse exemplo são fictícios.** Troque pelos números que você coletou. Os scripts não buscam dados. Registre mês (`AAAA-MM`), indicador e valor positivo. Use sempre a mesma unidade, definição, empresa e benchmark para cada indicador. Anote a fonte em um arquivo seu.

Acompanhe relatórios do METR, automação da Anthropic, receita de empresas de IA e benchmarks. Use indicadores em que maior significa avanço. Não misture latência ou custo, onde menor pode ser melhor, sem definir outra medida. Zero não permite calcular dobra e é rejeitado.

```sh
python3 kit/scripts/sinais.py
python3 kit/testes/run.py
```

A seta compara apenas meses consecutivos do mesmo indicador. Sem o mês anterior, não há comparação. A média usa taxas logarítmicas de crescimento, com peso igual por indicador. Queda e estabilidade entram nessa média; não viram uma dobra positiva. Ela resume sua cesta, não mede o avanço real da IA.

Os três arquivos em `kit/prompts/` podem ser copiados manualmente para qualquer IA. Esse uso externo é opcional. Não envie dados sensíveis. O kit não se conecta a nenhum serviço.
