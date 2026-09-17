from test._common import separador, _filtrar_por_data, mostrar_tabela
from utils.db import ler_tabela


def run():
    separador("PEDIDOS — tabela ativa")
    pedidos = ler_tabela("pedidos")
    print(f"  total: {len(pedidos)}")

    if not pedidos.empty:
        print("\n  por status:")
        print(pedidos["status"].value_counts().to_string())

        print("\n  por origem:")
        print(pedidos["origem_venda"].value_counts().to_string())

        df_hoje = _filtrar_por_data(pedidos, "criado_em")
        mostrar_tabela(df_hoje, ["id_pedido", "id_item", "id_mesa", "nome_prod", "quantidade", "status", "origem_venda", "criado_em"])

    separador("PEDIDOS — histórico")
    hist = ler_tabela("historico_pedidos")
    print(f"  total: {len(hist)}")

    if not hist.empty:
        print("\n  por status:")
        print(hist["status"].value_counts().to_string())

        df_hoje = _filtrar_por_data(hist, "criado_em")
        mostrar_tabela(df_hoje, ["id_pedido", "id_item", "id_mesa", "nome_prod", "status", "criado_em"])