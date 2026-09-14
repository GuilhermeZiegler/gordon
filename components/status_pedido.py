def card_pedido(row):
    return f"""
    <div style="
        border: 1px solid #444;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        background-color: #1a1a1a;
    ">
        <p style="margin: 2px 0;"><b>{row['nome_prod']}</b></p>
        <p style="margin: 2px 0; color: #aaa;">
            Qtd: {row['quantidade']} x R$ {row['preco_unitario']:.2f} = R$ {row['subtotal']:.2f}
        </p>
    </div>
    """

import streamlit as st

def renderizar_status_pedido(itens_pedido):
    html = """
    <div style="
        background:#fffdf5;
        border:1px solid #d8d0bd;
        border-radius:12px;
        padding:18px 22px;
        box-shadow:2px 3px 8px rgba(0,0,0,0.08);
        font-family:'Comic Sans MS','Segoe Print',cursive;
        color:#333;
        margin:10px 0 20px 0;
    ">
        <div style="
            font-size:22px;
            font-weight:bold;
            margin-bottom:12px;
            border-bottom:2px dashed #c9c0aa;
            padding-bottom:8px;
        ">
            📝 Itens do pedido
        </div>
    """

    for _, item in itens_pedido.iterrows():
        id_item = item['id_item']
        nome_prod = item['nome_prod']
        quantidade = item['quantidade']
        observacao = item.get('observacao', '')
        status = str(item.get('status', '')).lower()

        texto = f"{quantidade}x {nome_prod}"

        if observacao and str(observacao).strip() not in ['', 'nan']:
            texto += f" <span style='font-size:14px;'>(obs: {observacao})</span>"

        if status == 'fechado':
            html += f"""
            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                font-size:18px;
                margin:9px 0;
            ">
                <span style="color:#222;">✓</span>
                <span style="text-decoration:line-through; text-decoration-thickness:2px;">
                    Item {id_item}: {texto}
                </span>
            </div>
            """
        elif status == 'cancelado':
            html += f"""
            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                font-size:18px;
                margin:9px 0;
            ">
                <span style="color:#d62828; font-weight:bold; font-size:22px;">✕</span>
                <span style="
                    color:#d62828;
                    text-decoration:line-through;
                    text-decoration-thickness:2px;
                ">
                    Item {id_item}: {texto}
                </span>
            </div>
            """
        else:
            html += f"""
            <div style="
                font-size:18px;
                margin:9px 0;
            ">
                • <b>Item {id_item}</b>: {texto}
            </div>
            """

    html += "</div>"

    st.html(html)