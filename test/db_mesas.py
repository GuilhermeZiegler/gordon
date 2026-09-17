from test._common import separador, mostrar_tabela, _filtrar_por_data
from utils.db import ler_tabela


def run():
    separador("MESAS — ativas")
    mesas = ler_tabela("mesas")
    print(f"  total: {len(mesas)}")
    mostrar_tabela(mesas, ["id_mesa", "status", "garcom", "qtd_clientes", "aberto_em", "fechado_em", "valor_total", "id_venda_caixa"])

    separador("MESAS — histórico (hoje)")
    hist = ler_tabela("historico_mesas")
    print(f"  total geral: {len(hist)}")

    df_hoje = _filtrar_por_data(hist, "fechado_em")
    mostrar_tabela(df_hoje, ["id_mesa", "garcom", "qtd_clientes", "aberto_em", "fechado_em", "valor_total", "valor_10", "cover"])