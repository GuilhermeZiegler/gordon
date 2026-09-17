import json
import pandas as pd
import streamlit as st

from datetime import datetime

from utils.db import ler_tabela, escrever_tabela, inserir_linha, executar


COLUNAS_ESTOQUE = [
    'id_insumo', 'nome_insumo', 'unidade',
    'estoque', 'inventario', 'diferenca',
    'a_vencer_7d', 'a_vencer_30d',
    'ultima_compra', 'ultimo_inventario'
]

COLUNAS_COMPRAS = [
    'id_compra', 'id_insumo', 'data_compra', 'data_validade',
    'quantidade', 'unidade', 'preco_unitario', 'valor_total',
    'fornecedor', 'nota_fiscal'
]

COLUNAS_ESTOQUE_BAIXAS = [
    'id_baixa', 'id_pedido', 'cod_item', 'cod_prod',
    'id_insumo', 'quantidade', 'unidade', 'data_baixa', 'observacao'
]

COLUNAS_ESTOQUE_INVENTARIO = [
    'id_inventario', 'id_insumo', 'data_inventario',
    'quantidade_real', 'quantidade_virtual', 'diferenca',
    'observacao', 'usuario'
]


def _carregar_jsonb(nome_tabela):
    df = ler_tabela(nome_tabela)

    if df.empty or "dados" not in df.columns:
        return []

    valor = df["dados"].iloc[0]

    if valor is None:
        return []

    if isinstance(valor, list):
        return valor

    if isinstance(valor, str):
        try:
            return json.loads(valor)
        except Exception:
            return []

    return []


def _salvar_jsonb(nome_tabela, dados):
    payload = json.dumps(dados, ensure_ascii=False, default=str)

    executar(f'TRUNCATE TABLE "{nome_tabela}"')
    executar(
        f'INSERT INTO "{nome_tabela}" (dados) VALUES (CAST(:d AS jsonb))',
        {"d": payload}
    )


def carregar_df(nome_tabela, colunas=None):
    df = ler_tabela(nome_tabela)

    if df.empty:
        if colunas:
            return pd.DataFrame(columns=colunas)
        return pd.DataFrame()

    if colunas:
        for col in colunas:
            if col not in df.columns:
                df[col] = ''

        for col in colunas:
            if col in df.columns and col not in ['quantidade', 'preco_unitario', 'valor_total', 'estoque', 'inventario', 'diferenca', 'a_vencer_7d', 'a_vencer_30d']:
                df[col] = df[col].astype(str)

    return df


def salvar_df(df, nome_tabela):
    try:
        escrever_tabela(nome_tabela, df)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False


def gerar_id_compra():
    from utils.db import proximo_id_numerico

    proximo = proximo_id_numerico("compras", "id_compra", "CMP-")
    return f"CMP-{proximo:03d}"


def gerar_id_baixa():
    from utils.db import proximo_id_numerico

    proximo = proximo_id_numerico("estoque_baixas", "id_baixa", "BAIXA-")
    return f"BAIXA-{proximo:03d}"


def gerar_id_inventario():
    from utils.db import proximo_id_numerico

    proximo = proximo_id_numerico("estoque_inventario", "id_inventario", "INV-")
    return f"INV-{proximo:03d}"


def calcular_a_vencer(id_insumo):
    df_compras = carregar_df("compras", COLUNAS_COMPRAS)
    if df_compras.empty:
        return 0.0, 0.0

    hoje = datetime.now().date()
    compras_insumo = df_compras[df_compras['id_insumo'] == id_insumo]
    if compras_insumo.empty:
        return 0.0, 0.0

    a_vencer_7d = 0.0
    a_vencer_30d = 0.0

    for _, row in compras_insumo.iterrows():
        if pd.notna(row['data_validade']) and row['data_validade']:
            try:
                data_validade = pd.to_datetime(row['data_validade']).date()
                dias_para_vencer = (data_validade - hoje).days

                if 0 <= dias_para_vencer <= 7:
                    a_vencer_7d += float(row['quantidade'])
                if 0 <= dias_para_vencer <= 30:
                    a_vencer_30d += float(row['quantidade'])
            except Exception:
                pass

    return a_vencer_7d, a_vencer_30d


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


