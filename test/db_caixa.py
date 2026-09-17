from test._common import separador, mostrar_tabela, carregar_jsonb


def run():
    separador("CAIXA — estado atual")

    caixa = carregar_jsonb("caixa")

    if not caixa:
        print("  (caixa vazio)")
        return

    print(f"  status: {caixa.get('status')}")
    print(f"  data_abertura: {caixa.get('data_abertura')}")
    print(f"  data_fechamento: {caixa.get('data_fechamento')}")
    print(f"  saldo_inicial: R$ {caixa.get('saldo_inicial', 0):.2f}")
    print(f"  vendas_mesa: R$ {caixa.get('vendas_mesa', 0):.2f}")
    print(f"  vendas_balcao: R$ {caixa.get('vendas_balcao', 0):.2f}")
    print(f"  vendas_takeaway: R$ {caixa.get('vendas_takeaway', 0):.2f}")
    print(f"  vendas_delivery: R$ {caixa.get('vendas_delivery', 0):.2f}")

    separador("CAIXA — entradas")
    entradas = caixa.get("entradas", [])
    if entradas:
        import pandas as pd
        df = pd.DataFrame(entradas)
        mostrar_tabela(df, ["id_venda", "categoria", "valor", "metodo", "descricao", "data"])
    else:
        print("  (nenhuma)")

    separador("CAIXA — estornos")
    estornos = caixa.get("estornos", [])
    if estornos:
        import pandas as pd
        df = pd.DataFrame(estornos)
        mostrar_tabela(df, ["id_estorno", "id_venda_original", "valor_estornado", "tipo", "metodo", "classificacao", "data"])
    else:
        print("  (nenhum)")

    separador("CAIXA — fiados")
    fiados = caixa.get("fiados", [])
    if fiados:
        import pandas as pd
        df = pd.DataFrame(fiados)
        mostrar_tabela(df, ["id", "cliente", "valor", "status", "data"])
    else:
        print("  (nenhum)")

    separador("HISTÓRICO CAIXA — últimos 5 dias")
    hist = carregar_jsonb("historico_caixa")

    if not hist or not isinstance(hist, list):
        print("  (vazio)")
        return

    for cx in hist[-5:]:
        print(f"\n  {cx.get('data_abertura')} — status {cx.get('status')}")
        print(f"    entradas: {len(cx.get('entradas', []))}, estornos: {len(cx.get('estornos', []))}, fiados: {len(cx.get('fiados', []))}")