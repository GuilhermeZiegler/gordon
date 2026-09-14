import streamlit as st
import pandas as pd

def card_ficha_tecnica(produto_info, ficha_completa, custo_total_produto):
    """Exibe a ficha técnica em formato HTML estilizado"""
    
    if ficha_completa.empty:
        return """
        <div style="background: #1e1e1e; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #333;">
            <p style="color: #888; font-size: 16px;">📭 Nenhum insumo adicionado à ficha deste produto.</p>
        </div>
        """
    
    html = f"""
    <div style="background: #1e1e1e; border-radius: 10px; padding: 15px; margin-bottom: 15px; border: 1px solid #333;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h4 style="margin: 0; color: #fff;">📦 Insumos da Ficha</h4>
            <span style="color: #888; font-size: 12px;">{len(ficha_completa)} insumos</span>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; color: #ccc; font-size: 14px;">
            <thead>
                <tr style="border-bottom: 2px solid #444;">
                    <th style="padding: 8px; text-align: left;">Insumo</th>
                    <th style="padding: 8px; text-align: center;">Qtd</th>
                    <th style="padding: 8px; text-align: center;">Unid.</th>
                    <th style="padding: 8px; text-align: right;">Preço Unit.</th>
                    <th style="padding: 8px; text-align: right;">Custo</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, row in ficha_completa.iterrows():
        custo = row.get('custo_total', 0.0)
        html += f"""
            <tr style="border-bottom: 1px solid #333;">
                <td style="padding: 8px;">{row['nome']}</td>
                <td style="padding: 8px; text-align: center;">{row['quantidade']}</td>
                <td style="padding: 8px; text-align: center;">{row['unidade_ficha']}</td>
                <td style="padding: 8px; text-align: right;">R$ {float(row['preco_unitario']):.2f}</td>
                <td style="padding: 8px; text-align: right; color: #4CAF50;">R$ {custo:.2f}</td>
            </tr>
        """
    
    html += f"""
            </tbody>
        </table>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 15px; border-top: 1px solid #444; padding-top: 15px;">
            <div style="text-align: center; background: #2d2d2d; border-radius: 8px; padding: 10px;">
                <p style="margin: 0; color: #888; font-size: 11px;">💰 Custo Total</p>
                <p style="margin: 0; color: #4CAF50; font-size: 20px; font-weight: bold;">R$ {custo_total_produto:.2f}</p>
            </div>
            <div style="text-align: center; background: #2d2d2d; border-radius: 8px; padding: 10px;">
                <p style="margin: 0; color: #888; font-size: 11px;">📊 Margem</p>
                <p style="margin: 0; color: #FFD700; font-size: 20px; font-weight: bold;">
                    {f"{(float(produto_info['p_venda']) / custo_total_produto - 1) * 100:.1f}%" if custo_total_produto > 0 else "N/A"}
                </p>
            </div>
            <div style="text-align: center; background: #2d2d2d; border-radius: 8px; padding: 10px;">
                <p style="margin: 0; color: #888; font-size: 11px;">💵 Preço Venda</p>
                <p style="margin: 0; color: #2196F3; font-size: 20px; font-weight: bold;">R$ {float(produto_info['p_venda']):.2f}</p>
            </div>
        </div>
    </div>
    """
    
    return html


def renderizar_card_ficha(produto_info, ficha_completa, custo_total_produto):
    """Renderiza o card diretamente no Streamlit"""
    st.html(card_ficha_tecnica(produto_info, ficha_completa, custo_total_produto))