def _snapshot_estoque():
    df_estoque = carregar_df("estoque", COLUNAS_ESTOQUE)
    if df_estoque.empty:
        return

    historico = _carregar_jsonb("historico_estoque")

    historico.append({
        'data': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'estoque': df_estoque.to_dict('records')
    })

    _salvar_jsonb("historico_estoque", historico)


def _registrar_historico_baixa(id_pedido, cod_item, cod_prod, insumos):
    historico = _carregar_jsonb("historico_baixas")

    for insumo in insumos:
        historico.append({
            'id_baixa': gerar_id_baixa(),
            'id_pedido': id_pedido,
            'cod_item': cod_item,
            'cod_prod': cod_prod,
            'id_insumo': insumo['id_insumo'],
            'quantidade': insumo['quantidade'],
            'unidade': insumo['unidade'],
            'data_baixa': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'observacao': 'Baixa automática'
        })

    _salvar_jsonb("historico_baixas", historico)


def _registrar_nao_baixado(id_pedido, cod_item, cod_prod, nome_prod, quantidade, motivo):
    historico = _carregar_jsonb("historico_nao_baixados")

    historico.append({
        'id_pedido': id_pedido,
        'cod_item': cod_item,
        'cod_prod': cod_prod,
        'nome_prod': nome_prod,
        'quantidade': quantidade,
        'motivo': motivo,
        'data_processamento': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })

    _salvar_jsonb("historico_nao_baixados", historico)


