# ⏰ Reloj 2027 — Prepárate: la IA va a superar a los humanos

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Reloj 2027](guia/assets/banner-es.jpg)](https://inematds.github.io/relogio-2027/guia/es/)

## Qué es

Reloj 2027 es un kit gratuito de tres scripts en Python para quienes quieren entender la velocidad de la IA y prepararse sin pánico. El primero rehace las proyecciones de la actualización de noviembre de 2026 de AI 2027 y te permite cambiar las hipótesis. El segundo toma la lista de tus tareas, asigna un nivel de automatización del 1 al 5 a cada una y muestra cuánto de tu semana ya lidera la IA, con un plan para el mes. El tercero guarda las señales que sigues mes a mes. Solo necesitas Python 3; nada sale de tu máquina.

## 📖 Guía de uso

Guía completa (landing + paso a paso): **https://inematds.github.io/relogio-2027/guia/es/**

## Vídeo

[Ver en YouTube](https://www.youtube.com/watch?v=PoPJ2SLFjsM) (en portugués) · [Short 9:16](https://youtube.com/shorts/ukmrqSJVL1k) · [Reproductor con subtítulos y capítulos](https://inematds.github.io/relogio-2027/videos/)

## La tesis en 5 líneas

1. El 10/11/2026, AI Futures Project (autores del escenario AI 2027) publicó que la aceleración causada por la IA ya está unos cinco meses por delante del escenario.
2. Base: METR estimó que Anthropic avanza a cerca de 2x el ritmo histórico (rango de 1,3x a 3x).
3. Cerca del 80% de esa aceleración provendría de la propia IA: aproximadamente 1,7x de aceleración causada por la IA.
4. Con esto, todos los autores pasaron a prever que el Investigador de IA Sobrehumano (SAR) sería probable en 2027.
5. Y estiman entre un 35% y un 65% de probabilidad de que una IA que automatice todo el trabajo de oficina (TED-AI) llegue antes de 2028.

Fuente: «Q3.5 Timelines Update», AI Futures Project, 10/11/2026 (cifras verificadas en el texto publicado). Son estimaciones y extrapolaciones, no hechos futuros garantizados.

## Ejecútalo en tu máquina

En la carpeta del proyecto:

```sh
python3 kit/scripts/projecao.py
python3 kit/scripts/minha-escada.py
python3 kit/scripts/sinais.py
python3 kit/testes/run.py
```

Lee [COMECE-AQUI](kit/COMECE-AQUI.md) (en portugués). Edita los CSV en `kit/exemplos/`. La escalera guarda `kit/relatorio.md`. Los valores de señales son ficticios y sirven únicamente para mostrar el panel.

Parámetros de la proyección:

```sh
python3 kit/scripts/projecao.py --dobra-meses 3.4 --ganho-hoje 12 --data-hoje 2026-09-30 --cenario base
python3 kit/scripts/projecao.py --cenario rapido
python3 kit/scripts/projecao.py --ponto-logistico 2027-06-01:50 --ponto-logistico 2027-11-01:95
python3 kit/scripts/minha-escada.py --data 2026-11-11 --saida kit/relatorio.md
```

## Cómo funcionan los cálculos

Las constantes y sus comentarios sobre las fuentes están en `kit/scripts/comum.py`.

**Productividad:** mejora autodeclarada de cerca de 1,2x a principios de 2025, con Claude 3.7 Sonnet, a 12x con Model 4 en septiembre de 2026. El modelo simple usa `ganho(t) = 1 + (ganho_inicial − 1) × 2^(t / dobra)`, con el tiempo en meses de 30,436875 días. El tiempo de duplicación predeterminado es de 3,4 meses. El valor de 1,2x es contexto, no un segundo punto de ajuste, porque no tenemos su fecha exacta.

El informe citado indica aproximadamente 30x en marzo de 2027, 100x en septiembre de 2027 y 1.000x en agosto de 2028. Con 12x el **30/09/2026**, convención usada para el mes sin día informado, el cálculo simple llega a febrero de 2027, agosto de 2027 y agosto de 2028. Los dos primeros hitos difieren en un mes. No tenemos todos los datos del ajuste original. La salida muestra los resultados y las referencias lado a lado.

**Automatización:** AL1 humano solo; AL2 la IA asiste; AL3 la IA colabora; AL4 la IA lidera con revisión; AL5 automatización total. Los puntos observados informados de AL4 son 1% en marzo, 12% en mayo, 14% en junio, 22% en julio y 26% en agosto de 2026. Ninguna tarea estaba en AL5. Esto no permite inferir por sí solo la curva de AL5.

La logística de AL5 de este kit es una **reconstrucción calibrada con los hitos proyectados**: 50% el 01/06/2027 y 95% el 01/11/2027. Ajustamos una recta en `log(p/(1−p))` a lo largo del tiempo. Con puntos personalizados, usamos mínimos cuadrados. No afirmamos reproducir la metodología completa del informe. Los puntos observados de AL4 se mantienen separados. La escalera personal reutiliza solo la pendiente de esa curva, como hipótesis ilustrativa para tu proporción de horas AL4+AL5. No predice la promoción individual de tareas ni la transformación automática de AL4 en AL5.

Los escenarios lento, base y rápido multiplican la velocidad por 0,75, 1 y 1,25. Son opciones de sensibilidad del kit, no intervalos de confianza del informe. En productividad, el ancla es la mejora inicial. En la logística, el ancla es el valor ajustado en la primera fecha; con los puntos predeterminados, el hito del 50% queda fijo.

**El coche en la subida:** el motor mejora cerca de 5x, como la mejora en I+D de software. La velocidad solo aumenta 1,7x. La pendiente se vuelve más pronunciada y el cómputo, es decir, la capacidad de computación, no se aceleró al mismo ritmo. La mejora en una tarea no se traduce automáticamente en la misma mejora en el progreso total.

El panel mensual compara valores positivos, en la misma unidad, del mismo indicador y de meses consecutivos. El tiempo de duplicación promedio es `ln(2) / media(ln(valor_actual/valor_anterior))`, cuando la tasa promedio es positiva. No es el promedio aritmético de los tiempos de duplicación. Una flecha no demuestra que el escenario se haya adelantado o retrasado: es una señal simplificada. Los ingresos no equivalen a capacidad; los benchmarks y los porcentajes tienen un límite máximo.

## Combina con

- [negocios-com-ia](https://github.com/inematds/negocios-com-ia)
- [esforco-certo](https://github.com/inematds/esforco-certo)
- [audite-seu-claude](https://github.com/inematds/audite-seu-claude)
- [agente-que-aprende](https://github.com/inematds/agente-que-aprende)
- [caixa-do-agente](https://github.com/inematds/caixa-do-agente)
- [agente-blindado](https://github.com/inematds/agente-blindado)

Licencia MIT, inematds.

Más en inema.club