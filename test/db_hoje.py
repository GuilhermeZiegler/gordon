from test._common import separador, _filtrar_por_data, mostrar_tabela, carregar_jsonb


def run():
    separador("HOJE — pedidos ativos")

    from utils.db import ler_tabela
    pedidos = ler_tabela("pedidos")
    df = _filtrar_por_data(pedidos, "criado_em")
    mostrar_tabela(df, ["id_pedido", "id_item", "id_mesa", "nome_prod", "status", "criado_em"])

    separador("HOJE — histórico de pedidos")
    hist = ler_tabela("historico_pedidos")
    df_h = _filtrar_por_data(hist, "criado_em")
    mostrar_tabela(df_h, ["id_pedido", "id_item", "id_mesa", "nome_prod", "status", "criado_em", "fechado_em"])

    separador("HOJE — mesas ativas")
    mesas = ler_tabela("mesas")
    mostrar_tabela(mesas, ["id_mesa", "status", "garcom", "qtd_clientes", "aberto_em", "fechado_em", "valor_total"])

    separador("HOJE — histórico de mesas")
    hist_m = ler_tabela("historico_mesas")
    df_hm = _filtrar_por_data(hist_m, "fechado_em")
    mostrar_tabela(df_hm, ["id_mesa", "garcom", "aberto_em", "fechado_em", "valor_total"])

    separador("HOJE — movimentações de estoque")
    mov = ler_tabela("movimentacoes")
    df_mov = _filtrar_por_data(mov, "data_movimentacao")
    mostrar_tabela(df_mov, ["id_movimentacao", "tipo", "id_insumo", "quantidade", "data_movimentacao"])

    separador("HOJE — delivery")
    deliv = ler_tabela("delivery")
    df_d = _filtrar_por_data(deliv, "criado_em")
    mostrar_tabela(df_d, ["id_pedido", "id_cliente", "nome_cliente", "status_entrega", "criado_em"])

    separador("HOJE — caixa (JSONB atual)")
    caixa = carregar_jsonb("caixa")
    if caixa:
        print(f"  status: {caixa.get('status')}")
        print(f"  data_abertura: {caixa.get('data_abertura')}")
        print(f"  saldo_inicial: R$ {caixa.get('saldo_inicial', 0):.2f}")
        print(f"  entradas: {len(caixa.get('entradas', []))}")
        print(f"  estornos: {len(caixa.get('estornos', []))}")
        print(f"  fiados: {len(caixa.get('fiados', []))}")
    else:
        print("  (caixa vazio)")