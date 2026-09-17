import streamlit as st
import pandas as pd
from datetime import datetime
import time

from components.card_produto import card_produto
from components.card_ficha_tecnica import renderizar_card_ficha

from components.auth import exigir_permissao
exigir_permissao("produtos")

from utils.db import ler_tabela_df, escrever_tabela_df, invalidar_cache
from utils.produtos_utils import calcular_custo_insumo


COLUNAS = [
    'cod_prod', 'nome', 'descricao', 'tipo', 'categoria',
    'p_venda', 'p_custo', 'margem', 'tipo_venda',
    'insumo_direto', 'marcador_cozinha'
]
COLUNAS_INSUMOS = ['id_insumo', 'nome', 'categoria_insumo', 'unidade_compra', 'preco_unitario']
COLUNAS_FICHA = ['cod_prod', 'id_insumo', 'quantidade', 'unidade_ficha']

UNIDADES = ['g', 'kg', 'ml', 'L', 'un', 'cx', 'pct']


st.session_state.produtos = ler_tabela_df("produtos", COLUNAS)
if st.session_state.produtos.empty:
    st.session_state.produtos = pd.DataFrame(columns=COLUNAS)

if 'insumos' not in st.session_state:
    st.session_state.insumos = ler_tabela_df("insumos", COLUNAS_INSUMOS)
    if st.session_state.insumos.empty:
        st.session_state.insumos = pd.DataFrame(columns=COLUNAS_INSUMOS)

if 'ficha_tecnica' not in st.session_state:
    st.session_state.ficha_tecnica = ler_tabela_df("ficha_tecnica", COLUNAS_FICHA)
    if st.session_state.ficha_tecnica.empty:
        st.session_state.ficha_tecnica = pd.DataFrame(columns=COLUNAS_FICHA)

if 'form_data' not in st.session_state:
    st.session_state.form_data = {
        'cod_prod': '',
        'nome': '',
        'descricao': '',
        'tipo': '',
        'categoria': '',
        'p_venda': 0.0,
        'p_custo': 0.01,
        'tipo_venda': 'menu',
        'insumo_direto': ''
    }

st.header("Produtos")

aba1, aba2, aba3, aba4 = st.tabs(["Cadastrar", "Menu", "Ficha Técnica", 'Insumos'])


with aba1:
    def gerar_codigo_produto():
        df = st.session_state.produtos
        if df.empty:
            return "1"
        codigos_numericos = []
        for cod in df['cod_prod']:
            try:
                codigos_numericos.append(int(cod))
            except (ValueError, TypeError):
                pass
        if not codigos_numericos:
            return "1"
        return str(max(codigos_numericos) + 1)

    col_busca, col_botao, col_novo = st.columns([3, 1, 1])
    with col_busca:
        busca = st.text_input(
            "Buscar por Código ou Nome",
            placeholder="Digite o código ou nome do produto",
            key="busca_input"
        )
    with col_botao:
        st.write("")
        st.write("")
        if st.button("🔍 Buscar", use_container_width=True):
            if busca:
                df = st.session_state.produtos
                if not df.empty:
                    df['cod_prod'] = df['cod_prod'].astype(str)
                    df['nome'] = df['nome'].astype(str)

                    if busca.isdigit():
                        produto = df[df['cod_prod'] == busca]
                    else:
                        produto = df[df['nome'].str.contains(busca, case=False, na=False)]

                    if not produto.empty:
                        row = produto.iloc[0]
                        st.session_state.form_data = {
                            'cod_prod': str(row['cod_prod']),
                            'nome': str(row['nome']),
                            'descricao': str(row['descricao']) if pd.notna(row.get('descricao')) else '',
                            'tipo': str(row['tipo']) if pd.notna(row.get('tipo')) else '',
                            'categoria': str(row['categoria']) if pd.notna(row.get('categoria')) else '',
                            'p_venda': float(row['p_venda']) if pd.notna(row.get('p_venda')) else 0.0,
                            'p_custo': float(row['p_custo']) if pd.notna(row.get('p_custo')) else 0.01,
                            'tipo_venda': str(row['tipo_venda']) if pd.notna(row.get('tipo_venda')) else 'menu',
                            'insumo_direto': str(row['insumo_direto']) if pd.notna(row.get('insumo_direto')) else ''
                        }
                        st.session_state.editando = True
                        st.success(f"Produto encontrado: {row['nome']}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Produto não encontrado")
    with col_novo:
        st.write("")
        st.write("")
        if st.button("➕ Novo Produto", use_container_width=True):
            st.session_state.editando = False
            for key in st.session_state.form_data:
                if key in ['cod_prod', 'nome', 'descricao', 'tipo', 'categoria']:
                    st.session_state.form_data[key] = ''
                elif key == 'p_venda':
                    st.session_state.form_data[key] = 0.0
                elif key == 'p_custo':
                    st.session_state.form_data[key] = 0.01
                elif key == 'tipo_venda':
                    st.session_state.form_data[key] = 'menu'
                elif key == 'insumo_direto':
                    st.session_state.form_data[key] = ''
            st.rerun()

    with st.form("form_produto"):
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.get('editando', False):
                cod_prod = st.text_input("Código do Produto", value=st.session_state.form_data['cod_prod'])
            else:
                cod_auto = gerar_codigo_produto()
                cod_prod = st.text_input("Código do Produto", value=cod_auto)

            nome = st.text_input("Nome", value=st.session_state.form_data['nome'])
            descricao = st.text_area("Descrição", value=st.session_state.form_data['descricao'])
        with col2:
            tipo = st.text_input("Tipo", value=st.session_state.form_data['tipo'])
            categoria = st.text_input("Categoria", value=st.session_state.form_data['categoria'])
            p_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, step=0.01, value=st.session_state.form_data['p_venda'])
            p_custo = st.number_input("Preço de Custo (R$)", min_value=0.01, step=0.01, value=st.session_state.form_data['p_custo'])
            tipo_venda = st.selectbox(
                "Tipo de Venda:",
                ["menu", "bar", "caixa"],
                index=["menu", "bar", "caixa"].index(st.session_state.form_data['tipo_venda']) if st.session_state.form_data['tipo_venda'] in ["menu", "bar", "caixa"] else 0
            )

            if tipo_venda == 'caixa':
                if not st.session_state.insumos.empty:
                    opcoes_insumos = st.session_state.insumos['id_insumo'] + " - " + st.session_state.insumos['nome']
                    insumo_direto_selecionado = st.selectbox(
                        "Insumo Direto (baixa automática):",
                        [""] + opcoes_insumos.tolist(),
                        index=0 if st.session_state.form_data['insumo_direto'] == '' else (opcoes_insumos.tolist().index(st.session_state.form_data['insumo_direto'] + " - " + st.session_state.insumos[st.session_state.insumos['id_insumo'] == st.session_state.form_data['insumo_direto']]['nome'].iloc[0]) + 1 if st.session_state.form_data['insumo_direto'] != '' else 0)
                    )
                    insumo_direto = insumo_direto_selecionado.split(" - ")[0] if insumo_direto_selecionado else ''
                else:
                    insumo_direto = ''
                    st.warning("⚠️ Nenhum insumo cadastrado para baixa direta.")
            else:
                insumo_direto = ''

        col3, col4, col5 = st.columns([1, 1, 1])
        with col3:
            submitted = st.form_submit_button("Salvar", use_container_width=True)
        with col4:
            deletar = st.form_submit_button("Deletar", use_container_width=True)
        with col5:
            limpar = st.form_submit_button("Limpar", use_container_width=True)

        if submitted:
            erros = []
            if not cod_prod:
                erros.append("Código")
            if not nome:
                erros.append("Nome")
            if not descricao:
                erros.append("Descrição")
            if not tipo:
                erros.append("Tipo")
            if not categoria:
                erros.append("Categoria")
            if p_venda <= 0:
                erros.append("Preço de Venda > 0")
            if p_custo <= 0:
                erros.append("Preço de Custo > 0")
            if cod_prod and not cod_prod.isdigit():
                erros.append("Código deve ser um número (ex: 1, 2, 3...)")

            if not erros:
                margem = round((p_venda / p_custo) - 1, 2) if p_custo > 0 else 0

                df = st.session_state.produtos
                cod_prod_str = str(cod_prod)

                if cod_prod_str in df['cod_prod'].astype(str).values:
                    idx = df[df['cod_prod'].astype(str) == cod_prod_str].index[0]
                    df.loc[idx, 'nome'] = str(nome)
                    df.loc[idx, 'descricao'] = str(descricao)
                    df.loc[idx, 'tipo'] = str(tipo)
                    df.loc[idx, 'categoria'] = str(categoria)
                    df.loc[idx, 'p_venda'] = p_venda
                    df.loc[idx, 'p_custo'] = p_custo
                    df.loc[idx, 'margem'] = margem
                    df.loc[idx, 'tipo_venda'] = tipo_venda
                    df.loc[idx, 'insumo_direto'] = insumo_direto
                    st.session_state.produtos = df
                    st.session_state.editando = False
                else:
                    novo = pd.DataFrame([{
                        'cod_prod': cod_prod_str,
                        'nome': str(nome),
                        'descricao': str(descricao),
                        'tipo': str(tipo),
                        'categoria': str(categoria),
                        'p_venda': p_venda,
                        'p_custo': p_custo,
                        'margem': margem,
                        'tipo_venda': tipo_venda,
                        'insumo_direto': insumo_direto
                    }])
                    st.session_state.produtos = pd.concat([st.session_state.produtos, novo], ignore_index=True)
                    st.session_state.editando = False

                try:
                    escrever_tabela_df(st.session_state.produtos, "produtos")
                    invalidar_cache("produtos")

                    for key in st.session_state.form_data:
                        if key in ['cod_prod', 'nome', 'descricao', 'tipo', 'categoria']:
                            st.session_state.form_data[key] = ''
                        elif key == 'p_venda':
                            st.session_state.form_data[key] = 0.0
                        elif key == 'p_custo':
                            st.session_state.form_data[key] = 0.01
                        elif key == 'tipo_venda':
                            st.session_state.form_data[key] = 'menu'
                        elif key == 'insumo_direto':
                            st.session_state.form_data[key] = ''

                    st.success(f"Produto {cod_prod} - {nome} salvo!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {str(e)}")
            else:
                st.error(f"Campos obrigatórios: {', '.join(erros)}")

        if deletar:
            if cod_prod:
                df = st.session_state.produtos
                cod_prod_str = str(cod_prod)
                df = df[df['cod_prod'].astype(str) != cod_prod_str]
                st.session_state.produtos = df

                try:
                    escrever_tabela_df(st.session_state.produtos, "produtos")
                    invalidar_cache("produtos")


                    for key in st.session_state.form_data:
                        if key in ['cod_prod', 'nome', 'descricao', 'tipo', 'categoria']:
                            st.session_state.form_data[key] = ''
                        elif key == 'p_venda':
                            st.session_state.form_data[key] = 0.0
                        elif key == 'p_custo':
                            st.session_state.form_data[key] = 0.01
                        elif key == 'tipo_venda':
                            st.session_state.form_data[key] = 'menu'
                        elif key == 'insumo_direto':
                            st.session_state.form_data[key] = ''
                    st.session_state.editando = False

                    st.success(f"Produto {cod_prod} deletado!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao deletar: {str(e)}")
            else:
                st.error("Informe o código do produto para deletar")

        if limpar:
            for key in st.session_state.form_data:
                if key in ['cod_prod', 'nome', 'descricao', 'tipo', 'categoria']:
                    st.session_state.form_data[key] = ''
                elif key == 'p_venda':
                    st.session_state.form_data[key] = 0.0
                elif key == 'p_custo':
                    st.session_state.form_data[key] = 0.01
                elif key == 'tipo_venda':
                    st.session_state.form_data[key] = 'menu'
                elif key == 'insumo_direto':
                    st.session_state.form_data[key] = ''
            st.session_state.editando = False
            st.rerun()


