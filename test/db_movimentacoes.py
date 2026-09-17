from test._common import separador, mostrar_tabela, _filtrar_por_data
from utils.db import ler_tabela
import pandas as pd


def run():
    separador("MOVIMENTAÇÕES")

    mov = ler_tabela("movimentacoes")
    print(f"  total: {len(mov)}")

    if mov.empty:
        return

    print("\n  por tipo:")
    print(mov["tipo"].value_counts().to_string())

    separador("MOVIMENTAÇÕES — hoje")
    df_hoje = _filtrar_por_data(mov, "data_movimentacao")
    mostrar_tabela(df_hoje, ["id_movimentacao", "tipo", "id_insumo", "quantidade", "unidade", "data_movimentacao", "id_pedido"])

    separador("ESTOQUE — tabela")
    estoque = ler_tabela("estoque")
    print(f"  total: {len(estoque)}")

    separador("COMPRAS")
    compras = ler_tabela("compras")
    print(f"  total: {len(compras)}")

    separador("ESTOQUE_BAIXAS")
    baixas = ler_tabela("estoque_baixas")
    print(f"  total: {len(baixas)}")