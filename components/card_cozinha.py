import streamlit as st
from datetime import datetime


def _cor_origem(origem):
    return {
        'mesa': '#3498db',
        'takeaway': '#f39c12',
        'delivery': '#9b59b6',
        'caixa': '#16a085'
    }.get(str(origem).lower(), '#7f8c8d')


def _label_origem(origem):
    return {
        'mesa': 'Mesa',
        'takeaway': 'Takeaway',
        'delivery': 'Delivery',
        'caixa': 'Caixa'
    }.get(str(origem).lower(), str(origem).capitalize())


def _formata_valor(v):
    try:
        return f"R$ {float(v):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception:
        return "R$ 0,00"


def _linha_item(item):
    nome = item.get('nome_prod', '')
    qtd = int(item.get('quantidade', 1))
    valor = item.get('subtotal', 0)
    obs = item.get('observacao', '')

    obs_html = f'<div class="cz-obs">obs: {obs}</div>' if obs else ''

    return f"""
    <div class="cz-item">
        <div class="cz-item-info">
            <div class="cz-item-linha1">
                <span class="cz-qtd">{qtd}x</span>
                <span class="cz-prod">{nome}</span>
            </div>
            {obs_html}
        </div>
        <div class="cz-valor">{_formata_valor(valor)}</div>
    </div>
    """


def _renderizar_card_html(row, itens_pedido, filtro_status, cor_fundo_status):
    id_pedido = row['id_pedido']
    id_mesa = row.get('id_mesa', '') or ''
    origem = row.get('origem_venda', '')

    cor_origem = _cor_origem(origem)
    label_origem = _label_origem(origem)

    if id_mesa:
        badge_local = str(id_mesa)
    else:
        badge_local = label_origem

    itens_html = ''.join([_linha_item(item) for _, item in itens_pedido.iterrows()])

    total = row['subtotal']
    qtd_itens = len(itens_pedido)

    tempo_html = ''
    if filtro_status == 'Abertos' and row.get('tempo_formatado'):
        tempo_html = f'<span class="cz-tempo">⏱ {row["tempo_formatado"]}</span>'
    elif filtro_status != 'Abertos' and row.get('fechado_em'):
        tempo_html = f'<span class="cz-tempo">{row["fechado_em"]}</span>'

    label_status = filtro_status[:-1] if filtro_status.endswith('s') else filtro_status
    if filtro_status == 'Abertos':
        label_status = 'Aberto'

    return f"""
    <div class="cz-card">
        <div class="cz-header">
            <div class="cz-header-esq">
                <span class="cz-pedido">#{id_pedido}</span>
                <span class="cz-badge" style="background:{cor_origem};">{badge_local}</span>
            </div>
            <div class="cz-header-dir">
                {tempo_html}
                <span class="cz-status-badge" style="background:{cor_fundo_status};">{label_status}</span>
            </div>
        </div>

        <div class="cz-itens">
            {itens_html}
        </div>

        <div class="cz-footer">
            <span>{qtd_itens} item(ns)</span>
            <span class="cz-footer-total">Total: {_formata_valor(total)}</span>
        </div>
    </div>
    """


def renderizar_card_cozinha(df, filtro_status):
    if df.empty:
        st.info(f"Nenhum pedido {filtro_status.lower()} no momento.")
        return

    cor_fundo_status = {
        'Abertos': '#f39c12',
        'Fechados': '#2ecc71',
        'Cancelados': '#e74c3c'
    }.get(filtro_status, '#7f8c8d')

    agg_map = {
        'id_mesa': 'first',
        'origem_venda': 'first',
        'subtotal': 'sum',
        'quantidade': 'sum',
    }
    if 'tempo_formatado' in df.columns:
        agg_map['tempo_formatado'] = 'first'
    if 'fechado_em' in df.columns:
        agg_map['fechado_em'] = 'first'

    pedidos_agrupados = df.groupby('id_pedido', sort=False).agg(agg_map).reset_index()

    st.html("""
    <style>
        .cz-wrap {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .cz-card {
            background: #181818;
            border: 1px solid #303030;
            border-radius: 12px;
            overflow: hidden;
            width: 100%;
        }
        .cz-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            background: #202020;
            border-bottom: 1px solid #303030;
            flex-wrap: wrap;
            gap: 6px;
        }
        .cz-header-esq {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .cz-pedido {
            font-size: 13px;
            font-weight: 800;
            color: #f1f3f5;
        }
        .cz-badge {
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 10px;
            font-weight: 700;
            color: #fff;
        }
        .cz-header-dir {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 10px;
            color: #aaa;
        }
        .cz-tempo {
            background: #2a2a2a;
            padding: 2px 7px;
            border-radius: 999px;
            color: #ffd700;
            font-weight: 700;
            font-size: 10px;
        }
        .cz-status-badge {
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 9px;
            font-weight: 700;
            color: #000;
        }
        .cz-itens {
            padding: 4px 12px;
        }
        .cz-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #292929;
        }
        .cz-item:last-child {
            border-bottom: none;
        }
        .cz-item-info {
            display: flex;
            flex-direction: column;
            min-width: 0;
            flex: 1;
        }
        .cz-item-linha1 {
            display: flex;
            align-items: baseline;
            gap: 6px;
        }
        .cz-qtd {
            color: #ffd700;
            font-size: 11px;
            font-weight: 700;
        }
        .cz-prod {
            color: #f1f3f5;
            font-size: 12px;
            font-weight: 600;
            line-height: 1.3;
            overflow-wrap: anywhere;
        }
        .cz-obs {
            margin-top: 2px;
            font-size: 10px;
            color: #9da3ad;
            font-style: italic;
        }
        .cz-valor {
            font-size: 12px;
            font-weight: 700;
            color: #2ecc71;
            white-space: nowrap;
            padding-left: 8px;
        }
        .cz-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            background: #202020;
            border-top: 1px solid #303030;
            font-size: 11px;
            color: #858b94;
        }
        .cz-footer-total {
            font-size: 12px;
            font-weight: 800;
            color: #fff;
        }
    </style>
    """)

    num_colunas = 3
    registros = pedidos_agrupados.to_dict('records')

    for i in range(0, len(registros), num_colunas):
        cols = st.columns(num_colunas)
        for idx, row in enumerate(registros[i:i + num_colunas]):
            with cols[idx]:
                itens_pedido = df[df['id_pedido'] == row['id_pedido']]
                html = _renderizar_card_html(row, itens_pedido, filtro_status, cor_fundo_status)
                st.html(html)