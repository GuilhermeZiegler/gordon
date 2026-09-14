import streamlit as st
import html


def card_item_pedido(id_pedido, origem_venda, itens):
    itens_html = ""

    for _, item in itens.iterrows():
        nome = html.escape(str(item.get("nome_prod", "")))
        quantidade = int(item.get("quantidade", 1))
        status = str(item.get("status", "enviado")).lower()

        if status == "fechado":
            icone = "✅"
            classe = "item-fechado"
        elif status == "cancelado":
            icone = "❌"
            classe = "item-cancelado"
        else:
            icone = "☐"
            classe = "item-aberto"

        itens_html += f"""
        <div class="item {classe}">
            <span class="icone">{icone}</span>
            <span class="descricao">{quantidade}x {nome}</span>
        </div>
        """

    origem = {
        "mesa": "Mesa",
        "takeaway": "Takeaway",
        "delivery": "Delivery"
    }.get(str(origem_venda).lower(), str(origem_venda))

    st.html(f"""
    <div class="card-pedido">
        <div class="cabecalho">
            <div class="pedido">{html.escape(str(id_pedido))}</div>
            <div class="origem"><strong>Origem:</strong> {html.escape(origem)}</div>
        </div>

        <div class="titulo">Itens do pedido:</div>

        <div class="itens">
            {itens_html}
        </div>
    </div>

    <style>
        .card-pedido {{
            background: #fffdf5;
            border: 1px solid #d9d2c3;
            border-radius: 10px;
            padding: 16px 18px;
            margin: 8px 0 16px 0;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
        }}

        .cabecalho {{
            border-bottom: 1px solid #e5dfd3;
            padding-bottom: 10px;
            margin-bottom: 12px;
        }}

        .pedido {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 4px;
        }}

        .origem {{
            font-size: 14px;
            color: #555;
        }}

        .titulo {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .item {{
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 5px 0;
            font-size: 15px;
        }}

        .icone {{
            width: 20px;
            text-align: center;
            flex-shrink: 0;
        }}

        .descricao {{
            flex: 1;
        }}

        .item-fechado {{
            color: #555;
        }}

        .item-cancelado {{
            color: #888;
            text-decoration: line-through;
            text-decoration-thickness: 1.5px;
        }}

        .item-aberto {{
            color: #222;
        }}
    </style>
    """)