with aba2:
    st.subheader("📋 Cardápio")

    df = st.session_state.produtos[st.session_state.produtos['tipo_venda'].isin(['menu', 'bar'])].copy()

    if not df.empty:
        df['cod_prod_num'] = pd.to_numeric(df['cod_prod'], errors='coerce')
        df = df.sort_values(by='cod_prod_num', na_position='last').drop(columns=['cod_prod_num'])

        def tem_ficha(cod_prod):
            ficha = st.session_state.ficha_tecnica[
                st.session_state.ficha_tecnica['cod_prod'].astype(str) == str(cod_prod)
            ]
            return "✅" if not ficha.empty else "❌"

        df['Ficha'] = df['cod_prod'].apply(tem_ficha)

        colunas_exibir = ['cod_prod', 'nome', 'tipo', 'categoria', 'p_venda', 'p_custo', 'margem', 'Ficha']
        df_exibicao = df[colunas_exibir].copy()
        df_exibicao.columns = ['Código', 'Nome', 'Tipo', 'Categoria', 'Preço Venda', 'Preço Custo', 'Margem', 'Ficha']
        df_exibicao['Preço Venda'] = df_exibicao['Preço Venda'].apply(lambda x: f"R$ {float(x):.2f}")
        df_exibicao['Preço Custo'] = df_exibicao['Preço Custo'].apply(lambda x: f"R$ {float(x):.2f}")
        df_exibicao['Margem'] = df_exibicao['Margem'].apply(
            lambda x: f"{float(x) * 100:.1f}%" if float(x) != 0 else "N/A"
        )

        st.dataframe(
            df_exibicao,
            column_config={
                'Ficha': st.column_config.TextColumn('Ficha', width='small'),
            },
            use_container_width=True,
            hide_index=True
        )

        st.caption(f"📊 Total: {len(df)} produtos")
    else:
        st.info("Nenhum produto no menu/bar cadastrado")


