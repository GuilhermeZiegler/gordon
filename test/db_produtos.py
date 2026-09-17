from test._common import separador, mostrar_tabela
from utils.db import ler_tabela


def run():
    separador("PRODUTOS")
    produtos = ler_tabela("produtos")
    print(f"  total: {len(produtos)}")
    mostrar_tabela(produtos, ["cod_prod", "nome", "descricao", "tipo_venda", "p_venda", "p_custo", "margem"])

    separador("INSUMOS")
    insumos = ler_tabela("insumos")
    print(f"  total: {len(insumos)}")

    separador("FICHA TÉCNICA")
    ficha = ler_tabela("ficha_tecnica")
    print(f"  total: {len(ficha)}")

    if not ficha.empty:
        print("\n  por produto (top 10 com mais insumos):")
        contagem = ficha.groupby("cod_prod").size().sort_values(ascending=False).head(10)
        print(contagem.to_string())

    separador("PRODUTOS — sem ficha técnica")
    if not produtos.empty and not ficha.empty:
        produtos_com_ficha = set(ficha["cod_prod"].astype(str).unique())
        produtos_menu = produtos[produtos["tipo_venda"].isin(["menu", "bar"])]
        sem_ficha = produtos_menu[~produtos_menu["cod_prod"].astype(str).isin(produtos_com_ficha)]
        mostrar_tabela(sem_ficha, ["cod_prod", "nome", "tipo_venda"])