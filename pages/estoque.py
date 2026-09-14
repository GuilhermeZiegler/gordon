import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import time
import pickle

from components.auth import exigir_permissao
exigir_permissao("estoque")

from utils.paths import get_caminhos
from utils.pedidos_utils import carregar_pkl

from utils.movimentacoes_utils import (
    COLUNAS_MOVIMENTACOES,
    MOTIVOS_AJUSTE,
    carregar_movimentacoes,
    salvar_movimentacoes,
    registrar_compra,
    registrar_ajuste,
    calcular_estoque_atual,
    custo_medio_por_insumo,
    converter_unidade
)

_c = get_caminhos()
CAMINHO_MOVIMENTACOES = _c["movimentacoes"]
CAMINHO_INSUMOS = _c["insumos"]

os.makedirs(os.path.dirname(CAMINHO_MOVIMENTACOES), exist_ok=True)

from help.estoque_help import help_itens

UNIDADES = ['kg', 'g', 'L', 'ml', 'un', 'cx', 'pct']


def importar_compras_excel(df_upload, ids_insumos_validos, usuario):
    importados = 0
    erros = []

    for idx, row in df_upload.iterrows():
        id_insumo = str(row.get('id_insumo', '')).strip()

        if id_insumo not in ids_insumos_validos:
            erros.append(f"Linha {idx+2}: Insumo {id_insumo} não encontrado")
            continue

        try:
            quantidade = float(row['quantidade'])
            preco_unitario = float(row['preco_unitario'])
            unidade = str(row['unidade']).strip()
            fornecedor = str(row.get('fornecedor', 'Importado')).strip()
            nota_fiscal = str(row.get('nota_fiscal', '')).strip()
            data_validade = str(row.get('data_validade', '')).strip()

            registrar_compra(
                id_insumo=id_insumo,
                quantidade=quantidade,
                unidade=unidade,
                preco_unitario=preco_unitario,
                fornecedor=fornecedor,
                nota_fiscal=nota_fiscal,
                data_validade=data_validade,
                usuario=usuario,
            )
            importados += 1
        except Exception as e:
            erros.append(f"Linha {idx+2}: {str(e)}")

    return importados, erros


def importar_ajustes_excel(df_upload, ids_insumos_validos, usuario):
    importados = 0
    erros = []

    for idx, row in df_upload.iterrows():
        id_insumo = str(row.get('id_insumo', '')).strip()

        if id_insumo not in ids_insumos_validos:
            erros.append(f"Linha {idx+2}: Insumo {id_insumo} não encontrado")
            continue

        try:
            quantidade = float(row['quantidade'])
            unidade = str(row['unidade']).strip()
            motivo = str(row['motivo']).strip().lower()
            observacao = str(row.get('observacao', '')).strip()

            if motivo not in MOTIVOS_AJUSTE:
                erros.append(f"Linha {idx+2}: Motivo inválido '{motivo}'")
                continue

            registrar_ajuste(
                id_insumo=id_insumo,
                quantidade=quantidade,
                unidade=unidade,
                motivo=motivo,
                observacao=observacao,
                usuario=usuario,
            )
            importados += 1
        except Exception as e:
            erros.append(f"Linha {idx+2}: {str(e)}")

    return importados, erros


if 'insumos' not in st.session_state:
    st.session_state.insumos = carregar_pkl(CAMINHO_INSUMOS)

if st.session_state.insumos is None or st.session_state.insumos.empty:
    st.session_state.insumos = pd.DataFrame()

if 'compra_temp' not in st.session_state:
    st.session_state.compra_temp = {
        'fornecedor': '',
        'nota_fiscal': '',
        'itens': []
    }

usuario_atual = st.session_state.get('usuario', 'Sistema')

st.header("Estoque")

aba1, aba2, aba3, aba4 = st.tabs([
    "Controle",
    "Movimentações",
    "Compras",
    "Ajustes"
])


