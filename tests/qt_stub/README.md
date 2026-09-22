# Stub do PySide6

Stub permissivo usado pelo `test_ui_smoke.py` para importar e construir a
camada de UI num ambiente sem Qt e sem servidor gráfico (CI, contentores).

Não simula comportamento do Qt. Serve para apanhar nomes indefinidos, imports
em falta, ciclos de import e erros de assinatura no nosso próprio código --
que é exactamente a classe de erros que só aparece quando se abre a janela.

Os testes reais de lógica estão em `test_pipeline.py` e não precisam disto:
o `core/` não importa Qt.
