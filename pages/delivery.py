import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


from components.auth import exigir_permissao
exigir_permissao("delivery")



from utils.delivery_utils import (
    carregar_delivery,
    atualizar_status,
    metricas_delivery
)
from components.card_delivery import renderizar_card_delivery

st.header("Delivery")

df = carregar_delivery()

if df.empty:
    st.info("Nenhum pedido de delivery registrado.")
    st.stop()

metricas = metricas_delivery(df)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Ativos", metricas['ativos'])
col2.metric("Entregues hoje", metricas['entregues_hoje'])
col3.metric("Produção (min)", metricas['tempo_medio_producao'])
col4.metric("Entrega (min)", metricas['tempo_medio_entrega'])
col5.metric("Atrasados", metricas['atrasados'])

st.divider()

aba_ativos, aba_entregues = st.tabs(["Em Andamento", "Entregues"])

with aba_ativos:
    ativos = df[df['status_entrega'].isin(['preparando', 'pronto', 'em_rota', 'chegou'])].copy()

    if ativos.empty:
        st.info("Nenhum pedido ativo.")
    else:
        ativos = ativos.sort_values('criado_em')
        for _, row in ativos.iterrows():
            renderizar_card_delivery(row)

            id_pedido = row['id_pedido']
            status = row['status_entrega']

            col_a, col_b, col_c = st.columns(3)

            with col_a:
                if status == 'preparando':
                    if st.button("🛎️ Pronto", key=f"pronto_{id_pedido}", use_container_width=True):
                        atualizar_status(id_pedido, 'pronto')
                        st.rerun()

            with col_b:
                if status == 'pronto':
                    motoboy = st.text_input("Motoboy", key=f"motoboy_{id_pedido}", label_visibility="collapsed", placeholder="Nome do motoboy")
                    if st.button("🛵 Despachar", key=f"despachar_{id_pedido}", use_container_width=True):
                        atualizar_status(id_pedido, 'em_rota', motoboy)
                        st.rerun()

                if status == 'em_rota':
                    if st.button("📍 Chegou", key=f"chegou_{id_pedido}", use_container_width=True):
                        atualizar_status(id_pedido, 'chegou')
                        st.rerun()

            with col_c:
                if status in ['chegou', 'em_rota']:
                    if st.button("✅ Entregue", key=f"entregue_{id_pedido}", use_container_width=True, type="primary"):
                        atualizar_status(id_pedido, 'entregue')
                        st.rerun()

with aba_entregues:
    entregues_base = df[df['status_entrega'] == 'entregue'].copy()
    entregues_base['entregue_dt'] = pd.to_datetime(
        entregues_base['entregue_em'],
        format="%d/%m/%Y %H:%M:%S",
        errors='coerce'
    )

    st.markdown("##### 🔎 Filtros")

    col_periodo, col_busca = st.columns([1, 2])

    with col_periodo:
        periodo = st.selectbox(
            "Período",
            ["Hoje", "Ontem", "Últimos 7 dias", "Últimos 30 dias", "Todo o período"],
            index=0,
            key="entregues_periodo"
        )

    with col_busca:
        busca = st.text_input(
            "Buscar por ID do pedido ou ID do cliente",
            placeholder="Ex: PED-00123 ou CLI-045",
            key="entregues_busca"
        )

    hoje_dt = datetime.now()
    inicio_dt = hoje_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    if periodo == "Hoje":
        fim_dt = inicio_dt + timedelta(days=1)
    elif periodo == "Ontem":
        inicio_dt = inicio_dt - timedelta(days=1)
        fim_dt = inicio_dt + timedelta(days=1)
    elif periodo == "Últimos 7 dias":
        inicio_dt = inicio_dt - timedelta(days=7)
        fim_dt = hoje_dt + timedelta(days=1)
    elif periodo == "Últimos 30 dias":
        inicio_dt = inicio_dt - timedelta(days=30)
        fim_dt = hoje_dt + timedelta(days=1)
    else:
        inicio_dt = None
        fim_dt = None

    entregues = entregues_base.copy()

    if inicio_dt is not None:
        entregues = entregues[entregues['entregue_dt'] >= inicio_dt]
    if fim_dt is not None:
        entregues = entregues[entregues['entregue_dt'] <= fim_dt]

    if busca.strip():
        termo = busca.strip().lower()
        entregues = entregues[
            entregues['id_pedido'].astype(str).str.lower().str.contains(termo, na=False)
            | entregues['id_cliente'].astype(str).str.lower().str.contains(termo, na=False)
        ]

    entregues = entregues.sort_values('entregue_dt', ascending=False)

    st.caption(f"{len(entregues)} entregue(s) no filtro aplicado")

    if entregues.empty:
        st.info("Nenhum pedido entregue no período/busca aplicado.")
    else:
        for _, row in entregues.iterrows():
            renderizar_card_delivery(row)