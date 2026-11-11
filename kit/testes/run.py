#!/usr/bin/env python3
"""Testes locais de resultados, erros e execução dos comandos."""
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / 'scripts'))
from comum import cruzamento_ganho, curva, data, deslocar, logit


class KitTestes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pasta = Path(self.tmp.name)

    def rodar(self, script, *args):
        return subprocess.run([sys.executable, str(KIT / 'scripts' / script), *map(str, args)],
                              cwd=self.pasta, capture_output=True, text=True,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), timeout=10)

    def csv(self, texto):
        p = self.pasta / 'entrada.csv'
        p.write_text(texto, encoding='utf-8')
        return p

    def erro(self, resultado, trecho):
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn('Erro:', resultado.stderr)
        self.assertIn(trecho, resultado.stderr)
        self.assertNotIn('Traceback', resultado.stderr)

    def mes_proximo(self, calculada, ano, mes):
        self.assertLessEqual(abs(calculada.year * 12 + calculada.month - (ano * 12 + mes)), 1)

    def test_01_30x_marco(self):
        self.mes_proximo(cruzamento_ganho(30), 2027, 3)

    def test_02_100x_setembro(self):
        self.mes_proximo(cruzamento_ganho(100), 2027, 9)

    def test_03_1000x_agosto(self):
        self.mes_proximo(cruzamento_ganho(1000), 2028, 8)

    def test_04_al5_marcos(self):
        origem, b, k = curva([(data('2027-06-01'), 50), (data('2027-11-01'), 95)])
        for alvo, mes in [(50, 6), (95, 11)]:
            calculada = deslocar(origem, (logit(alvo) - b) / k)
            self.mes_proximo(calculada, 2027, mes)
            self.assertLessEqual(abs((calculada - data(f'2027-{mes:02}-01')).days), 1)

    def test_05_projecao_comando(self):
        r = self.rodar('projecao.py')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('É extrapolação, não profecia', r.stdout)
        self.assertIn('95% | 2027-11-01', r.stdout)

    def test_06_cenarios_ordenados(self):
        datas = [cruzamento_ganho(100, velocidade=v) for v in (0.75, 1, 1.25)]
        self.assertGreater(datas[0], datas[1])
        self.assertGreater(datas[1], datas[2])

    def test_07_parametros_mudam_resultado(self):
        r = self.rodar('projecao.py', '--ganho-hoje', '30', '--data-hoje', '2026-12-01', '--dobra-meses', '6')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('30x | 2026-12-01', r.stdout)

    def test_08_pontos_personalizados(self):
        r = self.rodar('projecao.py', '--ponto-logistico', '2030-01-01:50', '--ponto-logistico', '2031-01-01:95')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('95% | 2031-01-01', r.stdout)

    def test_09_exemplo_relatorio(self):
        saida = self.pasta / 'relatorio.md'
        r = self.rodar('minha-escada.py', '--saida', saida, '--data', '2026-11-11')
        self.assertEqual(r.returncode, 0, r.stderr)
        texto = saida.read_text(encoding='utf-8')
        self.assertIn('28.6%', texto)  # 8 de 28 horas, não contagem de tarefas
        secao = texto.split('## Subir um nível neste mês')[1].split('## Manter revisão humana')[0]
        self.assertEqual(secao.count('\n- '), 3)
        self.assertLess(secao.index('Rascunhar textos'), secao.index('Organizar notas'))
        self.assertNotIn('Conferir pagamentos', secao)
        self.assertNotIn('Arquivar cópias', secao)
        self.assertIn('Revisar contratos', texto.split('## Manter revisão humana')[1])

    def test_10_nivel_invalido(self):
        p = self.csv('tarefa,horas_semana,nivel,critico\nTeste,2,AL6,n\n')
        self.erro(self.rodar('minha-escada.py', '--csv', p), 'AL1..AL5')

    def test_11_horas_invalidas(self):
        for valor in ('-1', '0', 'nan', 'inf', 'abc'):
            with self.subTest(valor=valor):
                p = self.csv(f'tarefa,horas_semana,nivel,critico\nTeste,{valor},AL1,n\n')
                self.erro(self.rodar('minha-escada.py', '--csv', p), '')

    def test_12_critico_invalido(self):
        p = self.csv('tarefa,horas_semana,nivel,critico\nTeste,2,AL2,talvez\n')
        self.erro(self.rodar('minha-escada.py', '--csv', p), 's ou n')

    def test_13_csv_vazio_e_colunas(self):
        for texto in ('', 'tarefa,horas_semana,nivel,critico\n', 'tarefa,horas_semana,nivel,critico\nA,2,AL1\n'):
            self.erro(self.rodar('minha-escada.py', '--csv', self.csv(texto)), '')

    def test_14_extremos_sem_inventar_curva(self):
        for nivel in ('AL1', 'AL5'):
            p = self.csv(f'tarefa,horas_semana,nivel,critico\nTeste,2,{nivel},s\n')
            r = self.rodar('minha-escada.py', '--csv', p, '--saida', self.pasta / 'r.md')
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('não estima uma trajetória finita', r.stdout)
            if nivel == 'AL5':
                self.assertIn('volte a AL4', r.stdout)

    def test_15_dobra_sinais(self):
        p = self.csv('mes,indicador,valor\n2026-09,A,10\n2026-10,A,20\n2026-09,B,10\n2026-10,B,40\n')
        r = self.rodar('sinais.py', '--csv', p)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('média de dobra: 0.67 meses', r.stdout)  # ln2 / média(ln2, ln4)
        self.assertIn('↑ adiantou', r.stdout)

    def test_16_queda_estabilidade(self):
        for atual, seta in [('5', '↓ atrasou'), ('10', '→ estável')]:
            p = self.csv(f'mes,indicador,valor\n2026-09,A,10\n2026-10,A,{atual}\n')
            r = self.rodar('sinais.py', '--csv', p)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(seta, r.stdout)
            self.assertIn('sem dobra finita', r.stdout)

    def test_17_mes_faltante(self):
        p = self.csv('mes,indicador,valor\n2026-08,A,10\n2026-10,A,20\n')
        r = self.rodar('sinais.py', '--csv', p)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('Sem pares de meses consecutivos', r.stdout)

    def test_18_sinais_invalidos(self):
        for linhas, mensagem in [('2026-13,A,10\n', 'data inválida'), ('2026-09,A,0\n', 'maior que zero'),
                                  ('2026-09,A,10\n2026-09,A,20\n', 'duplicado')]:
            p = self.csv('mes,indicador,valor\n' + linhas)
            self.erro(self.rodar('sinais.py', '--csv', p), mensagem)

    def test_19_projecao_invalida(self):
        for args in [('--ganho-hoje', '1'), ('--dobra-meses', '0'), ('--data-hoje', 'ontem'),
                     ('--ponto-logistico', '2027-06-01:100'), ('--ganho-hoje', 'nan')]:
            self.erro(self.rodar('projecao.py', *args), '')

    def test_20_curva_invalida(self):
        for pontos in [[(data('2027-01-01'), 20), (data('2027-01-01'), 50)],
                       [(data('2027-01-01'), 90), (data('2028-01-01'), 50)]]:
            with self.assertRaises(ValueError):
                curva(pontos)

    def test_21_sinais_exemplo(self):
        r = self.rodar('sinais.py')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('4 indicador(es)', r.stdout)
        self.assertIn('fictício', r.stdout)

    def test_22_arquivo_ausente(self):
        self.erro(self.rodar('minha-escada.py', '--csv', self.pasta / 'nao-existe.csv'), '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
