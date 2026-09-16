import pandas as pd

from datetime import datetime

from utils.db import ler_tabela, inserir_linha


COLUNAS_MOVIMENTACOES = [
    'id_movimentacao',
    'tipo',
    'id_insumo',
    'quantidade',
    'unidade',
    'data_movimentacao',
    'preco_unitario',
    'fornecedor',
    'nota_fiscal',
    'data_validade',
    'id_pedido',
    'cod_item',
    'cod_prod',
    'motivo',
    'usuario',
    'observacao'
]

MOTIVOS_AJUSTE = [
    'venda_extra',
    'perda',
    'vencimento',
    'consumo_interno',
    'doacao',
    'erro_operacional',
    'outros'
]


def converter_unidade(quantidade, unidade_origem, unidade_destino):
    if unidade_origem == unidade_destino:
        return quantidade

    if unidade_origem == 'g' and unidade_destino == 'kg':
        return quantidade / 1000
    if unidade_origem == 'kg' and unidade_destino == 'g':
        return quantidade * 1000
    if unidade_origem == 'ml' and unidade_destino == 'L':
        return quantidade / 1000
    if unidade_origem == 'L' and unidade_destino == 'ml':
        return quantidade * 1000
    if unidade_origem == 'un' and unidade_destino == 'un':
        return quantidade

    return None


def carregar_movimentacoes():
    df = ler_tabela("movimentacoes")

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_MOVIMENTACOES)

    for coluna in COLUNAS_MOVIMENTACOES:
        if coluna not in df.columns:
            df[coluna] = ''

    return df


def salvar_movimentacoes(df):
    from utils.db import escrever_tabela
    escrever_tabela("movimentacoes", df)


def gerar_id_movimentacao():
    from utils.db import proximo_id_numerico

    proximo = proximo_id_numerico("movimentacoes", "id_movimentacao", "MOV-")
    return f"MOV-{proximo:05d}"


def _inserir(registro):
    inserir_linha("movimentacoes", registro)
    return registro


def registrar_compra(id_insumo, quantidade, unidade, preco_unitario, fornecedor, nota_fiscal='', data_validade='', usuario='', data_movimentacao=None):
    registro = {
        'id_movimentacao': gerar_id_movimentacao(),
        'tipo': 'compra',
        'id_insumo': id_insumo,
        'quantidade': float(quantidade),
        'unidade': unidade,
        'data_movimentacao': data_movimentacao or datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'preco_unitario': float(preco_unitario),
        'fornecedor': fornecedor,
        'nota_fiscal': nota_fiscal,
        'data_validade': data_validade,
        'id_pedido': None,
        'cod_item': None,
        'cod_prod': None,
        'motivo': None,
        'usuario': usuario,
        'observacao': None
    }
    return _inserir(registro)


def registrar_venda(id_insumo, quantidade, unidade, id_pedido, cod_item, cod_prod, usuario='', data_movimentacao=None):
    registro = {
        'id_movimentacao': gerar_id_movimentacao(),
        'tipo': 'venda',
        'id_insumo': id_insumo,
        'quantidade': float(quantidade),
        'unidade': unidade,
        'data_movimentacao': data_movimentacao or datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'preco_unitario': None,
        'fornecedor': None,
        'nota_fiscal': None,
        'data_validade': None,
        'id_pedido': id_pedido,
        'cod_item': cod_item,
        'cod_prod': cod_prod,
        'motivo': None,
        'usuario': usuario,
        'observacao': None
    }
    return _inserir(registro)


def registrar_ajuste(id_insumo, quantidade, unidade, motivo, observacao='', usuario='', data_movimentacao=None):
    if motivo not in MOTIVOS_AJUSTE:
        raise ValueError(f"Motivo inválido: {motivo}. Use um de: {MOTIVOS_AJUSTE}")

    motivos_negativos = ['perda', 'vencimento', 'consumo_interno', 'doacao', 'erro_operacional']

    quantidade = abs(float(quantidade))
    if motivo in motivos_negativos:
        quantidade = -quantidade

    registro = {
        'id_movimentacao': gerar_id_movimentacao(),
        'tipo': 'ajuste',
        'id_insumo': id_insumo,
        'quantidade': quantidade,
        'unidade': unidade,
        'data_movimentacao': data_movimentacao or datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'preco_unitario': None,
        'fornecedor': None,
        'nota_fiscal': None,
        'data_validade': None,
        'id_pedido': None,
        'cod_item': None,
        'cod_prod': None,
        'motivo': motivo,
        'usuario': usuario,
        'observacao': observacao
    }
    return _inserir(registro)


