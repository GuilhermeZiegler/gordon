import streamlit as st
from datetime import datetime
from utils.delivery_utils import calcular_tempo, obter_dados_cliente


def _cor_status(status):
    return {
        'preparando': '#f39c12',
        'pronto': '#3498db',
        'em_rota': '#9b59b6',
        'chegou': '#1abc9c',
        'entregue': '#2ecc71',
        'cancelado': '#e74c3c'
    }.get(status, '#888')


def _label_status(status):
    return {
        'preparando': 'Preparando',
        'pronto': 'Pronto',
        'em_rota': 'Em rota',
        'chegou': 'No cliente',
        'entregue': 'Entregue',
        'cancelado': 'Cancelado'
    }.get(status, status)


def renderizar_card_delivery(row):
    cor = _cor_status(row['status_entrega'])
    label = _label_status(row['status_entrega'])

    tempo_prod = calcular_tempo(row['criado_em'], row['pronto_em'])
    tempo_rota = calcular_tempo(row['saiu_entrega_em'], row['entregue_em'])
    tempo_total = calcular_tempo(row['criado_em'], datetime.now().strftime("%d/%m/%Y %H:%M:%S")) \
        if row['status_entrega'] not in ['entregue', 'cancelado'] else None

    atraso = (
        tempo_total is not None
        and row['status_entrega'] not in ['entregue', 'cancelado']
        and tempo_total > 45
    )

    id_cliente = str(row.get('id_cliente', '') or '')
    nome_cliente = str(row.get('nome_cliente', '') or '—')
    if id_cliente:
        cliente_linha = f"{nome_cliente} ({id_cliente})"
    else:
        cliente_linha = f"{nome_cliente} (sem cadastro)"

    cliente = obter_dados_cliente(id_cliente)

    if cliente:
        telefone = cliente.get('telefone_principal', '') or '—'
        partes_end = [
            cliente.get('logradouro', ''),
            cliente.get('numero', ''),
            cliente.get('complemento', '')
        ]
        endereco = ' '.join([p for p in partes_end if p]) or '—'
        bairro_cidade = ' - '.join([
            p for p in [cliente.get('bairro', ''), cliente.get('cidade', ''), cliente.get('estado', '')] if p
        ])
        if bairro_cidade:
            endereco = f"{endereco} ({bairro_cidade})"
        referencia = cliente.get('referencia', '')
    else:
        telefone = '—'
        endereco = 'Cadastro incompleto — completar em Clientes'
        referencia = ''

    def _linha_tempo(label_t, valor):
        if valor is None:
            return ''
        return f'<span class="dl-tempo">{label_t}: {valor}min</span>'

    tempos_html = ''.join([
        _linha_tempo('Produção', tempo_prod),
        _linha_tempo('Rota', tempo_rota),
        _linha_tempo('Total', tempo_total),
    ])

    atraso_html = '<span class="dl-atraso">⚠️ Atrasado</span>' if atraso else ''

    referencia_html = f'<div class="dl-linha"><strong>📌</strong> {referencia}</div>' if referencia else ''

    motoboy_html = f'<div class="dl-linha"><strong>🛵</strong> {row["motoboy"]}</div>' if row.get('motoboy') else ''

    st.html(f"""
    <style>
        .dl-card {{
            background: #181818;
            border: 2px solid {cor};
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
        }}
        .dl-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .dl-pedido {{
            font-size: 16px;
            font-weight: 800;
            color: {cor};
        }}
        .dl-status {{
            background: {cor};
            color: #000;
            padding: 3px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
        }}
        .dl-linha {{
            font-size: 13px;
            color: #ccc;
            margin: 3px 0;
        }}
        .dl-linha strong {{
            color: #fff;
        }}
        .dl-rodape {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #333;
        }}
        .dl-tempo {{
            font-size: 11px;
            color: #888;
        }}
        .dl-atraso {{
            font-size: 11px;
            color: #e74c3c;
            font-weight: 700;
        }}
    </style>

    <div class="dl-card">
        <div class="dl-header">
            <div class="dl-pedido">#{row['id_pedido']}</div>
            <div class="dl-status">{label}</div>
        </div>

        <div class="dl-linha"><strong>👤</strong> {cliente_linha}</div>
        <div class="dl-linha"><strong>📞</strong> {telefone}</div>
        <div class="dl-linha"><strong>📍</strong> {endereco}</div>
        {referencia_html}
        {motoboy_html}

        <div class="dl-rodape">
            {tempos_html}
            {atraso_html}
        </div>
    </div>
    """)