def baixar_estoque_por_item(id_pedido, cod_item, cod_prod, quantidade_item, nome_prod=''):
    df_produtos = carregar_df("produtos")

    if df_produtos.empty:
        _registrar_nao_baixado(id_pedido, cod_item, cod_prod, nome_prod, quantidade_item, "Nenhum produto cadastrado")
        return False, "Nenhum produto cadastrado", []

    produto = df_produtos[df_produtos['cod_prod'] == str(cod_prod)]

    if produto.empty:
        _registrar_nao_baixado(id_pedido, cod_item, cod_prod, nome_prod, quantidade_item, f"Produto {cod_prod} não encontrado")
        return False, f"Produto {cod_prod} não encontrado", []

    produto = produto.iloc[0]
    marcador_cozinha = produto.get('marcador_cozinha', False)
    insumo_direto = produto.get('insumo_direto', '')

    if marcador_cozinha:
        df_ficha = carregar_df("ficha_tecnica")
        if df_ficha.empty:
            _registrar_nao_baixado(id_pedido, cod_item, cod_prod, nome_prod, quantidade_item, "Ficha técnica vazia")
            return False, "Ficha técnica vazia", []

        ficha_produto = df_ficha[df_ficha['cod_prod'] == str(cod_prod)]
        if ficha_produto.empty:
            _registrar_nao_baixado(id_pedido, cod_item, cod_prod, nome_prod, quantidade_item, f"Produto {cod_prod} sem ficha técnica")
            return False, f"Produto {cod_prod} não tem ficha técnica", []

        df_insumos = carregar_df("insumos")
        if df_insumos.empty:
            _registrar_nao_baixado(id_pedido, cod_item, cod_prod, nome_prod, quantidade_item, "Nenhum insumo cadastrado")
            return False, "Nenhum insumo cadastrado", []

        df_estoque = carregar_df("estoque", COLUNAS_ESTOQUE)
        df_baixas = carregar_df("estoque_baixas", COLUNAS_ESTOQUE_BAIXAS)

        insumos_baixados = []
        erros = []

        for _, ficha_row in ficha_produto.iterrows():
            id_insumo = ficha_row['id_insumo']
            quantidade_ficha = float(ficha_row['quantidade'])
            unidade_ficha = ficha_row['unidade_ficha']

            insumo_data = df_insumos[df_insumos['id_insumo'] == id_insumo]
            if insumo_data.empty:
                erros.append(f"Insumo {id_insumo} não encontrado")
                continue

            unidade_compra = insumo_data.iloc[0]['unidade_compra']

            quantidade_total = quantidade_ficha * quantidade_item

            quantidade_convertida = converter_unidade(
                quantidade_total,
                unidade_ficha,
                unidade_compra
            )

            if quantidade_convertida is None:
                erros.append(f"Conversão inválida: {unidade_ficha} → {unidade_compra}")
                continue

            idx_estoque = df_estoque[df_estoque['id_insumo'] == id_insumo].index
            if not idx_estoque.empty:
                df_estoque.loc[idx_estoque[0], 'estoque'] -= quantidade_convertida
            else:
                erros.append(f"Insumo {id_insumo} não está no estoque")
                continue

            id_baixa = gerar_id_baixa()
            nova_baixa = pd.DataFrame([{
                'id_baixa': id_baixa,
                'id_pedido': id_pedido,
                'cod_item': cod_item,
                'cod_prod': cod_prod,
                'id_insumo': id_insumo,
                'quantidade': quantidade_convertida,
                'unidade': unidade_compra,
                'data_baixa': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'observacao': f"Qtd original: {quantidade_total}{unidade_ficha}"
            }])
            df_baixas = pd.concat([df_baixas, nova_baixa], ignore_index=True)

            insumos_baixados.append({
                'id_insumo': id_insumo,
                'quantidade': quantidade_convertida,
                'unidade': unidade_compra
            })

        if not salvar_df(df_estoque, "estoque"):
            return False, "Erro ao salvar estoque", insumos_baixados
        if not salvar_df(df_baixas, "estoque_baixas"):
            return False, "Erro ao salvar baixas", insumos_baixados

        if insumos_baixados:
            _snapshot_estoque()
            _registrar_historico_baixa(id_pedido, cod_item, cod_prod, insumos_baixados)

        mensagem = f"{len(insumos_baixados)} insumos baixados"
        if erros:
            mensagem += f" | Erros: {', '.join(erros)}"

        return True, mensagem, insumos_baixados

    elif insumo_direto:
        df_estoque = carregar_df("estoque", COLUNAS_ESTOQUE)
        df_baixas = carregar_df("estoque_baixas", COLUNAS_ESTOQUE_BAIXAS)

        df_insumos = carregar_df("insumos")
        if df_insumos.empty:
            _registrar_nao_baixado(id_pedido, cod_item, cod_prod, nome_prod, quantidade_item, "Nenhum insumo cadastrado")
            return False, "Nenhum insumo cadastrado", []

        insumo_info = df_insumos[df_insumos['id_insumo'] == insumo_direto]
        if insumo_info.empty:
            _registrar_nao_baixado(id_pedido, cod_item, cod_prod, nome_prod, quantidade_item, f"Insumo {insumo_direto} não encontrado")
            return False, f"Insumo {insumo_direto} não encontrado", []

        insumo_info = insumo_info.iloc[0]
        unidade_compra = insumo_info['unidade_compra']

        idx_estoque = df_estoque[df_estoque['id_insumo'] == insumo_direto].index
        if not idx_estoque.empty:
            df_estoque.loc[idx_estoque[0], 'estoque'] -= quantidade_item
        else:
            _registrar_nao_baixado(id_pedido, cod_item, cod_prod, nome_prod, quantidade_item, f"Insumo {insumo_direto} não está no estoque")
            return False, f"Insumo {insumo_direto} não está no estoque", []

        id_baixa = gerar_id_baixa()
        nova_baixa = pd.DataFrame([{
            'id_baixa': id_baixa,
            'id_pedido': id_pedido,
            'cod_item': cod_item,
            'cod_prod': cod_prod,
            'id_insumo': insumo_direto,
            'quantidade': quantidade_item,
            'unidade': unidade_compra,
            'data_baixa': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'observacao': 'Baixa direta'
        }])
        df_baixas = pd.concat([df_baixas, nova_baixa], ignore_index=True)

        if not salvar_df(df_estoque, "estoque"):
            return False, "Erro ao salvar estoque", []
        if not salvar_df(df_baixas, "estoque_baixas"):
            return False, "Erro ao salvar baixas", []

        insumos_baixados = [{
            'id_insumo': insumo_direto,
            'quantidade': quantidade_item,
            'unidade': unidade_compra
        }]

        _snapshot_estoque()
        _registrar_historico_baixa(id_pedido, cod_item, cod_prod, insumos_baixados)

        return True, "1 insumo baixado (direto)", insumos_baixados

    else:
        _registrar_nao_baixado(id_pedido, cod_item, cod_prod, nome_prod, quantidade_item, f"Produto {cod_prod} sem ficha técnica nem insumo direto")
        return False, f"Produto {cod_prod} não tem ficha técnica nem insumo direto", []


