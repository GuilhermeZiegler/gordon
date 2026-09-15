import streamlit as st
import pandas as pd
import pickle
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from components.auth import exigir_permissao
exigir_permissao("indicadores")

st.set_page_config(page_title="Indicadores", page_icon="📊", layout="wide")
st.title("Dashboard")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def carregar_pkl(caminho):
    if os.path.exists(caminho):
        with open(caminho, 'rb') as f:
            return pickle.load(f)
    return None


def carregar_historicos():
    historico_mesas = carregar_pkl("data/historico_mesas.pkl")
    historico_pedidos = carregar_pkl("data/historico_pedidos.pkl")
    historico_caixa = carregar_pkl("data/historico_caixa.pkl")
    clientes = carregar_pkl("data/clientes.pkl")

    if historico_mesas is None:
        historico_mesas = []
    if historico_pedidos is None:
        historico_pedidos = []
    if historico_caixa is None:
        historico_caixa = []
    if clientes is None:
        clientes = []

    df_mesas = historico_mesas.copy() if isinstance(historico_mesas, pd.DataFrame) else pd.DataFrame(historico_mesas if historico_mesas else [])
    df_pedidos = historico_pedidos.copy() if isinstance(historico_pedidos, pd.DataFrame) else pd.DataFrame(historico_pedidos if historico_pedidos else [])
    df_caixa = historico_caixa.copy() if isinstance(historico_caixa, pd.DataFrame) else pd.DataFrame(historico_caixa if historico_caixa else [])

    for df in [df_mesas, df_pedidos]:
        if not df.empty:
            for col in ['aberto_em', 'fechado_em', 'criado_em', 'data_fechamento']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], format="%d/%m/%Y %H:%M:%S", errors='coerce')

    if not df_pedidos.empty and 'data_fechamento' in df_pedidos.columns:
        df_pedidos['data_fechamento'] = pd.to_datetime(
            df_pedidos['data_fechamento'], format="%d/%m/%Y %H:%M:%S", errors='coerce'
        )

    return df_mesas, df_pedidos, df_caixa, pd.DataFrame(clientes)


def filtrar_por_periodo(df, coluna_data, dias):
    if df.empty or coluna_data not in df.columns:
        return df
    data_corte = datetime.now() - timedelta(days=dias)
    return df[df[coluna_data] >= data_corte]


def card_metricas_html(metricas):
    html = '<div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 20px;">'

    for metrica in metricas:
        cor = metrica.get('cor', '#4CAF50')
        html += f"""
        <div style="background: #1e1e1e; border-radius: 10px; padding: 15px; border-left: 4px solid {cor}; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
            <p style="margin: 0; color: #888; font-size: 12px;">{metrica['label']}</p>
            <p style="margin: 4px 0 0 0; font-size: 22px; font-weight: bold; color: #fff;">{metrica['valor']}</p>
            {f'<p style="margin: 0; color: {metrica.get("delta_cor", "#888")}; font-size: 12px;">{metrica["delta"]}</p>' if metrica.get('delta') else ''}
        </div>
        """

    html += '</div>'
    return html


# ============================================================
# CARREGAR DADOS
# ============================================================
df_mesas, df_pedidos, df_caixa, df_clientes = carregar_historicos()

if df_mesas.empty and df_pedidos.empty:
    st.warning("⚠️ Nenhum dado histórico encontrado. Popule os históricos primeiro.")
    st.stop()


# ============================================================
# FILTROS
# ============================================================
st.sidebar.header("Filtros")

periodo = st.sidebar.selectbox(
    "Período:",
    [7, 30, 60, 90, 180, 365],
    index=2,
    format_func=lambda x: f"Últimos {x} dias"
)

df_mesas_filtrado = filtrar_por_periodo(df_mesas, 'fechado_em', periodo)
df_pedidos_filtrado = filtrar_por_periodo(df_pedidos, 'data_fechamento', periodo)


# ============================================================
# SELETOR DE GRÁFICOS
# ============================================================
st.sidebar.header("Selecionar Gráficos")

mostrar = {
    'metricas': st.sidebar.checkbox("Métricas Gerais", True),
    'dre': st.sidebar.checkbox("DRE", True),
    'evolucao_mensal': st.sidebar.checkbox("Evolução Mensal (3 meses)", True),
    'demanda_diaria': st.sidebar.checkbox("Demanda Diária", True),
    'demanda_semana': st.sidebar.checkbox("Demanda por Dia da Semana", True),
    'distribuicao_horario': st.sidebar.checkbox("Distribuição por Horário", True),
    'origem_venda': st.sidebar.checkbox("Origem de Venda", True),
    'top_produtos': st.sidebar.checkbox("Top Produtos", True),
    'analise_garcom': st.sidebar.checkbox("Análise por Garçom", True),
    'menu_vs_bar': st.sidebar.checkbox("Menu vs Bar vs Balcão", True),
    'analise_cliente': st.sidebar.checkbox("Análise por Cliente", True),
    'analise_bairro': st.sidebar.checkbox("Análise por Bairro", True),
    'analise_pagamento': st.sidebar.checkbox("Meios de Pagamento", True),
    'analise_delivery': st.sidebar.checkbox("Análise de Delivery", True),
    'analise_financeira': st.sidebar.checkbox("Análise Financeira", True),
    'analise_cover': st.sidebar.checkbox("Análise de Cover e 10%", True),
    'analise_caixa': st.sidebar.checkbox("Análise do Caixa", True),
    # 'comparativo_mes': st.sidebar.checkbox("Comparativo Mês Atual vs Anterior", False),
    'analise_estoque': st.sidebar.checkbox("Análise de Estoque", True),
}

st.sidebar.markdown("---")
st.sidebar.caption(f"Dados de {periodo} dias")


# ============================================================
# 1. MÉTRICAS GERAIS
# ============================================================
if mostrar['metricas']:
    st.subheader("Métricas Gerais")

    faturamento_total = df_pedidos_filtrado['valor_com_desconto'].sum() if not df_pedidos_filtrado.empty else 0
    taxa_entrega_total = df_pedidos_filtrado['taxa_entrega'].sum() if not df_pedidos_filtrado.empty and 'taxa_entrega' in df_pedidos_filtrado.columns else 0
    taxa_embalagem_total = df_pedidos_filtrado['taxa_embalagem'].sum() if not df_pedidos_filtrado.empty and 'taxa_embalagem' in df_pedidos_filtrado.columns else 0

    faturamento_final = faturamento_total + taxa_entrega_total + taxa_embalagem_total

    total_pedidos = df_pedidos_filtrado['id_pedido'].nunique() if not df_pedidos_filtrado.empty else 0
    total_itens = df_pedidos_filtrado['quantidade'].sum() if not df_pedidos_filtrado.empty else 0
    ticket_medio = faturamento_final / total_pedidos if total_pedidos > 0 else 0
    clientes_unicos = df_pedidos_filtrado['id_cliente'].replace('', pd.NA).dropna().nunique() if not df_pedidos_filtrado.empty else 0

    metricas = [
        {'label': 'Faturamento Total', 'valor': f"R$ {faturamento_final:,.2f}", 'cor': '#2ecc71'},
        {'label': 'Pedidos', 'valor': f"{total_pedidos}", 'cor': '#3498db'},
        {'label': 'Itens Vendidos', 'valor': f"{int(total_itens)}", 'cor': '#f39c12'},
        {'label': 'Ticket Médio', 'valor': f"R$ {ticket_medio:.2f}", 'cor': '#9b59b6'},
        {'label': 'Clientes Únicos', 'valor': f"{clientes_unicos}", 'cor': '#e74c3c'},
    ]

    st.html(card_metricas_html(metricas))
    st.divider()