def calcular_estoque_atual():
    df = carregar_movimentacoes()

    if df.empty:
        return pd.DataFrame(columns=['id_insumo', 'estoque'])

    df = df.copy()
    df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)

    df['sinal'] = df['tipo'].map({'compra': 1, 'venda': -1, 'ajuste': 1}).fillna(0)
    df['delta'] = df['quantidade'] * df['sinal']

    resultado = df.groupby('id_insumo')['delta'].sum().reset_index()
    resultado.columns = ['id_insumo', 'estoque']

    return resultado


def custo_medio_por_insumo():
    df = carregar_movimentacoes()

    if df.empty:
        return pd.DataFrame(columns=['id_insumo', 'custo_medio'])

    df = df.copy()
    df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
    df['preco_unitario'] = pd.to_numeric(df['preco_unitario'], errors='coerce')

    compras = df[(df['tipo'] == 'compra') & (df['preco_unitario'].notna())].copy()
    compras['valor'] = compras['quantidade'] * compras['preco_unitario']

    agrupado = compras.groupby('id_insumo').agg(
        qtd_total=('quantidade', 'sum'),
        valor_total=('valor', 'sum')
    ).reset_index()

    agrupado['custo_medio'] = agrupado.apply(
        lambda r: r['valor_total'] / r['qtd_total'] if r['qtd_total'] > 0 else 0.0,
        axis=1
    )

    return agrupado[['id_insumo', 'custo_medio']]


def baixar_por_produto(id_pedido, cod_item, cod_prod, quantidade, nome_prod='', usuario='', data_movimentacao=None):
    produtos = ler_tabela("produtos")
    fichas = ler_tabela("ficha_tecnica")
    insumos = ler_tabela("insumos")

    if produtos.empty:
        return False, "Produtos não carregados", []

    produto_df = produtos[produtos['cod_prod'].astype(str) == str(cod_prod)]

    if produto_df.empty:
        return False, f"Produto {cod_prod} não encontrado", []

    produto = produto_df.iloc[0].to_dict()
    insumo_direto = str(produto.get('insumo_direto', '') or '').strip()

    ficha = None
    if not fichas.empty and 'cod_prod' in fichas.columns:
        ficha_df = fichas[fichas['cod_prod'].astype(str) == str(cod_prod)]
        if not ficha_df.empty:
            ficha = ficha_df

    if insumos.empty:
        return False, "Insumos não carregados", []

    insumos_index = insumos.set_index('id_insumo')

    movimentacoes_geradas = []

    if ficha is not None:
        for _, linha in ficha.iterrows():
            id_insumo = linha['id_insumo']

            if id_insumo not in insumos_index.index:
                continue

            insumo = insumos_index.loc[id_insumo]
            unidade_compra = insumo['unidade_compra']

            qtd_ficha = float(linha['quantidade'])
            unidade_ficha = linha['unidade_ficha']

            qtd_total = qtd_ficha * quantidade
            qtd_convertida = converter_unidade(qtd_total, unidade_ficha, unidade_compra)

            if qtd_convertida is None:
                continue

            registrar_venda(
                id_insumo=id_insumo,
                quantidade=qtd_convertida,
                unidade=unidade_compra,
                id_pedido=id_pedido,
                cod_item=cod_item,
                cod_prod=cod_prod,
                usuario=usuario,
                data_movimentacao=data_movimentacao
            )
            movimentacoes_geradas.append({
                'id_insumo': id_insumo,
                'quantidade': qtd_convertida,
                'unidade': unidade_compra
            })

        return True, f"{len(movimentacoes_geradas)} insumo(s) baixado(s)", movimentacoes_geradas

    if insumo_direto:
        if insumo_direto not in insumos_index.index:
            return False, f"Insumo {insumo_direto} não encontrado", []

        insumo = insumos_index.loc[insumo_direto]
        unidade_compra = insumo['unidade_compra']

        registrar_venda(
            id_insumo=insumo_direto,
            quantidade=quantidade,
            unidade=unidade_compra,
            id_pedido=id_pedido,
            cod_item=cod_item,
            cod_prod=cod_prod,
            usuario=usuario,
            data_movimentacao=data_movimentacao
        )

        return True, "1 insumo baixado (direto)", [{
            'id_insumo': insumo_direto,
            'quantidade': quantidade,
            'unidade': unidade_compra
        }]

    return False, f"Produto {cod_prod} sem ficha nem insumo direto", []