def calcular_estoque():
    df_compras = st.session_state.compras
    df_baixas = st.session_state.estoque_baixas
    df_estoque = st.session_state.estoque

    if df_estoque.empty:
        return

    df_estoque['estoque'] = 0.0

    if not df_compras.empty:
        compras_por_insumo = df_compras.groupby('id_insumo')['quantidade'].sum().reset_index()
        compras_por_insumo.columns = ['id_insumo', 'total_compras']

        for _, row in compras_por_insumo.iterrows():
            idx = df_estoque[df_estoque['id_insumo'] == row['id_insumo']].index
            if not idx.empty:
                df_estoque.loc[idx[0], 'estoque'] += float(row['total_compras'])

    if not df_baixas.empty:
        baixas_por_insumo = df_baixas.groupby('id_insumo')['quantidade'].sum().reset_index()
        baixas_por_insumo.columns = ['id_insumo', 'total_baixas']

        for _, row in baixas_por_insumo.iterrows():
            idx = df_estoque[df_estoque['id_insumo'] == row['id_insumo']].index
            if not idx.empty:
                df_estoque.loc[idx[0], 'estoque'] -= float(row['total_baixas'])

    st.session_state.estoque = df_estoque
    salvar_df(df_estoque, "estoque")


def registrar_inventario(id_insumo, quantidade_real, observacao=""):
    df_estoque = st.session_state.estoque
    df_inventario = st.session_state.estoque_inventario

    idx = df_estoque[df_estoque['id_insumo'] == id_insumo].index
    if idx.empty:
        return False, "Insumo não encontrado"

    quantidade_virtual = float(df_estoque.loc[idx[0], 'estoque'])
    diferenca = quantidade_virtual - quantidade_real

    id_inventario = gerar_id_inventario()
    novo_registro = pd.DataFrame([{
        'id_inventario': id_inventario,
        'id_insumo': id_insumo,
        'data_inventario': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'quantidade_real': quantidade_real,
        'quantidade_virtual': quantidade_virtual,
        'diferenca': diferenca,
        'observacao': observacao,
        'usuario': st.session_state.get('usuario', 'Sistema')
    }])

    st.session_state.estoque_inventario = pd.concat(
        [st.session_state.estoque_inventario, novo_registro],
        ignore_index=True
    )

    df_estoque.loc[idx[0], 'inventario'] = quantidade_real
    df_estoque.loc[idx[0], 'diferenca'] = diferenca
    df_estoque.loc[idx[0], 'ultimo_inventario'] = datetime.now().strftime("%d/%m/%Y %H:%M")

    st.session_state.estoque = df_estoque

    salvar_df(df_estoque, "estoque")
    salvar_df(st.session_state.estoque_inventario, "estoque_inventario")

    _snapshot_estoque()

    if diferenca > 0:
        mensagem = f"Divergência: +{diferenca:.1f} (estoque > inventário)"
    elif diferenca < 0:
        mensagem = f"Divergência: {diferenca:.1f} (estoque < inventário)"
    else:
        mensagem = "Sem divergência"

    return True, mensagem


def restaurar_estoque_do_historico():
    historico_estoque = _carregar_jsonb("historico_estoque")

    if not historico_estoque:
        return False, "Histórico de estoque vazio"

    ultimo = historico_estoque[-1]

    if isinstance(ultimo.get('estoque'), list):
        df_restaurado = pd.DataFrame(ultimo['estoque'])
    else:
        ultima_data = ultimo.get('data', '')
        registros = [item for item in historico_estoque if item.get('data') == ultima_data]
        df_restaurado = pd.DataFrame(registros) if registros else pd.DataFrame()

    if df_restaurado.empty:
        return False, "Nenhum dado válido no snapshot"

    for col in COLUNAS_ESTOQUE:
        if col not in df_restaurado.columns:
            df_restaurado[col] = 0.0 if col in ['estoque', 'inventario', 'diferenca', 'a_vencer_7d', 'a_vencer_30d'] else ''

    salvar_df(df_restaurado, "estoque")
    return True, f"Estoque restaurado do snapshot de {ultimo.get('data', 'N/A')} com {len(df_restaurado)} insumos"


def carregar_pkl(caminho=None):
    if not caminho:
        return None

    base = str(caminho).replace("\\", "/").split("/")[-1].replace(".pkl", "")

    if base in ["estoque", "compras", "estoque_baixas", "estoque_inventario", "produtos", "insumos", "ficha_tecnica"]:
        try:
            return ler_tabela(base)
        except Exception:
            return None

    return None