import os
import pickle
import pandas as pd

from install.seed._common import DATA_DIR, _c
from install.seed.insumos import INSUMOS
from install.seed.produtos import PRODUTOS
from install.seed.fichas import FICHAS
from install.seed.funcionarios import FUNCIONARIOS
from install.seed.clientes import CLIENTES


def _get_custo_insumo(id_insumo, quantidade, unidade_ficha, df_insumos):
    insumo = df_insumos[df_insumos['id_insumo'] == id_insumo]
    if insumo.empty:
        return 0.0
    preco = float(insumo.iloc[0]['preco_unitario'])
    unidade_compra = insumo.iloc[0]['unidade_compra']
    if unidade_ficha == 'g' and unidade_compra == 'kg':
        q = quantidade / 1000.0
    elif unidade_ficha == 'ml' and unidade_compra == 'L':
        q = quantidade / 1000.0
    else:
        q = quantidade
    return q * preco


def popular_dados():
    with open(_c["insumos"], 'wb') as f:
        pickle.dump(pd.DataFrame(INSUMOS), f)

    with open(_c["produtos"], 'wb') as f:
        pickle.dump(pd.DataFrame(PRODUTOS), f)

    fichas = []
    for cod_prod, itens in FICHAS.items():
        for id_insumo, qtd, unidade in itens:
            fichas.append({
                'cod_prod': cod_prod,
                'id_insumo': id_insumo,
                'quantidade': qtd,
                'unidade_ficha': unidade
            })
    with open(_c["ficha"], 'wb') as f:
        pickle.dump(pd.DataFrame(fichas), f)

    with open(os.path.join(DATA_DIR, "funcionarios.pkl"), 'wb') as f:
        pickle.dump(FUNCIONARIOS, f)

    with open(os.path.join(DATA_DIR, "clientes.pkl"), 'wb') as f:
        pickle.dump(CLIENTES, f)

    with open(_c["produtos"], 'rb') as f:
        df_produtos = pickle.load(f)
        df_produtos['p_custo'] = df_produtos['p_custo'].astype(float)
        df_produtos['margem'] = df_produtos['margem'].astype(float)
    with open(_c["ficha"], 'rb') as f:
        df_ficha = pickle.load(f)
    with open(_c["insumos"], 'rb') as f:
        df_insumos = pickle.load(f)

    for idx, row in df_produtos.iterrows():
        itens_ficha = df_ficha[df_ficha['cod_prod'] == str(row['cod_prod'])]
        if itens_ficha.empty:
            df_produtos.loc[idx, 'p_custo'] = 0.0
            df_produtos.loc[idx, 'margem'] = 0
            continue
        custo_total = sum(
            _get_custo_insumo(item['id_insumo'], float(item['quantidade']), item['unidade_ficha'], df_insumos)
            for _, item in itens_ficha.iterrows()
        )
        df_produtos.loc[idx, 'p_custo'] = round(custo_total, 2)
        p_venda = float(row['p_venda'])
        df_produtos.loc[idx, 'margem'] = round((p_venda - custo_total) / custo_total, 2) if custo_total > 0 else 0

    with open(_c["produtos"], 'wb') as f:
        pickle.dump(df_produtos, f)

    print("Dados populados.")


if __name__ == "__main__":
    popular_dados()