with aba1:
    st.subheader("Situação Atual")

    df_insumos = st.session_state.insumos

    if df_insumos.empty:
        st.warning("⚠️ Nenhum insumo cadastrado.")
    else:
        df_estoque = calcular_estoque_atual()
        df_custo = custo_medio_por_insumo()

        df_view = df_insumos[['id_insumo', 'nome', 'unidade_compra']].copy()
        df_view = df_view.merge(df_estoque, on='id_insumo', how='left')
        df_view = df_view.merge(df_custo, on='id_insumo', how='left')

        df_view['estoque'] = df_view['estoque'].fillna(0.0)
        df_view['custo_medio'] = df_view['custo_medio'].fillna(0.0)
        df_view['valor_total'] = df_view['estoque'] * df_view['custo_medio']

        total_itens = len(df_view)
        total_zerados = (df_view['estoque'] <= 0).sum()
        total_valor = df_view['valor_total'].sum()

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("📦 Insumos", total_itens)
        with col_m2:
            st.metric("⚠️ Zerados", int(total_zerados))
        with col_m3:
            st.metric("💰 Valor em Estoque", f"R$ {total_valor:.2f}")

        st.divider()

        busca = st.text_input(
            "🔍 Buscar insumo:",
            placeholder="Nome ou código",
            key="busca_estoque"
        )

        df_exibicao = df_view.copy()

        if busca:
            df_exibicao = df_exibicao[
                df_exibicao['id_insumo'].str.contains(busca, case=False, na=False) |
                df_exibicao['nome'].str.contains(busca, case=False, na=False)
            ]

        df_exibicao = df_exibicao.sort_values('estoque', ascending=False)

        st.dataframe(
            df_exibicao,
            column_config={
                'id_insumo': 'ID',
                'nome': 'Insumo',
                'unidade_compra': 'Unid',
                'estoque': st.column_config.NumberColumn('Estoque', format="%.2f"),
                'custo_medio': st.column_config.NumberColumn('Custo Médio (R$)', format="R$ %.2f"),
                'valor_total': st.column_config.NumberColumn('Valor Total (R$)', format="R$ %.2f"),
            },
            use_container_width=True,
            hide_index=True
        )


with aba2:
    st.subheader("Movimentações")

    df_mov = carregar_movimentacoes()

    if df_mov.empty:
        st.info("Nenhuma movimentação registrada.")
    else:
        df_mov = df_mov.copy()
        df_mov['data_movimentacao_dt'] = pd.to_datetime(
            df_mov['data_movimentacao'],
            format="%d/%m/%Y %H:%M:%S",
            errors='coerce'
        )

        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            filtro_tipo = st.selectbox(
                "Tipo:",
                ["Todos", "compra", "venda", "ajuste"],
                key="filtro_tipo_mov"
            )

        with col_f2:
            filtro_insumo = st.selectbox(
                "Insumo:",
                ["Todos"] + sorted(df_mov['id_insumo'].dropna().unique().tolist()),
                key="filtro_insumo_mov"
            )

        with col_f3:
            periodo = st.selectbox(
                "Período:",
                ["Tudo", "Hoje", "Últimos 7 dias", "Últimos 30 dias"],
                key="filtro_periodo_mov"
            )

        df_filtrado = df_mov.copy()

        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado['tipo'] == filtro_tipo]

        if filtro_insumo != "Todos":
            df_filtrado = df_filtrado[df_filtrado['id_insumo'] == filtro_insumo]

        agora = datetime.now()

        if periodo == "Hoje":
            df_filtrado = df_filtrado[
                df_filtrado['data_movimentacao_dt'].dt.date == agora.date()
            ]
        elif periodo == "Últimos 7 dias":
            df_filtrado = df_filtrado[
                df_filtrado['data_movimentacao_dt'] >= (agora - timedelta(days=7))
            ]
        elif periodo == "Últimos 30 dias":
            df_filtrado = df_filtrado[
                df_filtrado['data_movimentacao_dt'] >= (agora - timedelta(days=30))
            ]

        df_filtrado = df_filtrado.sort_values(
            'data_movimentacao_dt',
            ascending=False
        )

        df_exibicao = df_filtrado[[
            'id_movimentacao',
            'tipo',
            'id_insumo',
            'quantidade',
            'unidade',
            'data_movimentacao',
            'id_pedido',
            'cod_item',
            'cod_prod'
        ]].copy()

        for col in ['id_pedido', 'cod_item', 'cod_prod']:
            df_exibicao[col] = df_exibicao[col].fillna('')

        st.dataframe(
            df_exibicao,
            column_config={
                'id_movimentacao': 'ID',
                'tipo': 'Tipo',
                'id_insumo': 'Insumo',
                'quantidade': st.column_config.NumberColumn('Qtd', format="%.2f"),
                'unidade': 'Unid',
                'data_movimentacao': 'Data',
                'id_pedido': 'Pedido',
                'cod_item': 'Item',
                'cod_prod': 'Produto',
            },
            use_container_width=True,
            hide_index=True
        )

