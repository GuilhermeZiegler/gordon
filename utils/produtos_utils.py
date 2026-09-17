import streamlit as st


def calcular_custo_insumo(id_insumo, quantidade, unidade_ficha):
    try:
        quantidade = float(quantidade)
    except (ValueError, TypeError):
        return 0.0

    df_insumos = st.session_state.insumos
    if df_insumos.empty:
        return 0.0

    insumo = df_insumos[df_insumos['id_insumo'] == id_insumo]
    if insumo.empty:
        return 0.0

    insumo = insumo.iloc[0]
    unidade_compra = insumo['unidade_compra']
    preco_unitario = float(insumo['preco_unitario'])

    if unidade_ficha == unidade_compra:
        return quantidade * preco_unitario

    if unidade_ficha == 'g' and unidade_compra == 'kg':
        return (quantidade / 1000) * preco_unitario
    elif unidade_ficha == 'ml' and unidade_compra == 'L':
        return (quantidade / 1000) * preco_unitario
    elif unidade_ficha == 'kg' and unidade_compra == 'g':
        return (quantidade * 1000) * preco_unitario
    elif unidade_ficha == 'L' and unidade_compra == 'ml':
        return (quantidade * 1000) * preco_unitario
    else:
        return quantidade * preco_unitario