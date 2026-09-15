import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def _brl(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _pct(valor, base):
    if not base:
        return "—"
    try:
        return f"{(float(valor) / float(base)) * 100:.1f}%"
    except Exception:
        return "—"


def _delta(atual, anterior):
    try:
        atual = float(atual)
        anterior = float(anterior)
        if anterior == 0:
            return "—"
        variacao = ((atual - anterior) / abs(anterior)) * 100
        cor = "#2ecc71" if variacao >= 0 else "#e74c3c"
        sinal = "+" if variacao >= 0 else ""
        return f'<span style="color:{cor};">{sinal}{variacao:.1f}%</span>'
    except Exception:
        return "—"


def _linha(label, atual, anterior=None, destaque=False, nivel=0, cor_valor=None):
    padding = f"padding-left: {16 + nivel * 16}px;"

    if destaque:
        fundo = "background: #202020;"
        peso = "font-weight: 700;"
        tamanho = "font-size: 14px;"
    else:
        fundo = ""
        peso = "font-weight: 400;"
        tamanho = "font-size: 13px;"

    valor_cor = cor_valor or "#f1f3f5"

    html_anterior = ""
    html_delta = ""

    if anterior is not None:
        html_anterior = f'<td style="text-align:right; color:#858b94; {tamanho}">{_brl(anterior)}</td>'
        html_delta = f'<td style="text-align:right; {tamanho}">{_delta(atual, anterior)}</td>'

    return f"""
    <tr style="{fundo} border-bottom: 1px solid #2a2a2a;">
        <td style="{padding} color:#ccc; {peso} {tamanho}">{label}</td>
        <td style="text-align:right; color:{valor_cor}; {peso} {tamanho}">{_brl(atual)}</td>
        {html_anterior}
        {html_delta}
    </tr>
    """


def _linha_negativa(label, valor, anterior=None, destaque=False, nivel=0):
    html_anterior = ""
    html_delta = ""

    if anterior is not None:
        html_anterior = f'<td style="text-align:right; color:#858b94; font-size:13px">{_brl(anterior)}</td>'
        html_delta = f'<td style="text-align:right; font-size:13px">{_delta(valor, anterior)}</td>'

    fundo = "background: #202020;" if destaque else ""
    peso = "font-weight: 700;" if destaque else "font-weight: 400;"
    tamanho = "font-size: 14px;" if destaque else "font-size: 13px;"
    padding = f"padding-left: {16 + nivel * 16}px;"

    return f"""
    <tr style="{fundo} border-bottom: 1px solid #2a2a2a;">
        <td style="{padding} color:#ccc; {peso} {tamanho}">{label}</td>
        <td style="text-align:right; color:#e74c3c; {peso} {tamanho}">- {_brl(valor)}</td>
        {html_anterior}
        {html_delta}
    </tr>
    """


def _linha_total(label, valor, margem=None, anterior=None):
    html_anterior = ""
    html_delta = ""

    if anterior is not None:
        html_anterior = f'<td style="text-align:right; color:#858b94; font-size:14px">{_brl(anterior)}</td>'
        html_delta = f'<td style="text-align:right; font-size:14px">{_delta(valor, anterior)}</td>'

    margem_html = ""
    if margem:
        margem_html = f'<span style="color:#888; font-size:11px; margin-left:8px;">({margem})</span>'

    return f"""
    <tr style="background: #252525; border-top: 1px solid #444; border-bottom: 1px solid #444;">
        <td style="padding-left: 16px; color:#fff; font-weight: 800; font-size: 14px; padding-top: 10px; padding-bottom: 10px;">
            {label}{margem_html}
        </td>
        <td style="text-align:right; color:#fff; font-weight: 800; font-size: 15px; padding-top: 10px; padding-bottom: 10px;">
            {_brl(valor)}
        </td>
        {html_anterior}
        {html_delta}
    </tr>
    """


def renderizar_card_dre(dre, comparativo=None):
    comparativo_ativo = comparativo is not None

    cabecalho_extra = ""
    if comparativo_ativo:
        cabecalho_extra = """
            <th style="text-align:right; color:#858b94; font-size:12px; padding:8px;">ANTERIOR</th>
            <th style="text-align:right; color:#858b94; font-size:12px; padding:8px;">Δ</th>
        """

    def _ant(chave):
        if not comparativo_ativo:
            return None
        return comparativo.get(chave)

    linhas = ""

    linhas += _linha_total("RECEITA BRUTA", dre["receita_bruta"], anterior=_ant("receita_bruta"))

    linhas += _linha("Vendas Mesa", dre["vendas_mesa"], anterior=_ant("vendas_mesa"), nivel=1)
    linhas += _linha("Vendas Balcão", dre["vendas_balcao"], anterior=_ant("vendas_balcao"), nivel=1)
    linhas += _linha("Vendas Takeaway", dre["vendas_takeaway"], anterior=_ant("vendas_takeaway"), nivel=1)
    linhas += _linha("Vendas Delivery", dre["vendas_delivery"], anterior=_ant("vendas_delivery"), nivel=1)

    linhas += _linha_negativa("Estornos", dre["estornos"], anterior=_ant("estornos"))
    linhas += _linha_negativa("Descontos / Cortesias / Devoluções", dre["descontos"], anterior=_ant("descontos"))

    linhas += _linha_total("RECEITA LÍQUIDA", dre["receita_liquida"], anterior=_ant("receita_liquida"))

    linhas += _linha_negativa("CMV (Custo das Mercadorias Vendidas)", dre["cmv"], anterior=_ant("cmv"))

    margem_bruta = _pct(dre["lucro_bruto"], dre["receita_liquida"])
    linhas += _linha_total("LUCRO BRUTO", dre["lucro_bruto"], margem=f"Margem {margem_bruta}", anterior=_ant("lucro_bruto"))

    linhas += _linha_negativa("Despesas Operacionais", dre["despesas_total"], anterior=_ant("despesas_total"))

    for nome, valor in dre["despesas_detalhe"].items():
        linhas += _linha(nome, valor, anterior=None, nivel=2)

    linhas += _linha_total("LUCRO OPERACIONAL", dre["lucro_operacional"], anterior=_ant("lucro_operacional"))

    linhas += _linha_negativa("Repasses", dre["repasses_total"], anterior=_ant("repasses_total"))
    linhas += _linha("Cover", dre["repasse_cover"], anterior=_ant("repasse_cover"), nivel=2)
    linhas += _linha("Taxa de Entrega", dre["repasse_taxa_entrega"], anterior=_ant("repasse_taxa_entrega"), nivel=2)
    linhas += _linha("Atendimento 10%", dre["repasse_10"], anterior=_ant("repasse_10"), nivel=2)

    for setor, valor in dre["repasse_10_split"].items():
        linhas += _linha(setor, valor, anterior=None, nivel=3)

    margem_liquida = _pct(dre["resultado_liquido"], dre["receita_liquida"])
    linhas += _linha_total("RESULTADO LÍQUIDO", dre["resultado_liquido"], margem=f"Margem {margem_liquida}", anterior=_ant("resultado_liquido"))

    html = f"""
    <style>
        .dre-container {{
            background: #181818;
            border: 1px solid #303030;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
            overflow-x: auto;
        }}
        .dre-titulo {{
            color: #f1f3f5;
            font-size: 18px;
            font-weight: 800;
            margin-bottom: 4px;
        }}
        .dre-periodo {{
            color: #858b94;
            font-size: 12px;
            margin-bottom: 16px;
        }}
        .dre-tabela {{
            width: 100%;
            border-collapse: collapse;
        }}
        .dre-tabela th {{
            text-align: left;
            color: #858b94;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: .5px;
            padding: 8px;
            border-bottom: 1px solid #333;
        }}
        .dre-tabela td {{
            padding: 6px 8px;
        }}
    </style>

    <div class="dre-container">
        <div class="dre-titulo">📊 DRE — Demonstrativo de Resultado</div>
        <div class="dre-periodo">{dre["periodo_label"]}</div>

        <table class="dre-tabela">
            <thead>
                <tr>
                    <th style="width: 40%;">Descrição</th>
                    <th style="text-align:right;">Atual</th>
                    {cabecalho_extra}
                </tr>
            </thead>
            <tbody>
                {linhas}
            </tbody>
        </table>
    </div>
    """

    st.html(html)