with aba3:
    st.subheader("➕ Registrar Compra")

    df_insumos = st.session_state.insumos

    if df_insumos.empty:
        st.warning("⚠️ Nenhum insumo cadastrado.")
    else:
        with st.expander("📤 Importar Compras via Excel"):
            st.markdown("**Formato esperado:**")
            st.code(
                "id_insumo | quantidade | unidade | preco_unitario | "
                "fornecedor | nota_fiscal (opc) | data_validade (opc)"
            )

            arquivo_excel = st.file_uploader(
                "Envie o arquivo Excel (.xlsx)",
                type=['xlsx'],
                key="upload_compras_excel"
            )

            if arquivo_excel:
                try:
                    df_upload = pd.read_excel(arquivo_excel)
                    st.write(f"📄 {len(df_upload)} registros encontrados")

                    obrigatorias = [
                        'id_insumo',
                        'quantidade',
                        'unidade',
                        'preco_unitario',
                        'fornecedor'
                    ]
                    ausentes = [c for c in obrigatorias if c not in df_upload.columns]

                    if ausentes:
                        st.error(f"❌ Colunas obrigatórias faltando: {', '.join(ausentes)}")
                    else:
                        st.success("✅ Arquivo válido!")
                        st.dataframe(df_upload.head(), use_container_width=True, hide_index=True)

                        if st.button(
                            "📥 Importar Compras",
                            use_container_width=True,
                            type="primary",
                            key="btn_importar_compras"
                        ):
                            importados, erros = importar_compras_excel(
                                df_upload,
                                set(df_insumos['id_insumo'].astype(str)),
                                usuario_atual
                            )
                            if importados > 0:
                                st.success(f"✅ {importados} compras importadas!")
                                time.sleep(0.5)
                                st.rerun()
                            if erros:
                                st.warning(f"⚠️ {len(erros)} erros:")
                                for erro in erros[:10]:
                                    st.write(f"- {erro}")
                except Exception as e:
                    st.error(f"❌ Erro ao ler arquivo: {str(e)}")

        st.divider()

        st.markdown("### Dados da Compra")

        col1, col2 = st.columns(2)
        with col1:
            fornecedor = st.text_input(
                "Fornecedor:",
                placeholder="Nome do fornecedor",
                key="fornecedor_temp"
            )
        with col2:
            nota_fiscal = st.text_input(
                "Nota Fiscal:",
                placeholder="Número da NF",
                key="nota_fiscal_temp"
            )

        st.divider()
        st.markdown("### Adicionar Itens")

        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

        with col1:
            opcoes_insumos = (
                df_insumos['id_insumo'].astype(str) + " - " + df_insumos['nome']
            ).tolist()

            insumo_selecionado = st.selectbox(
                "Insumo:",
                opcoes_insumos,
                key="insumo_temp"
            )
            id_insumo_temp = insumo_selecionado.split(" - ")[0]

            unidade_padrao = df_insumos[
                df_insumos['id_insumo'].astype(str) == id_insumo_temp
            ]['unidade_compra'].iloc[0]

        with col2:
            quantidade = st.number_input(
                "Qtd:",
                min_value=0.01,
                step=0.1,
                value=1.0,
                key="qtd_temp"
            )

        with col3:
            unidade = st.selectbox(
                "Unidade:",
                UNIDADES,
                index=UNIDADES.index(unidade_padrao) if unidade_padrao in UNIDADES else 0,
                key="unidade_temp"
            )

        with col4:
            preco_unitario = st.number_input(
                "Preço (R$):",
                min_value=0.01,
                step=0.01,
                value=1.00,
                key="preco_temp"
            )

        with col5:
            st.write("")
            st.write("")
            if st.button("➕ Adicionar", use_container_width=True):
                st.session_state.compra_temp['itens'].append({
                    'id_insumo': id_insumo_temp,
                    'nome_insumo': insumo_selecionado.split(" - ")[1],
                    'quantidade': quantidade,
                    'unidade': unidade,
                    'preco_unitario': preco_unitario,
                    'valor_total': quantidade * preco_unitario,
                    'data_validade': ''
                })
                st.rerun()

        if st.session_state.compra_temp['itens']:
            st.divider()
            st.markdown("### Itens da Compra")

            df_itens = pd.DataFrame(st.session_state.compra_temp['itens'])
            total_compra = df_itens['valor_total'].sum()

            st.dataframe(
                df_itens[['nome_insumo', 'quantidade', 'unidade', 'preco_unitario', 'valor_total']],
                column_config={
                    'nome_insumo': 'Insumo',
                    'quantidade': 'Qtd',
                    'unidade': 'Unid',
                    'preco_unitario': st.column_config.NumberColumn('Preço (R$)', format="R$ %.2f"),
                    'valor_total': st.column_config.NumberColumn('Total (R$)', format="R$ %.2f"),
                },
                use_container_width=True,
                hide_index=True
            )

            col_t, col_l, col_s = st.columns([2, 1, 1])

            with col_t:
                st.metric("💰 Total da Compra", f"R$ {total_compra:.2f}")

            with col_l:
                if st.button("🗑️ Limpar", use_container_width=True):
                    st.session_state.compra_temp = {
                        'fornecedor': '',
                        'nota_fiscal': '',
                        'itens': []
                    }
                    st.rerun()

            with col_s:
                if st.button("✅ Registrar Compra", use_container_width=True, type="primary"):
                    if not fornecedor:
                        st.error("⚠️ Informe o fornecedor")
                    else:
                        for item in st.session_state.compra_temp['itens']:
                            registrar_compra(
                                id_insumo=item['id_insumo'],
                                quantidade=item['quantidade'],
                                unidade=item['unidade'],
                                preco_unitario=item['preco_unitario'],
                                fornecedor=str(fornecedor),
                                nota_fiscal=str(nota_fiscal),
                                data_validade=item.get('data_validade', ''),
                                usuario=usuario_atual,
                            )

                        st.session_state.compra_temp = {
                            'fornecedor': '',
                            'nota_fiscal': '',
                            'itens': []
                        }

                        st.success("✅ Compra registrada!")
                        time.sleep(0.5)
                        st.rerun()
        else:
            st.info("📭 Nenhum item adicionado.")


