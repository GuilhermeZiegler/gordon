import streamlit as st
from utils.caixa_utils import calcular_saldo_caixa


def card_caixa_resumo(caixa):
    saldo_final, total_entradas, total_saidas = calcular_saldo_caixa(caixa)

    total_estornos = sum(
        float(e.get("valor_estornado", 0)) for e in caixa.get("estornos", [])
    )

    status_icone = "🟢" if caixa['status'] == 'aberto' else "🔴"
    status_texto = "Aberto" if caixa['status'] == 'aberto' else "Fechado"

    vendas_mesa = caixa.get('vendas_mesa', 0.0)
    vendas_balcao = caixa.get('vendas_balcao', 0.0)
    vendas_takeaway = caixa.get('vendas_takeaway', 0.0)
    vendas_delivery = caixa.get('vendas_delivery', 0.0)

    html_metricas = f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
        <div style="background: #1e1e1e; border-radius: 10px; padding: 15px; border-left: 4px solid #f39c12; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
            <p style="margin: 0; color: #888; font-size: 12px;">💰 Saldo Inicial</p>
            <p style="margin: 4px 0 0 0; font-size: 22px; font-weight: bold; color: #fff;">R$ {caixa['saldo_inicial']:.2f}</p>
        </div>
        <div style="background: #1e1e1e; border-radius: 10px; padding: 15px; border-left: 4px solid #2ecc71; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
            <p style="margin: 0; color: #888; font-size: 12px;">📥 Entradas</p>
            <p style="margin: 4px 0 0 0; font-size: 22px; font-weight: bold; color: #fff;">R$ {total_entradas:.2f}</p>
        </div>
        <div style="background: #1e1e1e; border-radius: 10px; padding: 15px; border-left: 4px solid #e74c3c; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
            <p style="margin: 0; color: #888; font-size: 12px;">📤 Saídas</p>
            <p style="margin: 4px 0 0 0; font-size: 22px; font-weight: bold; color: #fff;">R$ {total_saidas:.2f}</p>
        </div>
        <div style="background: #1e1e1e; border-radius: 10px; padding: 15px; border-left: 4px solid #FFD700; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
            <p style="margin: 0; color: #888; font-size: 12px;">💵 Saldo Final</p>
            <p style="margin: 4px 0 0 0; font-size: 22px; font-weight: bold; color: #FFD700;">R$ {saldo_final:.2f}</p>
        </div>
    </div>
    """

    estornos_html = ''
    if total_estornos > 0:
        estornos_html = f"""
        <div style="background: #2d2d2d; border-radius: 8px; padding: 12px; margin-bottom: 15px;">
            <p style="margin: 0; color: #888; font-size: 12px;">↩️ Estornos</p>
            <p style="margin: 5px 0 0 0; color: #ff4444; font-size: 16px; font-weight: bold;">R$ {total_estornos:.2f}</p>
        </div>
        """

    html = f"""
    {html_metricas}

    <div style="
        background: #1e1e1e;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #333;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="margin: 0; color: #fff;">📋 Resumo do Dia</h3>
            <span style="color: #888; font-size: 14px;">{caixa['data_abertura']}</span>
        </div>

        <div style="display: flex; gap: 20px; margin-bottom: 15px; flex-wrap: wrap;">
            <span style="background: #2d2d2d; padding: 4px 14px; border-radius: 20px; font-size: 14px; color: #fff;">
                Status: {status_icone} {status_texto}
            </span>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
            <div style="background: #2d2d2d; border-radius: 8px; padding: 12px;">
                <p style="margin: 0; color: #888; font-size: 12px;">🛒 Vendas</p>
                <p style="margin: 5px 0 0 0; color: #FF9800; font-size: 14px;">Mesa: R$ {vendas_mesa:.2f}</p>
                <p style="margin: 2px 0 0 0; color: #4CAF50; font-size: 14px;">Balcão: R$ {vendas_balcao:.2f}</p>
                <p style="margin: 2px 0 0 0; color: #9C27B0; font-size: 14px;">Takeaway: R$ {vendas_takeaway:.2f}</p>
                <p style="margin: 2px 0 0 0; color: #2196F3; font-size: 14px;">Delivery: R$ {vendas_delivery:.2f}</p>
            </div>

            <div style="background: #2d2d2d; border-radius: 8px; padding: 12px;">
                <p style="margin: 0; color: #888; font-size: 12px;">📤 Saídas</p>
                <p style="margin: 5px 0 0 0; color: #ff4444; font-size: 14px;">Reembolso: R$ {caixa['reembolso']:.2f}</p>
                <p style="margin: 2px 0 0 0; color: #ff4444; font-size: 14px;">Estornos: R$ {total_estornos:.2f}</p>
            </div>
        </div>

        {estornos_html}

        {f'''
        <div style="background: #2d2d2d; border-radius: 8px; padding: 12px; margin-bottom: 15px;">
            <p style="margin: 0; color: #888; font-size: 12px;">💳 Por Método de Pagamento</p>
            {''.join([f'<p style="margin: 2px 0 0 0; color: #fff; font-size: 14px;">{metodo}: R$ {valor:.2f}</p>' for metodo, valor in caixa.get('vendas_metodo', {}).items()])}
        </div>
        ''' if caixa.get('vendas_metodo') else ''}

        {f'''
        <div style="background: #2d2d2d; border-radius: 8px; padding: 12px; margin-bottom: 15px;">
            <p style="margin: 0; color: #888; font-size: 12px;">👤 Pagamentos</p>
            {''.join([f'<p style="margin: 2px 0 0 0; color: #fff; font-size: 14px;">{p["funcionario"]}: R$ {p["valor"]:.2f} ({p.get("metodo", "")})</p>' for p in caixa['pagamentos']])}
        </div>
        ''' if caixa['pagamentos'] else ''}

        {f'''
        <div style="background: #2d2d2d; border-radius: 8px; padding: 12px; margin-bottom: 15px;">
            <p style="margin: 0; color: #888; font-size: 12px;">📤 Outras Saídas</p>
            {''.join([f'<p style="margin: 2px 0 0 0; color: #fff; font-size: 14px;">{s["descricao"]}: R$ {s["valor"]:.2f} ({s.get("metodo", "")})</p>' for s in caixa['saidas']])}
        </div>
        ''' if caixa['saidas'] else ''}
    </div>
    """

    st.html(html)