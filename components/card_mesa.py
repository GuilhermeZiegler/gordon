import streamlit as st
import pandas as pd
from datetime import datetime

def card_mesa(row):
    pedidos_df = st.session_state.pedidos.copy()
    
    if 'status' not in pedidos_df.columns:
        pedidos_df['status'] = 'enviado'
    
    if 'valor_com_desconto' not in pedidos_df.columns:
        pedidos_df['valor_com_desconto'] = pedidos_df['subtotal']
    
    if 'desconto_tipo' not in pedidos_df.columns:
        pedidos_df['desconto_tipo'] = 'nenhum'
    
    if 'desconto_item' not in pedidos_df.columns:
        pedidos_df['desconto_item'] = 0.0
    
    if 'cortesia' not in pedidos_df.columns:
        pedidos_df['cortesia'] = False
    
    pedidos_df['id_mesa'] = pedidos_df['id_mesa'].astype(str)
    mesa_id = str(row['id_mesa'])
    
    pedidos_mesa = pedidos_df[pedidos_df['id_mesa'] == mesa_id]
    
    pedidos_cancelados = pedidos_mesa[pedidos_mesa['status'] == 'cancelado']
    pedidos_devolvidos = pedidos_mesa[pedidos_mesa['desconto_tipo'] == 'devolucao']
    pedidos_ativos = pedidos_mesa[pedidos_mesa['status'] != 'cancelado']
    
    pedidos_fechados = pedidos_mesa[pedidos_mesa['status'] == 'fechado']
    pedidos_abertos = pedidos_mesa[pedidos_mesa['status'] == 'enviado']
    
    valor_cancelados = pedidos_cancelados['subtotal'].sum() if not pedidos_cancelados.empty else 0.0
    valor_devolvidos = pedidos_devolvidos['subtotal'].sum() if not pedidos_devolvidos.empty else 0.0
    valor_pedidos = pedidos_ativos['subtotal'].sum() if not pedidos_ativos.empty else 0.0
    valor_com_desconto = pedidos_ativos['valor_com_desconto'].fillna(pedidos_ativos['subtotal']).sum() if not pedidos_ativos.empty else 0.0
    
    valor_fechados = pedidos_fechados['subtotal'].sum() if not pedidos_fechados.empty else 0.0
    valor_fechados_com_desconto = pedidos_fechados['valor_com_desconto'].fillna(pedidos_fechados['subtotal']).sum() if not pedidos_fechados.empty else 0.0
    
    itens_cortesia = pedidos_ativos[pedidos_ativos['cortesia'] == True]
    itens_desconto = pedidos_ativos[pd.to_numeric(pedidos_ativos['desconto_item'], errors='coerce').fillna(0) > 0]
    valor_cortesia = itens_cortesia['subtotal'].sum() if not itens_cortesia.empty else 0.0
    valor_desconto = itens_desconto['subtotal'].sum() if not itens_desconto.empty else 0.0
    
    valor_total = row.get('valor_total', 0)
    if pd.isna(valor_total):
        valor_total = 0.0
    
    desconto_valor = row.get('desconto_valor', 0.0)
    if pd.isna(desconto_valor):
        desconto_valor = 0.0
    
    valor_10 = row.get('valor_10', 0.0)
    if pd.isna(valor_10):
        valor_10 = 0.0
    
    qtd_pedidos_abertos = len(pedidos_abertos)
    qtd_pedidos_fechados = len(pedidos_fechados)
    qtd_pedidos_cancelados = len(pedidos_cancelados) + len(pedidos_devolvidos)
    qtd_cortesias = len(itens_cortesia)
    qtd_devolucoes = len(pedidos_devolvidos)
    
    mesa_fechada = row.get('status', '') == 'fechada'
    
    if mesa_fechada:
        tem_pedido_aberto = False
        tem_pedido_cancelado = False
        tem_pedido_fechado = False
    else:
        tem_pedido_aberto = qtd_pedidos_abertos > 0
        tem_pedido_cancelado = qtd_pedidos_cancelados > 0
        tem_pedido_fechado = qtd_pedidos_fechados > 0
    
    if tem_pedido_cancelado:
        status_color = "🔴"
        border_color = "#ff4444"
        status_text = "Aberta (Cancelamentos)"
    elif tem_pedido_aberto:
        status_color = "🟡"
        border_color = "#ffd700"
        status_text = "Aberta (Pedidos)"
    elif tem_pedido_fechado:
        status_color = "🟢"
        border_color = "#00ff00"
        status_text = "Aberta (Finalizados)"
    else:
        status_color = "🟢"
        border_color = "#00ff00"
        status_text = "Aberta"
    
    ticket_medio = row['ticket_medio'] if row['ticket_medio'] > 0 else 0
    if pd.isna(ticket_medio):
        ticket_medio = 0
    
    cover_unitario = row.get('cover', 0.0)
    if pd.isna(cover_unitario):
        cover_unitario = 0.0
    
    qtd_clientes = row['qtd_clientes']
    if pd.isna(qtd_clientes):
        qtd_clientes = 0
    
    cover_total = cover_unitario * qtd_clientes
    incluir_10 = row.get('incluir_10', False)
    
    if incluir_10:
        dez_porcento = valor_10
    else:
        dez_porcento = 0
    
    if not pedidos_abertos.empty:
        criado_em_mais_antigo = pedidos_abertos['criado_em'].min()
        try:
            dt_mais_antigo = datetime.strptime(criado_em_mais_antigo, "%d/%m/%Y %H:%M:%S")
            agora = datetime.now()
            diff_minutos = int((agora - dt_mais_antigo).total_seconds() / 60)
            if diff_minutos < 60:
                tempo_str = f"{diff_minutos}min"
            else:
                horas = diff_minutos // 60
                minutos = diff_minutos % 60
                tempo_str = f"{horas}h {minutos}min"
        except:
            tempo_str = "N/A"
    else:
        tempo_str = "—"
    
    html = f"""
    <style>
        .mesa-card {{
            border: 2px solid {border_color};
            border-radius: 13px;
            padding: 12px;
            margin-bottom: 10px;
            background: #181818;
            box-shadow: 0 3px 10px rgba(0,0,0,0.22);
            font-family: sans-serif;
            box-sizing: border-box;
        }}

        .mesa-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 7px;
            margin-bottom: 10px;
        }}

        .mesa-titulo {{
            font-size: 17px;
            font-weight: 700;
            color: {border_color};
            line-height: 1.2;
        }}

        .mesa-status {{
            color: {border_color};
            border: 1px solid {border_color};
            background: #222;
            padding: 3px 7px;
            border-radius: 999px;
            font-size: 9px;
            font-weight: 700;
            text-align: center;
        }}

        .mesa-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            margin-bottom: 9px;
        }}

        .mesa-info-box {{
            background: #222;
            border-radius: 7px;
            padding: 6px 8px;
        }}

        .mesa-info-label {{
            color: #888;
            font-size: 8px;
            text-transform: uppercase;
            letter-spacing: .3px;
        }}

        .mesa-info-value {{
            color: #eee;
            font-size: 11px;
            font-weight: 600;
            margin-top: 2px;
        }}

        .mesa-badges {{
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }}

        .mesa-badge {{
            background: #252525;
            padding: 4px 7px;
            border-radius: 999px;
            font-size: 9px;
            white-space: nowrap;
        }}

        .mesa-financeiro {{
            background: #202020;
            border-radius: 8px;
            padding: 8px;
        }}

        .mesa-linha {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 7px;
            padding: 2px 0;
            color: #ddd;
            font-size: 11px;
        }}

        .mesa-linha span:last-child {{
            font-weight: 600;
            white-space: nowrap;
        }}

        .mesa-total {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 7px;
            padding: 9px 9px;
            border-radius: 7px;
            background: #292929;
            border: 1px solid {border_color};
            color: #fff;
        }}

        .mesa-total-label {{
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: .4px;
        }}

        .mesa-total-valor {{
            font-size: 17px;
            font-weight: 800;
            color: {border_color};
        }}

        .mesa-extra {{
            margin-top: 8px;
            padding-top: 7px;
            border-top: 1px solid #333;
        }}

        .mesa-footer {{
            margin-top: 8px;
            padding-top: 7px;
            border-top: 1px solid #333;
        }}

        .mesa-footer-linha {{
            display: flex;
            justify-content: space-between;
            gap: 7px;
            margin: 3px 0;
            font-size: 10px;
        }}

        .mesa-tempo {{
            color: #ffaa00;
        }}

        .mesa-fechados {{
            color: #4CAF50;
        }}

        .mesa-cancelados {{
            color: #ff4444;
        }}

        .mesa-data {{
            margin-top: 7px;
            color: #777;
            font-size: 8px;
        }}

        @media (max-width: 500px) {{
            .mesa-card {{
                padding: 10px;
            }}

            .mesa-header {{
                flex-direction: column;
            }}

            .mesa-status {{
                align-self: flex-start;
            }}

            .mesa-info {{
                grid-template-columns: 1fr 1fr;
            }}

            .mesa-total-valor {{
                font-size: 15px;
            }}
        }}
    </style>

    <div class="mesa-card">

        <div class="mesa-header">
            <div class="mesa-titulo">
                {status_color} Mesa {row['id_mesa']}
            </div>
            <div class="mesa-status">
                {status_text.replace('Aberta (', '').replace(')', '') if '(' in status_text else status_text}
            </div>
        </div>

        <div class="mesa-info">
            <div class="mesa-info-box">
                <div class="mesa-info-label">Garçom</div>
                <div class="mesa-info-value">
                    {row['garcom'] if pd.notna(row['garcom']) and row['garcom'] != '' else 'Não definido'}
                </div>
            </div>

            <div class="mesa-info-box">
                <div class="mesa-info-label">Clientes</div>
                <div class="mesa-info-value">{qtd_clientes}</div>
            </div>
        </div>

        <div class="mesa-badges">
            <span class="mesa-badge">
                📦 {qtd_pedidos_abertos + qtd_pedidos_fechados} itens
            </span>

            <span class="mesa-badge" style="color:#4CAF50;">
                ✅ {qtd_pedidos_fechados} fechados
            </span>

            <span class="mesa-badge" style="color:#ffd700;">
                ⏳ {qtd_pedidos_abertos} abertos
            </span>

            {f'<span class="mesa-badge" style="color:#ff4444;">🚫 {qtd_pedidos_cancelados} cancelados</span>' if qtd_pedidos_cancelados > 0 else ''}

            {f'<span class="mesa-badge" style="color:#FF6B6B;">🎁 {qtd_cortesias} cortesias</span>' if qtd_cortesias > 0 else ''}
        </div>

        <div class="mesa-financeiro">

            <div class="mesa-linha">
                <span>Valor Pedidos</span>
                <span>R$ {valor_pedidos:.2f}</span>
            </div>

            {f'''
            <div class="mesa-linha" style="color:#ffd700;">
                <span>Cortesia/Desconto</span>
                <span>R$ {valor_pedidos - valor_com_desconto:.2f}</span>
            </div>
            ''' if (valor_pedidos - valor_com_desconto) > 0 else ''}

            {f'''
            <div class="mesa-linha" style="color:#ff4444;">
                <span>Devolvidos</span>
                <span>R$ {valor_devolvidos:.2f}</span>
            </div>
            ''' if valor_devolvidos > 0 else ''}

            {f'''
            <div class="mesa-linha" style="color:#ff4444;">
                <span>Cancelados</span>
                <span>R$ {valor_cancelados:.2f}</span>
            </div>
            ''' if valor_cancelados > 0 else ''}

            {f'''
            <div class="mesa-linha" style="color:#ffd700;">
                <span>10% Garçom</span>
                <span>R$ {dez_porcento:.2f}</span>
            </div>
            ''' if incluir_10 else ''}

            {f'''
            <div class="mesa-linha">
                <span>Cover</span>
                <span>R$ {cover_total:.2f}</span>
            </div>
            ''' if cover_total > 0 else ''}

            {f'''
            <div class="mesa-linha" style="color:#00ff00;">
                <span>Valor Líquido</span>
                <span>R$ {valor_com_desconto:.2f}</span>
            </div>
            ''' if valor_com_desconto != valor_pedidos else ''}

            <div class="mesa-total">
                <div class="mesa-total-label">Total Final</div>
                <div class="mesa-total-valor">R$ {valor_total:.2f}</div>
            </div>

        </div>

        <div class="mesa-extra">

            <div class="mesa-linha">
                <span>Ticket Médio</span>
                <span>R$ {ticket_medio:.2f}</span>
            </div>

            <div class="mesa-data">
                Aberto em: {row['aberto_em']}
            </div>

        </div>

        <div class="mesa-footer">

            <div class="mesa-footer-linha mesa-tempo">
                <span><b>Pedidos em aberto</b></span>
                <span>
                    {qtd_pedidos_abertos}
                    {f' · há {tempo_str}' if qtd_pedidos_abertos > 0 else ''}
                </span>
            </div>

            {f'''
            <div class="mesa-footer-linha mesa-fechados">
                <span><b>Pedidos finalizados</b></span>
                <span>{qtd_pedidos_fechados}</span>
            </div>
            ''' if qtd_pedidos_fechados > 0 else ''}

            {f'''
            <div class="mesa-footer-linha mesa-cancelados">
                <span><b>Cancelados</b></span>
                <span>{qtd_pedidos_cancelados}</span>
            </div>
            ''' if qtd_pedidos_cancelados > 0 else ''}

        </div>

    </div>
    """
    
    st.html(html)