with aba4:
    st.subheader("Ajustes", help=help_itens['help_inventario'])

    df_insumos = st.session_state.insumos

    if df_insumos.empty:
        st.warning("⚠️ Nenhum insumo cadastrado.")
    else:
        with st.expander("📤 Importar Ajustes via Excel"):
            st.markdown("**Formato esperado:**")
            st.code(
                "id_insumo | quantidade | unidade | motivo | observacao (opc)"
            )
            st.caption(
                "Motivos válidos: " + ", ".join(MOTIVOS_AJUSTE)
            )

            arquivo_excel = st.file_uploader(
                "Envie o arquivo Excel (.xlsx)",
                type=['xlsx'],
                key="upload_ajustes_excel"
            )

            if arquivo_excel:
                try:
                    df_upload = pd.read_excel(arquivo_excel)
                    st.write(f"📄 {len(df_upload)} registros encontrados")

                    obrigatorias = ['id_insumo', 'quantidade', 'unidade', 'motivo']
                    ausentes = [c for c in obrigatorias if c not in df_upload.columns]

                    if ausentes:
                        st.error(f"❌ Colunas obrigatórias faltando: {', '.join(ausentes)}")
                    else:
                        st.success("✅ Arquivo válido!")
                        st.dataframe(df_upload.head(), use_container_width=True, hide_index=True)

                        if st.button(
                            "📥 Importar Ajustes",
                            use_container_width=True,
                            type="primary",
                            key="btn_importar_ajustes"
                        ):
                            importados, erros = importar_ajustes_excel(
                                df_upload,
                                set(df_insumos['id_insumo'].astype(str)),
                                usuario_atual
                            )
                            if importados > 0:
                                st.success(f"✅ {importados} ajustes importados!")
                                time.sleep(0.5)
                                st.rerun()
                            if erros:
                                st.warning(f"⚠️ {len(erros)} erros:")
                                for erro in erros[:10]:
                                    st.write(f"- {erro}")
                except Exception as e:
                    st.error(f"❌ Erro ao ler arquivo: {str(e)}")

        st.divider()

        df_estoque = calcular_estoque_atual()

        opcoes_insumos = (
            df_insumos['id_insumo'].astype(str) + " - " + df_insumos['nome']
        ).tolist()

        col1, col2 = st.columns(2)

        with col1:
            insumo_selecionado = st.selectbox(
                "Insumo:",
                opcoes_insumos,
                key="ajuste_insumo"
            )
            id_insumo = insumo_selecionado.split(" - ")[0]

            linha_insumo = df_insumos[
                df_insumos['id_insumo'].astype(str) == id_insumo
            ].iloc[0]
            unidade_padrao = linha_insumo['unidade_compra']

        with col2:
            estoque_atual = 0.0
            if not df_estoque.empty:
                match = df_estoque[df_estoque['id_insumo'].astype(str) == id_insumo]
                if not match.empty:
                    estoque_atual = float(match['estoque'].iloc[0])

            st.metric(
                "📦 Estoque Atual",
                f"{estoque_atual:.2f} {unidade_padrao}"
            )

        st.divider()

        with st.form("form_ajuste"):
            col1, col2, col3 = st.columns(3)

            with col1:
                quantidade_ajuste = st.number_input(
                    "Quantidade:",
                    min_value=0.01,
                    step=0.1,
                    value=1.0
                )

            with col2:
                unidade_ajuste = st.selectbox(
                    "Unidade:",
                    UNIDADES,
                    index=UNIDADES.index(unidade_padrao) if unidade_padrao in UNIDADES else 0
                )

            with col3:
                motivo_ajuste = st.selectbox(
                    "Motivo:",
                    MOTIVOS_AJUSTE
                )

            observacao_ajuste = st.text_input(
                "Observação:",
                placeholder="Detalhe o ajuste..."
            )

            if st.form_submit_button(
                "📊 Registrar Ajuste",
                use_container_width=True,
                type="primary"
            ):
                try:
                    registrar_ajuste(
                        id_insumo=id_insumo,
                        quantidade=quantidade_ajuste,
                        unidade=unidade_ajuste,
                        motivo=motivo_ajuste,
                        observacao=observacao_ajuste,
                        usuario=usuario_atual,
                    )
                    st.success("✅ Ajuste registrado!")
                    time.sleep(0.8)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {str(e)}")