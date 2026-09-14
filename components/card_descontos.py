import streamlit as st
import pandas as pd


def renderizar_card_item(
    nome_produto,
    cod_item,
    quantidade,
    preco_unitario,
    subtotal,
    valor_com_desconto,
    estado
):
    cores = {
        'cortesia': ('🎁', '#27ae60', 'CORTESIA'),
        'devolucao': ('↩️', '#e74c3c', 'DEVOLUÇÃO'),
        'desconto': ('✂️', '#f39c12', 'DESCONTO'),
    }

    preco_unitario = pd.to_numeric(preco_unitario, errors='coerce')
    subtotal = pd.to_numeric(subtotal, errors='coerce')
    valor_com_desconto = pd.to_numeric(valor_com_desconto, errors='coerce')

    preco_unitario = 0.0 if pd.isna(preco_unitario) else float(preco_unitario)
    subtotal = 0.0 if pd.isna(subtotal) else float(subtotal)
    valor_com_desconto = subtotal if pd.isna(valor_com_desconto) else float(valor_com_desconto)

    if estado in cores:
        emoji, cor, texto = cores[estado]
        status_html = f'<span class="item-status" style="color:{cor};">{emoji} {texto}</span>'
    else:
        status_html = ''

    return f"""
    <div class="item-card">
        <div class="item-top">
            <div>
                <div class="item-name">{nome_produto}</div>
                <div class="item-id">#{cod_item}</div>
            </div>
            {status_html}
        </div>

        <div class="item-info">
            <span class="item-qtd">{quantidade}x</span>
            <span class="item-unit">R$ {preco_unitario:.2f}</span>
            <span class="item-total">R$ {valor_com_desconto:.2f}</span>
        </div>
    </div>
    """


def renderizar_resumo_mesa(
    total_itens,
    valor_pedidos,
    desconto_valor,
    valor_com_desconto
):
    return f"""
    <div class="resumo-mesa">
        <div>
            <span>Itens</span>
            <strong>{total_itens}</strong>
        </div>
        <div>
            <span>Subtotal</span>
            <strong>R$ {float(valor_pedidos):.2f}</strong>
        </div>
        <div>
            <span>Desconto</span>
            <strong>R$ {float(desconto_valor):.2f}</strong>
        </div>
        <div>
            <span>Total</span>
            <strong>R$ {float(valor_com_desconto):.2f}</strong>
        </div>
    </div>
    """


def renderizar_cabecalho_pedido(
    pedido,
    mesa,
    quantidade_itens
):
    return f"""
    <div class="pedido-header">
        <div>
            <div class="pedido-titulo">
                Pedido #{pedido}
            </div>
            <div class="pedido-mesa">
                Mesa {mesa}
            </div>
        </div>

        <div class="pedido-qtd">
            {quantidade_itens} itens
        </div>
    </div>
    """


def renderizar_titulo_acoes(quantidade):
    return f"""
    <div class="acao-titulo">
        Ações para {quantidade} item(ns) selecionado(s)
    </div>
    """


def renderizar_estilo_cards():
    st.markdown(
        """
        <style>
        .item-card {
            padding: 2px 0 14px 0;
        }

        .item-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }

        .item-name {
            font-size: 17px;
            font-weight: 700;
            color: #f1f3f5;
            line-height: 1.2;
        }

        .item-id {
            margin-top: 4px;
            font-size: 11px;
            color: #8b929d;
        }

        .item-status {
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
        }

        .item-info {
            display: flex;
            align-items: baseline;
            gap: 12px;
            margin-top: 14px;
        }

        .item-qtd {
            font-size: 14px;
            font-weight: 700;
            color: #f1f3f5;
        }

        .item-unit {
            font-size: 14px;
            color: #9da3ad;
        }

        .item-total {
            margin-left: auto;
            font-size: 17px;
            font-weight: 700;
            color: #ffffff;
        }

        .pedido-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #181818;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 10px 14px;
            margin: 10px 0;
        }

        .pedido-titulo {
            color: #f1f3f5;
            font-size: 16px;
            font-weight: 700;
        }

        .pedido-mesa {
            color: #888;
            font-size: 11px;
            margin-top: 3px;
        }

        .pedido-qtd {
            color: #aaa;
            font-size: 13px;
        }

        .resumo-mesa {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin: 12px 0 16px 0;
        }

        .resumo-mesa div {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 10px 12px;
            text-align: center;
        }

        .resumo-mesa span {
            display: block;
            font-size: 12px;
            color: #8b929d;
        }

        .resumo-mesa strong {
            display: block;
            font-size: 18px;
            color: #f1f3f5;
            margin-top: 2px;
        }

        .gerenciar-selecao {
            font-size: 13px;
            color: #999;
            margin: 8px 0 4px 0;
        }

        .acao-titulo {
            font-size: 14px;
            font-weight: 700;
            color: #f1f3f5;
            margin: 14px 0 8px 0;
        }

        div[data-testid="stCheckbox"] {
            margin-bottom: -8px;
        }

        div[data-testid="stCheckbox"] label {
            font-size: 13px;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 10px;
        }

        div[data-testid="stHorizontalBlock"] button {
            min-height: 42px;
            border-radius: 9px;
            font-size: 13px;
        }

        @media (max-width: 600px) {
            .resumo-mesa {
                grid-template-columns: repeat(2, 1fr);
            }

            .pedido-header {
                padding: 9px 11px;
            }

            .item-name {
                font-size: 15px;
            }

            .item-total {
                font-size: 15px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )
