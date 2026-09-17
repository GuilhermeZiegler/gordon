from test._common import separador
from utils.db import ler_tabela


def run():
    separador("OVERVIEW — contagem por tabela")

    tabelas = [
        "produtos", "insumos", "ficha_tecnica",
        "clientes", "funcionarios",
        "mesas", "pedidos",
        "movimentacoes", "delivery", "agendamentos",
        "compras", "estoque", "estoque_baixas", "estoque_inventario",
        "historico_mesas", "historico_pedidos",
    ]

    for t in tabelas:
        try:
            df = ler_tabela(t)
            print(f"  {t:<25} {len(df):>6} linhas")
        except Exception as e:
            print(f"  {t:<25} ERRO: {e}")

    for t in ["caixa", "config", "historico_caixa", "historico_estoque",
              "historico_baixas", "historico_inventario", "historico_nao_baixados",
              "historico_compras"]:
        try:
            df = ler_tabela(t)
            if df.empty:
                print(f"  {t:<25} (vazio)")
            else:
                valor = df["dados"].iloc[0]
                if isinstance(valor, list):
                    print(f"  {t:<25} JSONB lista com {len(valor)} item(ns)")
                elif isinstance(valor, dict):
                    print(f"  {t:<25} JSONB dict com {len(valor)} chave(s)")
                else:
                    print(f"  {t:<25} JSONB")
        except Exception as e:
            print(f"  {t:<25} ERRO: {e}")