with aba3:
    st.subheader("📋 Ficha Técnica")

    df_produtos = st.session_state.produtos[st.session_state.produtos['tipo_venda'].isin(['menu', 'bar'])]

    if df_produtos.empty:
        st.warning("⚠️ Nenhum produto cadastrado. Cadastre produtos primeiro.")
    else:
        opcoes_produtos = df_produtos['cod_prod'].astype(str) + " - " + df_produtos['nome']
        produto_selecionado = st.selectbox(
            "Selecione o produto para ficha técnica:",
            opcoes_produtos.tolist()
        )

        cod_prod_selecionado = int(produto_selecionado.split(" - ")[0])
        produto_info = df_produtos[df_produtos['cod_prod'].astype(int) == cod_prod_selecionado].iloc[0]

        card_produto(
            produto_info['nome'],
            cod_prod_selecionado,
            produto_info['tipo'],
            float(produto_info['p_venda']),
            produto_info['descricao']
        )

        st.divider()

        ficha_produto = st.session_state.ficha_tecnica[
            st.session_state.ficha_tecnica['cod_prod'].astype(str) == str(cod_prod_selecionado)
        ].copy()

        if not ficha_produto.empty and not st.session_state.insumos.empty:
            ficha_completa = ficha_produto.merge(
                st.session_state.insumos[['id_insumo', 'nome', 'unidade_compra', 'preco_unitario']],
                on='id_insumo',
                how='left'
            )

            custo_total_produto = 0.0
            for idx, row in ficha_completa.iterrows():
                if pd.notna(row['id_insumo']):
                    try:
                        qtd = float(row['quantidade'])
                    except (ValueError, TypeError):
                        qtd = 0.0
                    custo = calcular_custo_insumo(
                        row['id_insumo'],
                        qtd,
                        row['unidade_ficha']
                    )
                    try:
                        custo = float(custo)
                    except (ValueError, TypeError):
                        custo = 0.0
                    ficha_completa.loc[idx, 'custo_total'] = custo
                    custo_total_produto += custo
                else:
                    ficha_completa.loc[idx, 'custo_total'] = 0.0

            renderizar_card_ficha(produto_info, ficha_completa, custo_total_produto)

            if custo_total_produto > 0:
                idx_prod = st.session_state.produtos[
                    st.session_state.produtos['cod_prod'].astype(str) == str(cod_prod_selecionado)
                ].index
                if not idx_prod.empty:
                    st.session_state.produtos.loc[idx_prod[0], 'p_custo'] = round(float(custo_total_produto), 2)
                    p_venda = float(st.session_state.produtos.loc[idx_prod[0], 'p_venda'])
                    st.session_state.produtos.loc[idx_prod[0], 'margem'] = round((p_venda / float(custo_total_produto)) - 1, 2) if float(custo_total_produto) > 0 else 0

                    try:
                        escrever_tabela_df(st.session_state.produtos, "produtos")
                        invalidar_cache("produtos")

                    except Exception as e:
                        st.error(f"Erro ao salvar: {str(e)}")

            st.divider()
        else:
            st.info("📭 Nenhum insumo adicionado à ficha deste produto.")

        st.subheader("Gerenciar Insumos da Ficha")

        if st.session_state.insumos.empty:
            st.warning("⚠️ Nenhum insumo cadastrado. Cadastre insumos na aba 'Insumos'.")
        else:
            ficha_atual = st.session_state.ficha_tecnica[
                st.session_state.ficha_tecnica['cod_prod'].astype(str) == str(cod_prod_selecionado)
            ].copy()

            if not ficha_atual.empty:
                with st.expander("📋 Editar", expanded=True):
                    ficha_com_nomes = ficha_atual.merge(
                        st.session_state.insumos[['id_insumo', 'nome', 'unidade_compra']],
                        on='id_insumo',
                        how='left'
                    )

                    novas_quantidades = {}

                    for idx, row in ficha_com_nomes.iterrows():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                        with col1:
                            st.write(f"**{row['nome']}**")
                            st.caption(f"ID: {row['id_insumo']}")

                        with col2:
                            qtd_key = f"qtd_ficha_{row['id_insumo']}_{cod_prod_selecionado}"
                            nova_qtd = st.number_input(
                                "Qtd:",
                                min_value=0.01,
                                step=0.01,
                                value=float(row['quantidade']),
                                key=qtd_key,
                                label_visibility="collapsed"
                            )
                            novas_quantidades[row['id_insumo']] = nova_qtd

                        with col3:
                            st.write(f"Unid: {row['unidade_ficha']}")

                        with col4:
                            if st.button("🗑️", key=f"remove_ficha_{row['id_insumo']}_{cod_prod_selecionado}", help="Remover este insumo"):
                                idx_remover = st.session_state.ficha_tecnica[
                                    (st.session_state.ficha_tecnica['cod_prod'].astype(str) == str(cod_prod_selecionado)) &
                                    (st.session_state.ficha_tecnica['id_insumo'] == row['id_insumo'])
                                ].index
                                if not idx_remover.empty:
                                    st.session_state.ficha_tecnica = st.session_state.ficha_tecnica.drop(idx_remover[0]).reset_index(drop=True)

                                    try:
                                        escrever_tabela_df(st.session_state.ficha_tecnica, "ficha_tecnica")
                                        invalidar_cache("ficha_tecnica")
                                        st.success(f"✅ {row['nome']} removido!")
                                        time.sleep(0.3)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro: {str(e)}")

                        st.divider()

                    col_salvar, _ = st.columns([1, 3])
                    with col_salvar:
                        if st.button("💾 Salvar Todas as Alterações", use_container_width=True, type="primary"):
                            for id_insumo, nova_qtd in novas_quantidades.items():
                                idx_edit = st.session_state.ficha_tecnica[
                                    (st.session_state.ficha_tecnica['cod_prod'].astype(str) == str(cod_prod_selecionado)) &
                                    (st.session_state.ficha_tecnica['id_insumo'] == id_insumo)
                                ].index
                                if not idx_edit.empty:
                                    st.session_state.ficha_tecnica.loc[idx_edit[0], 'quantidade'] = nova_qtd

                            try:
                                escrever_tabela_df(st.session_state.ficha_tecnica, "ficha_tecnica")
                                invalidar_cache("ficha_tecnica")

                                st.success(f"✅ Todas as quantidades atualizadas!")
                                time.sleep(0.3)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {str(e)}")
            else:
                st.info("📭 Nenhum insumo adicionado à ficha deste produto.")

            with st.expander("➕ Adicionar Novo Insumo", expanded=False):
                with st.form("form_adicionar_insumo_ficha"):
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        insumo_selecionado = st.selectbox(
                            "Selecione o insumo:",
                            st.session_state.insumos['id_insumo'] + " - " + st.session_state.insumos['nome']
                        )
                        id_insumo = insumo_selecionado.split(" - ")[0]
                        insumo_info = st.session_state.insumos[
                            st.session_state.insumos['id_insumo'] == id_insumo
                        ].iloc[0]
                        st.caption(f"Unidade de compra: {insumo_info['unidade_compra']} | Preço: R$ {float(insumo_info['preco_unitario']):.2f}")

                    with col2:
                        quantidade = st.number_input("Qtd:", min_value=0.01, step=0.01, value=1.0)

                    with col3:
                        unidade_ficha = st.selectbox("Unidade:", UNIDADES)

                    if st.form_submit_button("➕ Adicionar", use_container_width=True):
                        existe = st.session_state.ficha_tecnica[
                            (st.session_state.ficha_tecnica['cod_prod'].astype(str) == str(cod_prod_selecionado)) &
                            (st.session_state.ficha_tecnica['id_insumo'] == id_insumo)
                        ]
                        if not existe.empty:
                            st.warning("⚠️ Este insumo já está na ficha. Edite a quantidade acima.")
                        else:
                            novo_item = pd.DataFrame([{
                                'cod_prod': str(cod_prod_selecionado),
                                'id_insumo': id_insumo,
                                'quantidade': quantidade,
                                'unidade_ficha': unidade_ficha
                            }])
                            st.session_state.ficha_tecnica = pd.concat(
                                [st.session_state.ficha_tecnica, novo_item],
                                ignore_index=True
                            )

                            try:
                                escrever_tabela_df(st.session_state.ficha_tecnica, "ficha_tecnica")
                                invalidar_cache("ficha_tecnica")

                                st.success(f"✅ Insumo adicionado!")
                                time.sleep(0.3)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {str(e)}")


