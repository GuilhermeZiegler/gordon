from test._common import separador, mostrar_tabela, _filtrar_por_data
from utils.db import ler_tabela


def run():
    separador("DELIVERY")

    df = ler_tabela("delivery")
    print(f"  total: {len(df)}")

    if df.empty:
        return

    print("\n  por status:")
    print(df["status_entrega"].value_counts().to_string())

    separador("DELIVERY — criados hoje")
    df_hoje = _filtrar_por_data(df, "criado_em")
    mostrar_tabela(df_hoje, ["id_pedido", "id_cliente", "nome_cliente", "status_entrega", "motoboy", "criado_em"])