# ============================================================
# 1.5. DRE
# ============================================================
if mostrar['dre']:
    from components.card_dre import renderizar_card_dre
    from utils.caixa_utils import carregar_historico_caixa
    from utils.agendamentos_utils import carregar_agendamentos

    st.subheader("📊 DRE — Demonstrativo de Resultado")

    col_p1, col_p2, col_p3 = st.columns([2, 1, 1])

    opcoes_periodo = [
        "Este mês",
        "Mês passado",
        "Últimos 3 meses",
        "Últimos 6 meses",
        "Últimos 12 meses",
        "Mês específico",
        "Intervalo customizado"
    ]

    with col_p1:
        periodo_dre = st.selectbox(
            "Período:",
            opcoes_periodo,
            index=0,
            key="dre_periodo_select"
        )

    hoje = datetime.now()

    if periodo_dre == "Este mês":
        inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fim = hoje
        label = f"Este mês — {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
        inicio_ant = (inicio - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fim_ant = inicio - timedelta(seconds=1)
        label_ant = f"Mês anterior — {inicio_ant.strftime('%d/%m/%Y')} a {fim_ant.strftime('%d/%m/%Y')}"

    elif periodo_dre == "Mês passado":
        inicio = (hoje.replace(day=1) - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fim = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        label = f"Mês passado — {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
        inicio_ant = (inicio - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fim_ant = inicio - timedelta(seconds=1)
        label_ant = f"Período anterior — {inicio_ant.strftime('%d/%m/%Y')} a {fim_ant.strftime('%d/%m/%Y')}"

    elif periodo_dre == "Últimos 3 meses":
        inicio = (hoje - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0)
        fim = hoje
        label = f"Últimos 3 meses — {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
        inicio_ant = inicio - timedelta(days=90)
        fim_ant = inicio - timedelta(seconds=1)
        label_ant = f"3 meses anteriores — {inicio_ant.strftime('%d/%m/%Y')} a {fim_ant.strftime('%d/%m/%Y')}"

    elif periodo_dre == "Últimos 6 meses":
        inicio = (hoje - timedelta(days=180)).replace(hour=0, minute=0, second=0, microsecond=0)
        fim = hoje
        label = f"Últimos 6 meses — {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
        inicio_ant = inicio - timedelta(days=180)
        fim_ant = inicio - timedelta(seconds=1)
        label_ant = f"6 meses anteriores — {inicio_ant.strftime('%d/%m/%Y')} a {fim_ant.strftime('%d/%m/%Y')}"

    elif periodo_dre == "Últimos 12 meses":
        inicio = (hoje - timedelta(days=365)).replace(hour=0, minute=0, second=0, microsecond=0)
        fim = hoje
        label = f"Últimos 12 meses — {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
        inicio_ant = inicio - timedelta(days=365)
        fim_ant = inicio - timedelta(seconds=1)
        label_ant = f"12 meses anteriores — {inicio_ant.strftime('%d/%m/%Y')} a {fim_ant.strftime('%d/%m/%Y')}"

    elif periodo_dre == "Mês específico":
        with col_p2:
            meses_disponiveis = set()
            for cx in carregar_historico_caixa():
                data_str = cx.get("data_abertura", "")
                if data_str:
                    try:
                        dt = datetime.strptime(data_str.split(" ")[0], "%d/%m/%Y")
                        meses_disponiveis.add((dt.year, dt.month))
                    except Exception:
                        pass

            if not meses_disponiveis:
                st.warning("Nenhum mês com dados.")
                st.stop()

            meses_ordenados = sorted(meses_disponiveis, reverse=True)

            mes_escolhido = st.selectbox(
                "Mês/Ano:",
                meses_ordenados,
                format_func=lambda x: f"{x[1]:02d}/{x[0]}",
                key="dre_mes_especifico"
            )

        inicio = datetime(mes_escolhido[0], mes_escolhido[1], 1)
        if mes_escolhido[1] == 12:
            proximo = datetime(mes_escolhido[0] + 1, 1, 1)
        else:
            proximo = datetime(mes_escolhido[0], mes_escolhido[1] + 1, 1)
        fim = proximo - timedelta(seconds=1)

        label = f"{mes_escolhido[1]:02d}/{mes_escolhido[0]} — {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"

        ano_ant = mes_escolhido[0] - 1
        if (ano_ant, mes_escolhido[1]) in meses_disponiveis:
            inicio_ant = datetime(ano_ant, mes_escolhido[1], 1)
            if mes_escolhido[1] == 12:
                proximo_ant = datetime(ano_ant + 1, 1, 1)
            else:
                proximo_ant = datetime(ano_ant, mes_escolhido[1] + 1, 1)
            fim_ant = proximo_ant - timedelta(seconds=1)
            label_ant = f"Mesmo mês ano anterior — {inicio_ant.strftime('%d/%m/%Y')} a {fim_ant.strftime('%d/%m/%Y')}"
        else:
            inicio_ant = None
            fim_ant = None
            label_ant = "Sem dados do ano anterior"

    else:
        with col_p2:
            data_ini = st.date_input("Início:", hoje - timedelta(days=30), key="dre_ini")
        with col_p3:
            data_fim = st.date_input("Fim:", hoje, key="dre_fim")

        inicio = datetime.combine(data_ini, datetime.min.time())
        fim = datetime.combine(data_fim, datetime.max.time())

        label = f"{inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"

        duracao = fim - inicio
        inicio_ant = inicio - duracao
        fim_ant = inicio - timedelta(seconds=1)
        label_ant = f"Período anterior — {inicio_ant.strftime('%d/%m/%Y')} a {fim_ant.strftime('%d/%m/%Y')}"

    with col_p3 if periodo_dre != "Intervalo customizado" else col_p1:
        comparar = st.checkbox(
            "Comparar com período anterior",
            value=False,
            key="dre_comparar"
        )

    st.divider()

    st.markdown("**Split do 10% Atendimento**")

    col_s1, col_s2, col_s3 = st.columns(3)

    with col_s1:
        pct_garcom = st.number_input("Garçom (%)", min_value=0, max_value=100, value=70, step=5, key="dre_pct_garcom")
    with col_s2:
        pct_limpeza = st.number_input("Limpeza (%)", min_value=0, max_value=100, value=0, step=5, key="dre_pct_limpeza")
    with col_s3:
        pct_cozinha = st.number_input("Cozinha (%)", min_value=0, max_value=100, value=30, step=5, key="dre_pct_cozinha")

    soma_split = pct_garcom + pct_limpeza + pct_cozinha

    if soma_split != 100:
        st.warning(f"⚠️ Soma do split: {soma_split}% (deve ser 100%).")

    from utils.movimentacoes_utils import calcular_estoque_atual

    def _coletar_dre(inicio_dt, fim_dt, pct_garcom, pct_limpeza, pct_cozinha):
        vendas_mesa = 0.0
        vendas_balcao = 0.0
        vendas_takeaway = 0.0
        vendas_delivery = 0.0
        estornos = 0.0
        reembolsos = 0.0
        saidas_caixa = 0.0

        for cx in carregar_historico_caixa():
            data_abertura = cx.get("data_abertura", "")
            if not data_abertura:
                continue
            try:
                dt_cx = datetime.strptime(data_abertura, "%d/%m/%Y %H:%M:%S")
            except Exception:
                continue

            if dt_cx < inicio_dt or dt_cx > fim_dt:
                continue

            vendas_mesa += float(cx.get("vendas_mesa", 0) or 0)
            vendas_balcao += float(cx.get("vendas_balcao", 0) or 0)
            vendas_takeaway += float(cx.get("vendas_takeaway", 0) or 0)
            vendas_delivery += float(cx.get("vendas_delivery", 0) or 0)
            reembolsos += float(cx.get("reembolso", 0) or 0)

            for e in cx.get("estornos", []):
                estornos += float(e.get("valor_estornado", 0))

            for s in cx.get("saidas", []):
                saidas_caixa += float(s.get("valor", 0))

        # Coberturas e 10% vêm do historico_mesas
        cover_total = 0.0
        valor_10_total = 0.0
        descontos = 0.0

        try:
            import pickle
            with open("data/historico_mesas.pkl", "rb") as f:
                hist_mesas = pickle.load(f)
            for m in hist_mesas:
                fechado_em = m.get("fechado_em", "")
                if not fechado_em:
                    continue
                try:
                    dt_m = datetime.strptime(fechado_em, "%d/%m/%Y %H:%M:%S")
                except Exception:
                    continue
                if dt_m < inicio_dt or dt_m > fim_dt:
                    continue
                cover_total += float(m.get("cover", 0)) * int(m.get("qtd_clientes", 0))
                valor_10_total += float(m.get("valor_10", 0))
                descontos += float(m.get("desconto_valor", 0))
        except Exception:
            pass

        # Despesas: agendamentos pagos + saídas do caixa
        despesas_detalhe = {}

        try:
            df_agd = carregar_agendamentos()
            if not df_agd.empty:
                df_pagos = df_agd[df_agd["status"] == "pago"].copy()
                df_pagos["data_pgto_dt"] = pd.to_datetime(
                    df_pagos["data_pagamento"],
                    format="%d/%m/%Y %H:%M:%S",
                    errors="coerce"
                )
                df_pagos = df_pagos[
                    (df_pagos["data_pgto_dt"] >= inicio_dt) &
                    (df_pagos["data_pgto_dt"] <= fim_dt)
                ]
                for _, row in df_pagos.iterrows():
                    cat = row.get("categoria", "Outros")
                    despesas_detalhe[cat] = despesas_detalhe.get(cat, 0.0) + float(row.get("valor", 0))
        except Exception:
            pass

        if saidas_caixa > 0:
            despesas_detalhe["Saídas do Caixa"] = saidas_caixa

        despesas_total = sum(despesas_detalhe.values())

        # Taxa de entrega (do caixa de delivery)
        taxa_entrega = 0.0
        try:
            with open("data/historico_pedidos.pkl", "rb") as f:
                hist_pedidos = pickle.load(f)
            if isinstance(hist_pedidos, list):
                hist_pedidos = pd.DataFrame(hist_pedidos)
            if not hist_pedidos.empty:
                hist_pedidos["criado_dt"] = pd.to_datetime(
                    hist_pedidos["criado_em"],
                    format="%d/%m/%Y %H:%M:%S",
                    errors="coerce"
                )
                hist_pedidos = hist_pedidos[
                    (hist_pedidos["criado_dt"] >= inicio_dt) &
                    (hist_pedidos["criado_dt"] <= fim_dt)
                ]
                delivery = hist_pedidos[hist_pedidos["origem_venda"] == "delivery"]
                if not delivery.empty:
                    taxa_entrega = float(delivery["taxa_entrega"].drop_duplicates().sum())
        except Exception:
            pass

        # CMV simplificado (produto sem ficha = 0)
        cmv = 0.0
        try:
            with open("data/ficha_tecnica.pkl", "rb") as f:
                df_ficha = pickle.load(f)
            with open("data/insumos.pkl", "rb") as f:
                df_insumos = pickle.load(f)
            with open("data/historico_pedidos.pkl", "rb") as f:
                hist_pedidos = pickle.load(f)
            if isinstance(hist_pedidos, list):
                hist_pedidos = pd.DataFrame(hist_pedidos)

            if not df_ficha.empty and not df_insumos.empty and not hist_pedidos.empty:
                hist_pedidos["criado_dt"] = pd.to_datetime(
                    hist_pedidos["criado_em"],
                    format="%d/%m/%Y %H:%M:%S",
                    errors="coerce"
                )
                pedidos_periodo = hist_pedidos[
                    (hist_pedidos["criado_dt"] >= inicio_dt) &
                    (hist_pedidos["criado_dt"] <= fim_dt) &
                    (hist_pedidos["status"] != "cancelado")
                ]

                insumos_map = df_insumos.set_index("id_insumo")["preco_unitario"].to_dict()

                for _, pedido in pedidos_periodo.iterrows():
                    cod_prod = str(pedido["cod_prod"])
                    qtd = float(pedido["quantidade"])
                    ficha = df_ficha[df_ficha["cod_prod"].astype(str) == cod_prod]
                    for _, item in ficha.iterrows():
                        id_ins = item["id_insumo"]
                        qtd_item = float(item["quantidade"])
                        unidade_ficha = item["unidade_ficha"]

                        preco = float(insumos_map.get(id_ins, 0))

                        if unidade_ficha == "g" and "kg" in str(df_insumos[df_insumos["id_insumo"] == id_ins]["unidade_compra"].values):
                            qtd_item = qtd_item / 1000
                        elif unidade_ficha == "ml" and "L" in str(df_insumos[df_insumos["id_insumo"] == id_ins]["unidade_compra"].values):
                            qtd_item = qtd_item / 1000

                        cmv += qtd_item * qtd * preco
        except Exception:
            pass

        receita_bruta = vendas_mesa + vendas_balcao + vendas_takeaway + vendas_delivery
        receita_liquida = receita_bruta - estornos - descontos
        lucro_bruto = receita_liquida - cmv
        lucro_operacional = lucro_bruto - despesas_total

        repasse_cover = cover_total
        repasse_taxa = taxa_entrega
        repasse_10 = valor_10_total

        repasse_10_split = {
            "Garçom": round(repasse_10 * pct_garcom / 100, 2),
            "Limpeza": round(repasse_10 * pct_limpeza / 100, 2),
            "Cozinha": round(repasse_10 * pct_cozinha / 100, 2),
        }

        repasses_total = repasse_cover + repasse_taxa + repasse_10
        resultado_liquido = lucro_operacional - repasses_total

        return {
            "periodo_label": label,
            "receita_bruta": round(receita_bruta, 2),
            "vendas_mesa": round(vendas_mesa, 2),
            "vendas_balcao": round(vendas_balcao, 2),
            "vendas_takeaway": round(vendas_takeaway, 2),
            "vendas_delivery": round(vendas_delivery, 2),
            "estornos": round(estornos, 2),
            "descontos": round(descontos, 2),
            "receita_liquida": round(receita_liquida, 2),
            "cmv": round(cmv, 2),
            "lucro_bruto": round(lucro_bruto, 2),
            "despesas_total": round(despesas_total, 2),
            "despesas_detalhe": {k: round(v, 2) for k, v in despesas_detalhe.items()},
            "lucro_operacional": round(lucro_operacional, 2),
            "repasses_total": round(repasses_total, 2),
            "repasse_cover": round(repasse_cover, 2),
            "repasse_taxa_entrega": round(repasse_taxa, 2),
            "repasse_10": round(repasse_10, 2),
            "repasse_10_split": repasse_10_split,
            "resultado_liquido": round(resultado_liquido, 2),
        }

    dre_atual = _coletar_dre(inicio, fim, pct_garcom, pct_limpeza, pct_cozinha)

    dre_ant = None
    if comparar and inicio_ant and fim_ant:
        dre_ant = _coletar_dre(inicio_ant, fim_ant, pct_garcom, pct_limpeza, pct_cozinha)
        dre_ant["periodo_label"] = label_ant

    renderizar_card_dre(dre_atual, comparativo=dre_ant)
    st.divider()


# ============================================================
# 2. EVOLUÇÃO MENSAL (3 MESES)
# ============================================================
if mostrar['evolucao_mensal'] and not df_pedidos.empty:
    st.subheader("Evolução Mensal (Últimos 3 Meses)")

    df_evo = df_pedidos.copy()
    df_evo = df_evo[df_evo['data_fechamento'].notna()]

    hoje = datetime.now()
    inicio_mes_atual = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    inicio_3_meses = (inicio_mes_atual - timedelta(days=62)).replace(day=1)

    df_evo = df_evo[df_evo['data_fechamento'] >= inicio_3_meses].copy()

    if df_evo.empty:
        st.info("Sem dados nos últimos 3 meses.")
    else:
        df_evo['ano_mes'] = df_evo['data_fechamento'].dt.to_period('M').astype(str)
        df_evo['faturamento_item'] = (
            df_evo['valor_com_desconto'].fillna(0)
            + df_evo.get('taxa_entrega', 0)
            + df_evo.get('taxa_embalagem', 0)
        )

        df_evo_agg = df_evo.groupby('ano_mes').agg({
            'faturamento_item': 'sum',
            'id_pedido': 'nunique'
        }).reset_index()
        df_evo_agg.columns = ['ano_mes', 'faturamento', 'pedidos']
        df_evo_agg = df_evo_agg.sort_values('ano_mes')

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Bar(x=df_evo_agg['ano_mes'], y=df_evo_agg['faturamento'], name="Faturamento", marker_color='#2ecc71'),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=df_evo_agg['ano_mes'], y=df_evo_agg['pedidos'], name="Pedidos", mode='lines+markers', line=dict(color='#3498db')),
            secondary_y=True,
        )

        fig.update_layout(
            title="Faturamento e Pedidos por Mês",
            xaxis_title="Mês",
            hovermode='x unified',
            height=400
        )
        fig.update_yaxes(title_text="Faturamento (R$)", secondary_y=False)
        fig.update_yaxes(title_text="Pedidos", secondary_y=True)

        st.plotly_chart(fig, use_container_width=True)

        if len(df_evo_agg) >= 2:
            fat_atual = df_evo_agg['faturamento'].iloc[-1]
            fat_anterior = df_evo_agg['faturamento'].iloc[-2]
            var = ((fat_atual - fat_anterior) / fat_anterior * 100) if fat_anterior > 0 else 0

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    f"Faturamento {df_evo_agg['ano_mes'].iloc[-1]}",
                    f"R$ {fat_atual:,.2f}",
                    delta=f"{var:+.1f}% vs mês anterior"
                )
            with col2:
                st.metric(
                    f"Pedidos {df_evo_agg['ano_mes'].iloc[-1]}",
                    f"{df_evo_agg['pedidos'].iloc[-1]}",
                    delta=f"{df_evo_agg['pedidos'].iloc[-1] - df_evo_agg['pedidos'].iloc[-2]:+d} vs mês anterior"
                )
            with col3:
                media_3m = df_evo_agg['faturamento'].mean()
                st.metric("Média 3 Meses", f"R$ {media_3m:,.2f}")

    st.divider()


