import streamlit as st

def card_produto(nome, codigo, tipo, preco, descricao):
    st.html(f"""
    <div style="
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #444;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0; color: #fff;">{nome}</h3>
                <p style="margin: 5px 0; color: #aaa; font-size: 14px;">
                    Código: {codigo} | Tipo: {tipo}
                </p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; color: #fff; font-size: 24px; font-weight: bold;">
                    R$ {preco:.2f}
                </p>
                <p style="margin: 0; color: #888; font-size: 12px;">Preço de Venda</p>
            </div>
        </div>
        <div style="
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid #444;
            font-size: 13px;
            color: #ccc;
        ">
            <strong style="color: #fff;">Descrição:</strong> {descricao}
        </div>
    </div>
    """)