with aba4:
    st.subheader("Insumos")
    if not st.session_state.insumos.empty:
        st.dataframe(
            st.session_state.insumos.sort_values(by='nome'),
            column_config={
                'id_insumo': 'ID',
                'nome': 'Insumo',
                'categoria_insumo': 'Categoria',
                'unidade_compra': 'Unidade',
                'preco_unitario': st.column_config.NumberColumn('Preço (R$)', format="R$ %.2f")
            },
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    with st.form("form_insumo"):
        col1, col2 = st.columns(2)
        with col1:
            novo_nome = st.text_input("Nome do Insumo", placeholder="Ex: Queijo Gouda")
            nova_categoria = st.text_input("Categoria", placeholder="Ex: Frios")
        with col2:
            nova_unidade = st.selectbox("Unidade de Compra", ['kg', 'g', 'L', 'ml', 'un', 'cx', 'pct'])
            novo_preco = st.number_input("Preço Unitário (R$)", min_value=0.01, step=0.01, value=1.00)

        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.form_submit_button("➕ Adicionar", use_container_width=True):
                if novo_nome:
                    ids_existentes = st.session_state.insumos['id_insumo'].tolist()
                    numeros = [int(id.replace('INS-', '')) for id in ids_existentes if id.startswith('INS-')]
                    novo_num = max(numeros) + 1 if numeros else 1
                    novo_id = f"INS-{novo_num:03d}"

                    novo_insumo = pd.DataFrame([{
                        'id_insumo': novo_id,
                        'nome': str(novo_nome),
                        'categoria_insumo': str(nova_categoria),
                        'unidade_compra': nova_unidade,
                        'preco_unitario': novo_preco
                    }])
                    st.session_state.insumos = pd.concat([st.session_state.insumos, novo_insumo], ignore_index=True)

                    try:
                        escrever_tabela_df(st.session_state.insumos, "insumos")
                        invalidar_cache("insumos")

                        st.success(f"✅ Insumo {novo_nome} adicionado!")
                        time.sleep(0.3)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")
                else:
                    st.error("⚠️ Informe o nome do insumo")

        with col_btn2:
            if st.form_submit_button("💾 Alterar", use_container_width=True):
                if novo_nome:
                    idx = st.session_state.insumos[st.session_state.insumos['nome'] == novo_nome].index
                    if not idx.empty:
                        st.session_state.insumos.loc[idx[0], 'categoria_insumo'] = str(nova_categoria)
                        st.session_state.insumos.loc[idx[0], 'unidade_compra'] = nova_unidade
                        st.session_state.insumos.loc[idx[0], 'preco_unitario'] = novo_preco

                        try:
                            escrever_tabela_df(st.session_state.insumos, "insumos")
                            invalidar_cache("insumos")
                            st.success(f"✅ Insumo {novo_nome} atualizado!")
                            time.sleep(0.3)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {str(e)}")
                    else:
                        st.error("⚠️ Insumo não encontrado. Informe o nome existente.")
                else:
                    st.error("⚠️ Informe o nome do insumo para alterar")

        with col_btn3:
            if st.form_submit_button("🗑️ Excluir", use_container_width=True):
                if novo_nome:
                    idx = st.session_state.insumos[st.session_state.insumos['nome'] == novo_nome].index
                    if not idx.empty:
                        nome_deletado = st.session_state.insumos.loc[idx[0], 'nome']
                        st.session_state.insumos = st.session_state.insumos.drop(idx[0]).reset_index(drop=True)

                        try:
                            escrever_tabela_df(st.session_state.insumos, "insumos")
                            invalidar_cache("insumos")
                            st.success(f"✅ Insumo {nome_deletado} excluído!")
                            time.sleep(0.3)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {str(e)}")
                    else:
                        st.error("⚠️ Insumo não encontrado.")
                else:
                    st.error("⚠️ Informe o nome do insumo para excluir")