# ============================================================
# 4. DEMANDA DIÁRIA
# ============================================================
if mostrar['demanda_diaria'] and not df_pedidos_filtrado.empty:
    st.subheader("Demanda Diária")

    df_dia = df_pedidos_filtrado.copy()
    df_dia['dia'] = df_dia['data_fechamento'].dt.date
    df_dia['faturamento_item'] = df_dia['valor_com_desconto'] + df_dia['taxa_entrega'] + df_dia['taxa_embalagem']

    df_dia_agg = df_dia.groupby('dia').agg({
        'faturamento_item': 'sum',
        'id_pedido': 'nunique'
    }).reset_index()
    df_dia_agg.columns = ['dia', 'faturamento', 'pedidos']

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=df_dia_agg['dia'], y=df_dia_agg['faturamento'], name="Faturamento", marker_color='#2ecc71'),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df_dia_agg['dia'], y=df_dia_agg['pedidos'], name="Pedidos", mode='lines+markers', line=dict(color='#3498db')),
        secondary_y=True,
    )

    fig.update_layout(
        title="Faturamento e Pedidos por Dia",
        xaxis_title="Data",
        hovermode='x unified',
        height=400
    )
    fig.update_yaxes(title_text="Faturamento (R$)", secondary_y=False)
    fig.update_yaxes(title_text="Quantidade de Pedidos", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)
    st.divider()


# ============================================================
# 5. DEMANDA POR DIA DA SEMANA
# ============================================================
if mostrar['demanda_semana'] and not df_pedidos_filtrado.empty:
    st.subheader("Demanda por Dia da Semana")

    dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

    df_semana = df_pedidos_filtrado.copy()
    df_semana['dia_semana'] = df_semana['data_fechamento'].dt.weekday
    df_semana['faturamento_item'] = df_semana['valor_com_desconto'] + df_semana['taxa_entrega'] + df_semana['taxa_embalagem']

    df_semana_agg = df_semana.groupby('dia_semana').agg({
        'faturamento_item': 'sum',
        'id_pedido': 'nunique'
    }).reindex(range(7), fill_value=0).reset_index()
    df_semana_agg['dia_nome'] = dias_semana

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_semana_agg, x='dia_nome', y='faturamento_item',
            title="Faturamento por Dia da Semana",
            labels={'faturamento_item': 'Faturamento (R$)', 'dia_nome': ''},
            color='faturamento_item',
            color_continuous_scale='Greens'
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            df_semana_agg, x='dia_nome', y='id_pedido',
            title="Pedidos por Dia da Semana",
            labels={'id_pedido': 'Pedidos', 'dia_nome': ''},
            color='id_pedido',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

# ============================================================
# 6. DISTRIBUIÇÃO POR HORÁRIO
# ============================================================
if mostrar['distribuicao_horario'] and not df_pedidos_filtrado.empty:
    st.subheader("Distribuição por Horário")

    df_hora = df_pedidos_filtrado.copy()
    df_hora['hora'] = df_hora['data_fechamento'].dt.hour
    df_hora_agg = df_hora.groupby('hora')['id_pedido'].nunique().reset_index(name='pedidos')

    fig = px.bar(
        df_hora_agg, x='hora', y='pedidos',
        title="Distribuição de Pedidos por Hora",
        labels={'hora': 'Hora do Dia', 'pedidos': 'Pedidos'},
        color='pedidos',
        color_continuous_scale='Oranges'
    )
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)
    st.divider()

# ============================================================
# 3. ORIGEM DE VENDA
# ============================================================
if mostrar['origem_venda'] and not df_pedidos_filtrado.empty:
    st.subheader("Origem de Venda")

    df_origem = df_pedidos_filtrado.copy()
    df_origem['faturamento_item'] = df_origem['valor_com_desconto'] + df_origem['taxa_entrega'] + df_origem['taxa_embalagem']

    df_origem_agg = df_origem.groupby('origem_venda').agg({
        'faturamento_item': 'sum',
        'id_pedido': 'nunique',
        'quantidade': 'sum'
    }).reset_index()
    df_origem_agg.columns = ['origem', 'faturamento', 'pedidos', 'itens']
    df_origem_agg['ticket_medio'] = df_origem_agg['faturamento'] / df_origem_agg['pedidos']

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_origem_agg, x='origem', y='faturamento',
            title="Faturamento por Origem",
            labels={'origem': '', 'faturamento': 'Faturamento (R$)'},
            color='origem',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            df_origem_agg, x='origem', y='ticket_medio',
            title="Ticket Médio por Origem",
            labels={'origem': '', 'ticket_medio': 'Ticket Médio (R$)'},
            color='origem',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()


# ============================================================
# 7. TOP PRODUTOS
# ============================================================
if mostrar['top_produtos'] and not df_pedidos_filtrado.empty:

    df_top = df_pedidos_filtrado.copy()
    df_top = df_top[df_top['status'] != 'cancelado']

    df_agg = df_top.groupby('nome_prod').agg({
        'quantidade': 'sum',
        'subtotal': 'sum',
        'categoria': 'first'
    }).reset_index()

    df_agg = df_agg.sort_values('subtotal', ascending=False).reset_index(drop=True)

    total_faturamento = df_agg['subtotal'].sum()

    # ---------- 7.1 PARETO ----------
    st.markdown("### Pareto de Faturamento")

    limiar_pareto = st.number_input(
        "Limiar (%):",
        min_value=1,
        max_value=100,
        value=80,
        step=5,
        key="pareto_limiar"
    )

    if total_faturamento <= 0:
        st.info("Sem faturamento no período.")
    else:
        df_pareto = df_agg.copy()
        df_pareto['perc_acumulado'] = (
            df_pareto['subtotal'].cumsum() / total_faturamento * 100
        ).round(2)

        corte = df_pareto[df_pareto['perc_acumulado'] <= limiar_pareto]
        qtd_itens_corte = len(corte) + 1 if len(corte) < len(df_pareto) else len(df_pareto)

        st.caption(
            f"**{qtd_itens_corte}** produtos representam **{limiar_pareto}%** do faturamento "
            f"(de {len(df_pareto)} no total)."
        )

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Bar(
                x=df_pareto['nome_prod'],
                y=df_pareto['subtotal'],
                name="Faturamento",
                marker_color='#3498db'
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(
                x=df_pareto['nome_prod'],
                y=df_pareto['perc_acumulado'],
                name="% Acumulado",
                mode='lines+markers',
                line=dict(color='#f39c12', width=2)
            ),
            secondary_y=True,
        )

        fig.add_hline(
            y=limiar_pareto,
            line_dash="dash",
            line_color="#e74c3c",
            annotation_text=f"{limiar_pareto}%",
            annotation_position="top left",
            secondary_y=True
        )

        fig.update_layout(
            title=f"Curva de Pareto — Limiar {limiar_pareto}%",
            xaxis_title="Produto",
            hovermode='x unified',
            height=450,
            showlegend=True
        )
        fig.update_yaxes(title_text="Faturamento (R$)", secondary_y=False)
        fig.update_yaxes(
            title_text="% Acumulado",
            secondary_y=True,
            range=[0, 105]
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---------- 7.2 TOP 10 GERAL ----------
    st.markdown("### 🏆 Top 10 Geral")

    col1, col2 = st.columns(2)

    with col1:
        top_qtd = df_agg.sort_values('quantidade', ascending=False).head(10)

        fig = px.bar(
            top_qtd, x='quantidade', y='nome_prod',
            title="Top 10 Produtos Mais Vendidos",
            labels={'quantidade': 'Quantidade', 'nome_prod': ''},
            orientation='h',
            color='quantidade',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top_fat = df_agg.sort_values('subtotal', ascending=False).head(10)

        fig = px.bar(
            top_fat, x='subtotal', y='nome_prod',
            title="Top 10 Produtos com Maior Faturamento",
            labels={'subtotal': 'Faturamento (R$)', 'nome_prod': ''},
            orientation='h',
            color='subtotal',
            color_continuous_scale='Plasma'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---------- 7.2 FATURAMENTO POR CATEGORIA ----------
    st.markdown("### Faturamento por Categoria")

    df_cat = df_top[df_top['categoria'].notna() & (df_top['categoria'] != '')].copy()

    if df_cat.empty:
        st.info("Nenhum dado de categoria disponível.")
    else:
        df_cat_agg = df_cat.groupby('categoria').agg({
            'subtotal': 'sum',
            'quantidade': 'sum'
        }).reset_index().sort_values('subtotal', ascending=False)

        total_cat = df_cat_agg['subtotal'].sum()
        df_cat_agg['percentual'] = (df_cat_agg['subtotal'] / total_cat * 100).round(1)

        fig = px.bar(
            df_cat_agg.sort_values('subtotal'),
            x='subtotal', y='categoria',
            orientation='h',
            title="Faturamento por Categoria",
            labels={'subtotal': 'Faturamento (R$)', 'categoria': ''},
            color='subtotal',
            color_continuous_scale='Teal',
            text=df_cat_agg.sort_values('subtotal')['percentual'].apply(lambda x: f"{x:.1f}%")
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(height=max(400, len(df_cat_agg) * 40), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---------- 7.4 CONCENTRAÇÃO POR CATEGORIA ----------
    st.markdown("### 🎯 Concentração por Categoria")

    if df_cat.empty:
        st.info("Nenhum dado de categoria disponível.")
    else:
        linhas_concentracao = []

        for cat in df_cat_agg['categoria'].tolist():
            subset = df_cat[df_cat['categoria'] == cat]
            subset_agg = subset.groupby('nome_prod').agg({
                'subtotal': 'sum',
                'quantidade': 'sum'
            }).reset_index().sort_values('subtotal', ascending=False)

            total_cat_item = subset_agg['subtotal'].sum()
            n_produtos = len(subset_agg)

            if total_cat_item <= 0:
                continue

            lider = subset_agg.iloc[0]
            fat_lider = lider['subtotal']
            conc_top1 = fat_lider / total_cat_item * 100

            top3 = subset_agg.head(3)
            conc_top3 = top3['subtotal'].sum() / total_cat_item * 100

            if conc_top1 >= 50:
                sinal = "🔴"
            elif conc_top1 >= 30:
                sinal = "🟡"
            else:
                sinal = "🟢"

            linhas_concentracao.append({
                'Categoria': cat,
                'Nº Produtos': n_produtos,
                'Faturamento': f"R$ {total_cat_item:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                'Líder': lider['nome_prod'],
                'Fat. Líder': f"R$ {fat_lider:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                'Conc. Top 1': f"{sinal} {conc_top1:.1f}%",
                'Conc. Top 3': f"{conc_top3:.1f}%",
            })

        if linhas_concentracao:
            st.dataframe(
                pd.DataFrame(linhas_concentracao),
                use_container_width=True,
                hide_index=True
            )

            alertas = [
                l['Categoria'] for l in linhas_concentracao
                if l['Conc. Top 1'].startswith('🔴')
            ]

            if alertas:
                st.warning(
                    f"⚠️ **Atenção:** {', '.join(alertas)} "
                    f"{'tem' if len(alertas) == 1 else 'têm'} mais de 50% "
                    f"do faturamento concentrado em 1 produto."
                )

    st.divider()


# ============================================================
# 8. ANÁLISE POR GARÇOM
# ============================================================
if mostrar['analise_garcom'] and not df_mesas_filtrado.empty:
    st.subheader("Análise por Garçom")

    df_garcom = df_mesas_filtrado.copy()
    df_garcom = df_garcom[df_garcom['garcom'].notna() & (df_garcom['garcom'] != '')]

    if not df_garcom.empty:
        df_garcom_agg = df_garcom.groupby('garcom').agg({
            'valor_total': 'sum',
            'id_mesa': 'count',
            'qtd_clientes': 'sum'
        }).reset_index()
        df_garcom_agg['ticket_medio'] = df_garcom_agg['valor_total'] / df_garcom_agg['id_mesa']

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                df_garcom_agg, x='garcom', y='valor_total',
                title="Faturamento por Garçom",
                labels={'valor_total': 'Faturamento (R$)', 'garcom': ''},
                color='valor_total',
                color_continuous_scale='Teal'
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                df_garcom_agg, x='garcom', y='ticket_medio',
                title="Ticket Médio por Garçom",
                labels={'ticket_medio': 'Ticket Médio (R$)', 'garcom': ''},
                color='ticket_medio',
                color_continuous_scale='Purples'
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado de garçom disponível.")

    st.divider()


# ============================================================
# 9. COMPOSIÇÃO POR CATEGORIA
# # ============================================================
# if mostrar['analise_categoria'] and not df_pedidos_filtrado.empty:
#     st.subheader("Composição do Faturamento por Categoria")

#     df_cat = df_pedidos_filtrado.copy()
#     df_cat = df_cat[df_cat['categoria'].notna() & (df_cat['categoria'] != '')]

#     if not df_cat.empty:
#         df_cat_agg = df_cat.groupby('categoria').agg({
#             'subtotal': 'sum',
#             'quantidade': 'sum'
#         }).reset_index().sort_values('subtotal', ascending=False)

#         total_geral = df_cat_agg['subtotal'].sum()
#         df_cat_agg['percentual'] = (df_cat_agg['subtotal'] / total_geral * 100) if total_geral > 0 else 0

#         fig = px.bar(
#             df_cat_agg.sort_values('subtotal'),
#             x='subtotal', y='categoria',
#             orientation='h',
#             title="Faturamento por Categoria",
#             labels={'subtotal': 'Faturamento (R$)', 'categoria': ''},
#             color='subtotal',
#             color_continuous_scale='Viridis',
#             text=df_cat_agg.sort_values('subtotal')['percentual'].apply(lambda x: f"{x:.1f}%")
#         )
#         fig.update_traces(textposition='outside')
#         fig.update_layout(height=max(400, len(df_cat_agg) * 30))
#         st.plotly_chart(fig, use_container_width=True)

#         # st.dataframe(
#         #     df_cat_agg[['categoria', 'subtotal', 'quantidade', 'percentual']],
#         #     column_config={
#         #         'categoria': 'Categoria',
#         #         'subtotal': st.column_config.NumberColumn('Faturamento', format="R$ %.2f"),
#         #         'quantidade': 'Qtd',
#         #         'percentual': st.column_config.NumberColumn('% do Total', format="%.2f%%"),
#         #     },
#         #     use_container_width=True,
#         #     hide_index=True
#         # )
#     else:
#         st.info("Nenhum dado de categoria disponível.")

#     st.divider()


# ============================================================
# 10. MENU vs BAR vs BALCÃO
# ============================================================
if mostrar['menu_vs_bar'] and not df_pedidos_filtrado.empty:
    st.subheader("Menu vs Bar vs Balcão")

    df_tv = df_pedidos_filtrado.copy()

    mapa_tipo = {
        'menu': 'Cozinha (Menu)',
        'bar': 'Bar',
        'caixa': 'Balcão',
    }

    if 'tipo_venda' in df_tv.columns:
        df_tv['tipo_grupo'] = df_tv['tipo_venda'].map(mapa_tipo).fillna(df_tv['tipo_venda'])

        df_tv_agg = df_tv.groupby('tipo_grupo').agg({
            'subtotal': 'sum',
            'id_pedido': 'nunique',
            'quantidade': 'sum'
        }).reset_index()
        df_tv_agg.columns = ['tipo_grupo', 'faturamento', 'pedidos', 'itens']
        df_tv_agg = df_tv_agg.sort_values('faturamento', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                df_tv_agg, x='tipo_grupo', y='faturamento',
                title="Faturamento por Tipo de Venda",
                labels={'tipo_grupo': '', 'faturamento': 'Faturamento (R$)'},
                color='tipo_grupo',
                color_discrete_sequence=px.colors.qualitative.Set2,
                text='faturamento'
            )
            fig.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                df_tv_agg, x='tipo_grupo', y='itens',
                title="Itens Vendidos por Tipo",
                labels={'tipo_grupo': '', 'itens': 'Itens'},
                color='tipo_grupo',
                color_discrete_sequence=px.colors.qualitative.Set2,
                text='itens'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    #     st.markdown("**Top 10 Categorias por Faturamento (colorido por tipo)**")

    #     df_cat_tipo = df_tv[df_tv['categoria'].notna() & (df_tv['categoria'] != '')].copy()
    #     df_cat_tipo_agg = df_cat_tipo.groupby(['categoria', 'tipo_grupo']).agg({
    #         'subtotal': 'sum'
    #     }).reset_index().sort_values('subtotal', ascending=False).head(10)

    #     fig = px.bar(
    #         df_cat_tipo_agg.sort_values('subtotal'),
    #         x='subtotal', y='categoria',
    #         orientation='h',
    #         color='tipo_grupo',
    #         title="Top 10 Categorias por Faturamento",
    #         labels={'subtotal': 'Faturamento (R$)', 'categoria': '', 'tipo_grupo': 'Tipo'},
    #         color_discrete_sequence=px.colors.qualitative.Set2,
    #         text='subtotal'
    #     )
    #     fig.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
    #     fig.update_layout(height=max(400, len(df_cat_tipo_agg) * 40))
    #     st.plotly_chart(fig, use_container_width=True)
    # else:
    #     st.info("Coluna 'tipo_venda' não disponível nos pedidos.")

    # st.divider()

# ============================================================
# 11. ANÁLISE POR CLIENTE
# ============================================================
if mostrar['analise_cliente'] and not df_pedidos_filtrado.empty:
    st.subheader("Análise por Cliente")

    df_cli = df_pedidos_filtrado.copy()
    df_cli = df_cli[df_cli['id_cliente'].notna() & (df_cli['id_cliente'] != '')]

    if not df_cli.empty:
        df_cli_agg = df_cli.groupby('id_cliente').agg({
            'valor_com_desconto': 'sum',
            'id_pedido': 'nunique',
            'quantidade': 'sum'
        }).reset_index()
        df_cli_agg.columns = ['id_cliente', 'faturamento', 'pedidos', 'itens']
        df_cli_agg['ticket_medio'] = df_cli_agg['faturamento'] / df_cli_agg['pedidos']

        if not df_clientes.empty:
            df_cli_agg = df_cli_agg.merge(
                df_clientes[['id_cliente', 'nome_cliente', 'bairro']],
                on='id_cliente',
                how='left'
            )
            df_cli_agg['nome_cliente'] = df_cli_agg['nome_cliente'].fillna(df_cli_agg['id_cliente'])
        else:
            df_cli_agg['nome_cliente'] = df_cli_agg['id_cliente']
            df_cli_agg['bairro'] = ''

        top10 = df_cli_agg.nlargest(10, 'faturamento')

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                top10, x='faturamento', y='nome_cliente',
                title="Top 10 Clientes por Faturamento",
                labels={'faturamento': 'Faturamento (R$)', 'nome_cliente': ''},
                orientation='h',
                color='faturamento',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            top10_pedidos = df_cli_agg.nlargest(10, 'pedidos')
            fig = px.bar(
                top10_pedidos, x='pedidos', y='nome_cliente',
                title="Top 10 Clientes por Nº de Pedidos",
                labels={'pedidos': 'Pedidos', 'nome_cliente': ''},
                orientation='h',
                color='pedidos',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado de cliente disponível.")

    st.divider()


# ============================================================
# 12. ANÁLISE POR BAIRRO
# ============================================================
if mostrar['analise_bairro'] and not df_pedidos_filtrado.empty and not df_clientes.empty:
    st.subheader("Análise por Bairro")

    df_bairro = df_pedidos_filtrado.copy()
    df_bairro = df_bairro[df_bairro['id_cliente'].notna() & (df_bairro['id_cliente'] != '')]

    df_bairro = df_bairro.merge(
        df_clientes[['id_cliente', 'bairro']],
        on='id_cliente',
        how='left'
    )
    df_bairro = df_bairro[df_bairro['bairro'].notna() & (df_bairro['bairro'] != '')]

    if not df_bairro.empty:
        df_bairro_agg = df_bairro.groupby('bairro').agg({
            'valor_com_desconto': 'sum',
            'id_pedido': 'nunique',
            'id_cliente': 'nunique'
        }).reset_index()
        df_bairro_agg.columns = ['bairro', 'faturamento', 'pedidos', 'clientes']
        df_bairro_agg['ticket_medio'] = df_bairro_agg['faturamento'] / df_bairro_agg['pedidos']
        df_bairro_agg = df_bairro_agg.sort_values('faturamento', ascending=False)

        fig = px.bar(
            df_bairro_agg.head(15), x='faturamento', y='bairro',
            title="Top 15 Bairros por Faturamento",
            labels={'faturamento': 'Faturamento (R$)', 'bairro': ''},
            orientation='h',
            color='faturamento',
            color_continuous_scale='Oranges'
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        # st.dataframe(
        #     df_bairro_agg,
        #     column_config={
        #         'bairro': 'Bairro',
        #         'faturamento': st.column_config.NumberColumn('Faturamento', format="R$ %.2f"),
        #         'pedidos': 'Pedidos',
        #         'clientes': 'Clientes',
        #         'ticket_medio': st.column_config.NumberColumn('Ticket Médio', format="R$ %.2f"),
        #     },
        #     use_container_width=True,
        #     hide_index=True
        # )
    else:
        st.info("Nenhum dado de bairro disponível.")

    st.divider()


# ============================================================
# 13. MEIOS DE PAGAMENTO
# ============================================================
if mostrar['analise_pagamento'] and not df_pedidos_filtrado.empty:
    st.subheader("Meios de Pagamento")

    df_pag = df_pedidos_filtrado.copy()
    df_pag = df_pag[df_pag['metodo_pagamento'].notna() & (df_pag['metodo_pagamento'] != '')]

    if not df_pag.empty:
        df_pag_agg = df_pag.groupby('metodo_pagamento').agg({
            'valor_com_desconto': 'sum',
            'id_pedido': 'nunique'
        }).reset_index()
        df_pag_agg.columns = ['metodo', 'faturamento', 'pedidos']
        df_pag_agg['ticket_medio'] = df_pag_agg['faturamento'] / df_pag_agg['pedidos']

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                df_pag_agg.sort_values('faturamento', ascending=False),
                x='metodo', y='faturamento',
                title="Faturamento por Método",
                labels={'metodo': '', 'faturamento': 'Faturamento (R$)'},
                color='metodo',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                df_pag_agg.sort_values('faturamento', ascending=False),
                x='metodo', y='ticket_medio',
                title="Ticket Médio por Método",
                labels={'metodo': '', 'ticket_medio': 'Ticket Médio (R$)'},
                color='metodo',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado de pagamento disponível.")

    st.divider()


# ============================================================
# 14. ANÁLISE DE DELIVERY
# ============================================================
if mostrar['analise_delivery']:
    st.subheader("Análise de Delivery")

    df_delivery = carregar_pkl("data/delivery.pkl")

    if df_delivery is None or (isinstance(df_delivery, list) and not df_delivery):
        st.info("Nenhum dado de delivery disponível.")
    else:
        df_del = pd.DataFrame(df_delivery) if isinstance(df_delivery, list) else df_delivery

        if df_del.empty:
            st.info("Nenhum dado de delivery disponível.")
        else:
            df_del['criado_dt'] = pd.to_datetime(df_del['criado_em'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
            df_del['pronto_dt'] = pd.to_datetime(df_del['pronto_em'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
            df_del['saiu_dt'] = pd.to_datetime(df_del['saiu_entrega_em'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
            df_del['entregue_dt'] = pd.to_datetime(df_del['entregue_em'], format="%d/%m/%Y %H:%M:%S", errors='coerce')

            df_del_periodo = filtrar_por_periodo(df_del, 'criado_dt', periodo)

            if not df_del_periodo.empty:
                df_del_periodo = df_del_periodo.copy()
                df_del_periodo['tempo_producao'] = (df_del_periodo['pronto_dt'] - df_del_periodo['criado_dt']).dt.total_seconds() / 60
                df_del_periodo['tempo_rota'] = (df_del_periodo['entregue_dt'] - df_del_periodo['saiu_dt']).dt.total_seconds() / 60
                df_del_periodo['tempo_total'] = (df_del_periodo['entregue_dt'] - df_del_periodo['criado_dt']).dt.total_seconds() / 60

                total_del = len(df_del_periodo)
                entregues = df_del_periodo[df_del_periodo['status_entrega'] == 'entregue']
                cancelados = df_del_periodo[df_del_periodo['status_entrega'] == 'cancelado']

                tempo_medio_prod = entregues['tempo_producao'].mean() if not entregues.empty else 0
                tempo_medio_rota = entregues['tempo_rota'].mean() if not entregues.empty else 0
                tempo_medio_total = entregues['tempo_total'].mean() if not entregues.empty else 0
                taxa_cancelamento = len(cancelados) / total_del * 100 if total_del > 0 else 0

                metricas_del = [
                    {'label': 'Total Entregas', 'valor': f"{total_del}", 'cor': '#3498db'},
                    {'label': 'Tempo Médio Produção', 'valor': f"{tempo_medio_prod:.1f} min", 'cor': '#f39c12'},
                    {'label': 'Tempo Médio Rota', 'valor': f"{tempo_medio_rota:.1f} min", 'cor': '#9b59b6'},
                    {'label': 'Tempo Médio Total', 'valor': f"{tempo_medio_total:.1f} min", 'cor': '#2ecc71'},
                    {'label': 'Taxa Cancelamento', 'valor': f"{taxa_cancelamento:.1f}%", 'cor': '#e74c3c'},
                ]
                st.html(card_metricas_html(metricas_del))

                motoboys = entregues[entregues['motoboy'].notna() & (entregues['motoboy'] != '')]
                if not motoboys.empty:
                    df_motoboy_agg = motoboys.groupby('motoboy').agg({
                        'id_pedido': 'count',
                        'tempo_rota': 'mean'
                    }).reset_index()
                    df_motoboy_agg.columns = ['motoboy', 'entregas', 'tempo_medio_rota']
                    df_motoboy_agg = df_motoboy_agg.sort_values('entregas', ascending=False).head(10)

                    col1, col2 = st.columns(2)

                    with col1:
                        fig = px.bar(
                            df_motoboy_agg, x='entregas', y='motoboy',
                            title="Top 10 Motoboys por Entregas",
                            labels={'entregas': 'Entregas', 'motoboy': ''},
                            orientation='h',
                            color='entregas',
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        fig = px.bar(
                            df_motoboy_agg, x='tempo_medio_rota', y='motoboy',
                            title="Tempo Médio de Rota por Motoboy",
                            labels={'tempo_medio_rota': 'Minutos', 'motoboy': ''},
                            orientation='h',
                            color='tempo_medio_rota',
                            color_continuous_scale='Reds'
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)

                df_del_periodo['dia'] = df_del_periodo['criado_dt'].dt.date
                df_del_dia = df_del_periodo.groupby('dia').size().reset_index(name='entregas')

                fig = px.bar(
                    df_del_dia, x='dia', y='entregas',
                    title="Entregas por Dia",
                    labels={'dia': 'Data', 'entregas': 'Entregas'},
                    color='entregas',
                    color_continuous_scale='Oranges'
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum delivery no período.")

    st.divider()


# ============================================================
# 15. ANÁLISE FINANCEIRA
# ============================================================
if mostrar['analise_financeira']:
    st.subheader("Análise Financeira")

    if not df_pedidos_filtrado.empty:
        df_fin = df_pedidos_filtrado.copy()

        faturamento_bruto = df_fin['subtotal'].sum()
        faturamento_liquido = df_fin['valor_com_desconto'].sum()
        taxa_entrega = df_fin['taxa_entrega'].sum() if 'taxa_entrega' in df_fin.columns else 0
        taxa_embalagem = df_fin['taxa_embalagem'].sum() if 'taxa_embalagem' in df_fin.columns else 0
        descontos = faturamento_bruto - faturamento_liquido

        faturamento_total = faturamento_liquido + taxa_entrega + taxa_embalagem

        cortesia_total = 0
        devolucao_total = 0
        promo_total = 0

        if 'desconto_tipo' in df_fin.columns:
            cortesia_total = df_fin[df_fin['desconto_tipo'] == 'cortesia']['subtotal'].sum()
            devolucao_total = df_fin[df_fin['desconto_tipo'] == 'devolucao']['subtotal'].sum()
            promo_total = df_fin[df_fin['desconto_tipo'] == 'promo']['subtotal'].sum()

        metricas_fin = [
            {'label': 'Faturamento Total', 'valor': f"R$ {faturamento_total:,.2f}", 'cor': '#2ecc71'},
            {'label': 'Faturamento Bruto', 'valor': f"R$ {faturamento_bruto:,.2f}", 'cor': '#3498db'},
            {'label': 'Descontos', 'valor': f"R$ {descontos:,.2f}", 'cor': '#e74c3c'},
            {'label': 'Taxa Entrega', 'valor': f"R$ {taxa_entrega:,.2f}", 'cor': '#f39c12'},
            {'label': 'Taxa Embalagem', 'valor': f"R$ {taxa_embalagem:,.2f}", 'cor': '#9b59b6'},
        ]
        st.html(card_metricas_html(metricas_fin))

        if cortesia_total > 0 or devolucao_total > 0 or promo_total > 0:
            metricas_desc = [
                {'label': 'Cortesias', 'valor': f"R$ {cortesia_total:,.2f}", 'cor': '#f39c12'},
                {'label': 'Devoluções', 'valor': f"R$ {devolucao_total:,.2f}", 'cor': '#e74c3c'},
                {'label': 'Promoções', 'valor': f"R$ {promo_total:,.2f}", 'cor': '#9b59b6'},
            ]
            st.html(card_metricas_html(metricas_desc))

    st.divider()


# ============================================================
# 16. ANÁLISE DE COVER E 10%
# ============================================================
if mostrar['analise_cover'] and not df_mesas_filtrado.empty:
    st.subheader("Análise de Cover e 10%")

    df_cover = df_mesas_filtrado.copy()
    df_cover['cover_total'] = df_cover['cover'] * df_cover['qtd_clientes']

    cover_total = df_cover['cover_total'].sum()
    valor_10_total = df_cover['valor_10'].sum() if 'valor_10' in df_cover.columns else 0
    media_cover = cover_total / len(df_cover) if len(df_cover) > 0 else 0

    metricas_cover = [
        {'label': 'Total Cover', 'valor': f"R$ {cover_total:,.2f}", 'cor': '#f39c12'},
        {'label': 'Total 10% Garçom', 'valor': f"R$ {valor_10_total:,.2f}", 'cor': '#9b59b6'},
        {'label': 'Média Cover por Mesa', 'valor': f"R$ {media_cover:.2f}", 'cor': '#3498db'},
    ]
    st.html(card_metricas_html(metricas_cover))

    col1, col2 = st.columns(2)

    with col1:
        df_cover_dia = df_cover.groupby(df_cover['fechado_em'].dt.date)['cover_total'].sum().reset_index()
        fig = px.bar(
            df_cover_dia, x='fechado_em', y='cover_total',
            title="Cover por Dia",
            labels={'fechado_em': 'Data', 'cover_total': 'Cover (R$)'},
            color='cover_total',
            color_continuous_scale='Oranges'
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'valor_10' in df_cover.columns:
            df_10_dia = df_cover.groupby(df_cover['fechado_em'].dt.date)['valor_10'].sum().reset_index()
            fig = px.bar(
                df_10_dia, x='fechado_em', y='valor_10',
                title="10% Garçom por Dia",
                labels={'fechado_em': 'Data', 'valor_10': '10% (R$)'},
                color='valor_10',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()


# ============================================================
# 17. ANÁLISE DO CAIXA
# ============================================================
if mostrar['analise_caixa']:
    st.subheader("Análise do Caixa")

    if df_caixa.empty:
        st.info("Nenhum histórico de caixa disponível.")
    else:
        df_cx = df_caixa.copy()
        df_cx['data_dt'] = pd.to_datetime(df_cx['data_fechamento'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
        df_cx = df_cx[df_cx['data_dt'] >= (datetime.now() - timedelta(days=periodo))]

        total_dias = len(df_cx)
        total_vendas = df_cx['vendas_mesa'].sum() + df_cx['vendas_balcao'].sum() + df_cx['vendas_delivery'].sum() + df_cx['vendas_takeaway'].sum() if not df_cx.empty else 0

        media_mesa = df_cx['vendas_mesa'].mean() if not df_cx.empty else 0
        media_balcao = df_cx['vendas_balcao'].mean() if not df_cx.empty else 0
        media_takeaway = df_cx['vendas_takeaway'].mean() if not df_cx.empty else 0
        media_delivery = df_cx['vendas_delivery'].mean() if not df_cx.empty else 0

        metricas_caixa = [
            {'label': 'Dias no Período', 'valor': f"{total_dias}", 'cor': '#3498db'},
            {'label': 'Total Vendas', 'valor': f"R$ {total_vendas:,.2f}", 'cor': '#2ecc71'},
            {'label': 'Média/Dia', 'valor': f"R$ {total_vendas/total_dias if total_dias else 0:,.2f}", 'cor': '#f39c12'},
            {'label': 'Média Mesa/Dia', 'valor': f"R$ {media_mesa:,.2f}", 'cor': '#9b59b6'},
            {'label': 'Média Delivery/Dia', 'valor': f"R$ {media_delivery:,.2f}", 'cor': '#e74c3c'},
        ]
        st.html(card_metricas_html(metricas_caixa))

        col1, col2 = st.columns(2)

        with col1:
            categorias = pd.DataFrame({
                'Categoria': ['Mesa', 'Balcão', 'Takeaway', 'Delivery'],
                'Média': [media_mesa, media_balcao, media_takeaway, media_delivery]
            })
            fig = px.bar(
                categorias, x='Categoria', y='Média',
                title="Média de Vendas por Categoria (por dia)",
                labels={'Média': 'Média (R$)'},
                color='Categoria',
                color_discrete_sequence=['#2ecc71', '#3498db', '#f39c12', '#9b59b6']
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            vendas_metodo = {}
            for row in df_cx['vendas_metodo']:
                if isinstance(row, dict):
                    for metodo, valor in row.items():
                        vendas_metodo[metodo] = vendas_metodo.get(metodo, 0) + valor

            if vendas_metodo:
                vendas_metodo_media = {k: v / len(df_cx) for k, v in vendas_metodo.items()}
                df_vendas_met = pd.DataFrame(vendas_metodo_media.items(), columns=['Método', 'Média'])
                fig = px.bar(
                    df_vendas_met, x='Método', y='Média',
                    title="Média de Vendas por Método de Pagamento",
                    labels={'Média': 'Média (R$)'},
                    color='Método',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

    st.divider()


# ============================================================
# 18. COMPARATIVO MÊS ATUAL vs ANTERIOR
# ============================================================
# if mostrar['comparativo_mes'] and not df_pedidos.empty:
#     st.subheader("Comparativo Mês Atual vs Mês Anterior")

#     hoje = datetime.now()
#     inicio_mes_atual = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#     inicio_mes_anterior = (inicio_mes_atual - timedelta(days=1)).replace(day=1)

#     df_pedidos_dt = df_pedidos.copy()
#     df_pedidos_dt['data_fechamento'] = pd.to_datetime(df_pedidos_dt['data_fechamento'], errors='coerce')

#     df_mes_atual = df_pedidos_dt[df_pedidos_dt['data_fechamento'] >= inicio_mes_atual]
#     df_mes_anterior = df_pedidos_dt[
#         (df_pedidos_dt['data_fechamento'] >= inicio_mes_anterior) &
#         (df_pedidos_dt['data_fechamento'] < inicio_mes_atual)
#     ]

#     fat_atual = df_mes_atual['valor_com_desconto'].sum() + df_mes_atual['taxa_entrega'].sum() + df_mes_atual['taxa_embalagem'].sum()
#     fat_anterior = df_mes_anterior['valor_com_desconto'].sum() + df_mes_anterior['taxa_entrega'].sum() + df_mes_anterior['taxa_embalagem'].sum()

#     ped_atual = df_mes_atual['id_pedido'].nunique()
#     ped_anterior = df_mes_anterior['id_pedido'].nunique()

#     var_fat = ((fat_atual - fat_anterior) / fat_anterior * 100) if fat_anterior > 0 else 0
#     var_ped = ((ped_atual - ped_anterior) / ped_anterior * 100) if ped_anterior > 0 else 0

#     col1, col2 = st.columns(2)

#     with col1:
#         delta_fat = f"{var_fat:+.1f}% vs mês anterior"
#         st.metric("Faturamento Mês Atual", f"R$ {fat_atual:,.2f}", delta=delta_fat)

#     with col2:
#         delta_ped = f"{var_ped:+.1f}% vs mês anterior"
#         st.metric("Pedidos Mês Atual", f"{ped_atual}", delta=delta_ped)

#     comparativo = pd.DataFrame({
#         'Mês': ['Anterior', 'Atual'],
#         'Faturamento': [fat_anterior, fat_atual],
#         'Pedidos': [ped_anterior, ped_atual]
#     })

#     fig = make_subplots(specs=[[{"secondary_y": True}]])

#     fig.add_trace(
#         go.Bar(x=comparativo['Mês'], y=comparativo['Faturamento'], name="Faturamento", marker_color='#2ecc71'),
#         secondary_y=False,
#     )
#     fig.add_trace(
#         go.Scatter(x=comparativo['Mês'], y=comparativo['Pedidos'], name="Pedidos", mode='lines+markers', line=dict(color='#3498db')),
#         secondary_y=True,
#     )

#     fig.update_layout(height=400, hovermode='x unified', title="Comparativo Mensal")
#     fig.update_yaxes(title_text="Faturamento (R$)", secondary_y=False)
#     fig.update_yaxes(title_text="Pedidos", secondary_y=True)

#     st.plotly_chart(fig, use_container_width=True)
#     st.divider()


# ============================================================
# 19. ANÁLISE DE ESTOQUE
# ============================================================
# ============================================================
# 19. ANÁLISE DE ESTOQUE
# ============================================================
if mostrar['analise_estoque']:
    st.subheader("Análise de Estoque")

    from utils.movimentacoes_utils import (
        carregar_movimentacoes,
        calcular_estoque_atual,
        custo_medio_por_insumo,
    )

    insumos = carregar_pkl("data/insumos.pkl")
    df_mov = carregar_movimentacoes()

    if df_mov.empty or insumos is None:
        st.info("Nenhum dado de estoque disponível.")
    else:
        df_insumos = pd.DataFrame(insumos) if not isinstance(insumos, pd.DataFrame) else insumos

        df_mov = df_mov.copy()
        df_mov['data_mov_dt'] = pd.to_datetime(
            df_mov['data_movimentacao'],
            format="%d/%m/%Y %H:%M:%S",
            errors='coerce'
        )

        df_estoque = calcular_estoque_atual()
        df_custo = custo_medio_por_insumo()

        df_est = df_insumos[['id_insumo', 'nome', 'unidade_compra']].copy()
        df_est = df_est.merge(df_estoque, on='id_insumo', how='left')
        df_est = df_est.merge(df_custo, on='id_insumo', how='left')

        df_est['estoque'] = df_est['estoque'].fillna(0.0)
        df_est['custo_medio'] = df_est['custo_medio'].fillna(0.0)
        df_est['valor_estoque'] = df_est['estoque'] * df_est['custo_medio']

        hoje = datetime.now()
        data_corte = hoje - timedelta(days=periodo)
        data_corte_7d = hoje - timedelta(days=7)

        df_periodo = df_mov[df_mov['data_mov_dt'] >= data_corte]
        df_vendas_7d = df_mov[
            (df_mov['tipo'] == 'venda') &
            (df_mov['data_mov_dt'] >= data_corte_7d)
        ]

        media_saida_7d = df_vendas_7d.groupby('id_insumo')['quantidade'].apply(
            lambda x: x.abs().sum() / 7
        ).reset_index()
        media_saida_7d.columns = ['id_insumo', 'media_saida_7d']

        ultima_venda = df_mov[df_mov['tipo'] == 'venda'].groupby('id_insumo')['data_mov_dt'].max().reset_index()
        ultima_venda.columns = ['id_insumo', 'ultima_venda']

        df_est = df_est.merge(media_saida_7d, on='id_insumo', how='left')
        df_est = df_est.merge(ultima_venda, on='id_insumo', how='left')

        df_est['media_saida_7d'] = df_est['media_saida_7d'].fillna(0.0)

        df_est['alerta_baixo'] = (
            (df_est['media_saida_7d'] > 0)
            & (df_est['estoque'] < df_est['media_saida_7d'])
        )

        df_est['alerta_obsoleto'] = (
            (df_est['estoque'] > 0)
            & (
                df_est['ultima_venda'].isna()
                | (df_est['ultima_venda'] < data_corte_7d)
            )
        )

        total_estoque = df_est['estoque'].sum()
        valor_total_estoque = df_est['valor_estoque'].sum()
        qtd_baixo = int(df_est['alerta_baixo'].sum())
        qtd_obsoleto = int(df_est['alerta_obsoleto'].sum())

        metricas_estoque = [
            {'label': 'Total Estoque', 'valor': f"{total_estoque:.1f} un", 'cor': '#3498db'},
            {'label': 'Valor Estoque', 'valor': f"R$ {valor_total_estoque:,.2f}", 'cor': '#2ecc71'},
            {'label': 'Insumos', 'valor': f"{len(df_est)}", 'cor': '#f39c12'},
            {'label': '⚠️ Estoque Baixo', 'valor': f"{qtd_baixo}", 'cor': '#e74c3c'},
            {'label': '🕒 Obsoletos', 'valor': f"{qtd_obsoleto}", 'cor': '#9b59b6'},
        ]
        st.html(card_metricas_html(metricas_estoque))

        st.divider()

        st.markdown("### Evolução do Estoque")

        if df_periodo.empty:
            st.info("Sem movimentações no período selecionado.")
        else:
            df_evo = df_periodo.copy()
            df_evo['dia'] = df_evo['data_mov_dt'].dt.date
            df_evo['delta'] = df_evo['quantidade']

            df_dia = df_evo.groupby(['dia', 'tipo'])['delta'].sum().unstack(fill_value=0).reset_index()

            for col in ['compra', 'venda', 'ajuste']:
                if col not in df_dia.columns:
                    df_dia[col] = 0.0

            df_dia['saldo_dia'] = df_dia['compra'] + df_dia['ajuste'] - df_dia['venda'].abs()

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=df_dia['dia'], y=df_dia['compra'],
                name='Compras', marker_color='#2ecc71'
            ))
            fig.add_trace(go.Bar(
                x=df_dia['dia'], y=-df_dia['venda'].abs(),
                name='Vendas', marker_color='#e74c3c'
            ))
            fig.add_trace(go.Bar(
                x=df_dia['dia'], y=df_dia['ajuste'],
                name='Ajustes', marker_color='#f39c12'
            ))

            fig.add_trace(go.Scatter(
                x=df_dia['dia'], y=df_dia['saldo_dia'].cumsum(),
                name='Saldo Acumulado',
                mode='lines+markers',
                line=dict(color='#3498db', width=3),
                yaxis='y2'
            ))

            fig.update_layout(
                title="Movimentações Diárias e Saldo Acumulado",
                xaxis_title="Data",
                yaxis_title="Movimentação (un)",
                yaxis2=dict(
                    title="Saldo Acumulado (un)",
                    overlaying='y',
                    side='right'
                ),
                barmode='relative',
                hovermode='x unified',
                height=450,
                legend=dict(orientation='h', yanchor='bottom', y=1.02)
            )

            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.markdown("### Ajustes por Motivo")

        df_ajustes = df_mov[df_mov['tipo'] == 'ajuste'].copy()
        df_ajustes = df_ajustes[df_ajustes['data_mov_dt'] >= data_corte]

        if df_ajustes.empty:
            st.info("Nenhum ajuste no período.")
        else:
            df_ajustes_agg = df_ajustes.groupby('motivo')['quantidade'].agg(
                total='sum',
                ocorrencias='count'
            ).reset_index()

            df_ajustes_agg['total'] = df_ajustes_agg['total'].round(3)

            fig = px.bar(
                df_ajustes_agg.sort_values('total'),
                x='total', y='motivo',
                orientation='h',
                title="Ajustes por Motivo",
                labels={'total': 'Quantidade (sinal)', 'motivo': ''},
                color='total',
                color_continuous_scale='RdBu',
                text='total'
            )
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig.update_layout(height=max(300, len(df_ajustes_agg) * 40))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.markdown("### ⚠️ Estoque Baixo (estoque < média de saída 7d)")

        df_baixo = df_est[df_est['alerta_baixo']].copy()
        if df_baixo.empty:
            st.success("Nenhum insumo com estoque baixo.")
        else:
            st.dataframe(
                df_baixo[['id_insumo', 'nome', 'unidade_compra', 'estoque', 'media_saida_7d']],
                column_config={
                    'id_insumo': 'ID',
                    'nome': 'Insumo',
                    'unidade_compra': 'Unid',
                    'estoque': st.column_config.NumberColumn('Estoque', format="%.2f"),
                    'media_saida_7d': st.column_config.NumberColumn('Saída Média 7d', format="%.2f"),
                },
                use_container_width=True,
                hide_index=True
            )

        st.markdown("### Estoque Obsoleto (sem venda há 7+ dias)")

        df_obs = df_est[df_est['alerta_obsoleto']].copy()
        if df_obs.empty:
            st.success("Nenhum insumo obsoleto.")
        else:
            df_obs['ultima_venda'] = df_obs['ultima_venda'].dt.strftime('%d/%m/%Y').fillna('Sem venda')
            st.dataframe(
                df_obs[['id_insumo', 'nome', 'unidade_compra', 'estoque', 'ultima_venda']],
                column_config={
                    'id_insumo': 'ID',
                    'nome': 'Insumo',
                    'unidade_compra': 'Unid',
                    'estoque': st.column_config.NumberColumn('Estoque', format="%.2f"),
                    'ultima_venda': 'Última Venda',
                },
                use_container_width=True,
                hide_index=True
            )

# ============================================================
# RODAPÉ
# ============================================================
st.caption(f"Dashboard atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | {periodo} dias de histórico")