from datetime import datetime
import html
import streamlit as st
import pandas as pd
from utils.print import imprimir_ticket


def parse_data_hora(data_str):
    for fmt in ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"]:
        try:
            return datetime.strptime(data_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato de data inválido: {data_str}")

def _preparar_pedidos(pedidos):
    pedidos = pedidos.copy()

    if "status" in pedidos.columns:
        pedidos = pedidos[
            pedidos["status"].astype(str).str.lower() == "fechado"
        ].copy()

    if "valor_com_desconto" not in pedidos.columns:
        pedidos["valor_com_desconto"] = pedidos["subtotal"]
    else:
        pedidos["valor_com_desconto"] = pedidos[
            "valor_com_desconto"
        ].fillna(pedidos["subtotal"])

    if "cortesia" in pedidos.columns:
        mask_cortesia = (
            pedidos["cortesia"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "sim"])
        )
        pedidos.loc[mask_cortesia, "valor_com_desconto"] = 0.0

    if "desconto_item" in pedidos.columns:
        pedidos["desconto_item"] = pd.to_numeric(
            pedidos["desconto_item"],
            errors="coerce"
        ).fillna(0.0)
    else:
        pedidos["desconto_item"] = 0.0

    return pedidos


def gerar_comanda(mesa_id, pedidos_mesa, mesa_info, incluir_garcom=False):
    pedidos_mesa = _preparar_pedidos(pedidos_mesa)

    garcom = mesa_info["garcom"] if mesa_info["garcom"] else "Não definido"
    qtd_clientes = mesa_info["qtd_clientes"]
    cover_unitario = float(mesa_info.get("cover", 0))
    cover = cover_unitario * qtd_clientes
    incluir_garcom = incluir_garcom or mesa_info.get("incluir_10", False)

    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    if pedidos_mesa.empty:
        itens_html = """
        <div class="item">
            <div class="item-info">
                <span class="quantidade">-</span>
                <span class="nome">Nenhum item finalizado</span>
            </div>
            <span class="valor">R$ 0.00</span>
        </div>
        """
        subtotal = 0.0
        valor_real = 0.0
        desconto_total = 0.0
        qtd_itens = 0
        qtd_total = 0
    else:
        subtotal = float(pedidos_mesa["subtotal"].sum())
        valor_real = float(
            pedidos_mesa["valor_com_desconto"].sum()
        )
        desconto_total = subtotal - valor_real
        qtd_itens = len(pedidos_mesa)
        qtd_total = int(pedidos_mesa["quantidade"].sum())

        itens_html = ""

        for _, item in pedidos_mesa.iterrows():
            nome = html.escape(str(item["nome_prod"]))
            qtd = int(item["quantidade"])
            valor = float(item["valor_com_desconto"])

            desconto_info = ""

            if item.get("cortesia", False):
                desconto_info = " (CORTESIA)"
            elif item.get("desconto_tipo") == "devolucao":
                desconto_info = " (DEVOLUCAO)"
            elif item.get("desconto_item", 0) > 0:
                desconto_info = (
                    f" (DESC: R$ {float(item['desconto_item']):.2f})"
                )

            itens_html += f"""
            <div class="item">
                <div class="item-info">
                    <span class="quantidade">{qtd}x</span>
                    <span class="nome">{nome}{desconto_info}</span>
                </div>
                <span class="valor">R$ {valor:.2f}</span>
            </div>
            """

    taxa_garcom = valor_real * 0.10 if incluir_garcom else 0
    total = valor_real + cover + taxa_garcom

    garcom_html = f"""
    <div class="linha-total">
        <span>10% Garçom</span>
        <strong>R$ {taxa_garcom:.2f}</strong>
    </div>
    """ if incluir_garcom else ""

    cover_unitario = cover / qtd_clientes if qtd_clientes > 0 else 0

    cover_html = f"""
    <div class="linha-total">
        <span>Cover ({qtd_clientes} × R$ {cover_unitario:.2f})</span>
        <strong>R$ {cover:.2f}</strong>
    </div>
    """ if cover > 0 else ""

    desconto_html = f"""
    <div class="linha-total" style="color:#ff4444;">
        <span>Descontos</span>
        <strong>- R$ {desconto_total:.2f}</strong>
    </div>
    """ if desconto_total > 0 else ""

    return f"""
    <div class="comanda">
        <div class="cabecalho">
            <div class="titulo">COMANDA</div>
        </div>

        <div class="separador"></div>

        <div class="informacoes">
            <div>
                <span>Mesa</span>
                <strong>{html.escape(str(mesa_id))}</strong>
            </div>

            <div>
                <span>Garçom</span>
                <strong>{html.escape(str(garcom))}</strong>
            </div>

            <div>
                <span>Clientes</span>
                <strong>{qtd_clientes}</strong>
            </div>

            <div>
                <span>Data</span>
                <strong>{data_hora}</strong>
            </div>
        </div>

        <div class="separador"></div>

        <div class="itens-header">
            <span>ITEM</span>
            <span>VALOR</span>
        </div>

        <div class="itens">
            {itens_html}
        </div>

        <div class="separador"></div>

        <div class="resumo">
            <div>
                <span>Total de itens</span>
                <strong>{qtd_itens}</strong>
            </div>

            <div>
                <span>Quantidade</span>
                <strong>{qtd_total}</strong>
            </div>
        </div>

        <div class="linha-total">
            <span>Subtotal bruto</span>
            <strong>R$ {subtotal:.2f}</strong>
        </div>

        {desconto_html}

        <div class="linha-total" style="font-weight:bold;">
            <span>Valor líquido</span>
            <strong>R$ {valor_real:.2f}</strong>
        </div>

        {cover_html}

        {garcom_html}

        <div class="separador"></div>

        <div class="total">
            <span>TOTAL</span>
            <strong>R$ {total:.2f}</strong>
        </div>

        <div class="separador"></div>

        <div class="rodape">
            <strong>Obrigado pela preferência!</strong>
            <span>Volte sempre!</span>
        </div>
    </div>
    """


def gerar_comanda_impressao(
    mesa_id,
    pedidos_mesa,
    mesa_info,
    incluir_garcom=False
):
    pedidos_mesa = _preparar_pedidos(pedidos_mesa)

    garcom = mesa_info["garcom"] if mesa_info["garcom"] else "Não definido"
    qtd_clientes = mesa_info["qtd_clientes"]
    cover_unitario = float(mesa_info.get("cover", 0))
    cover = cover_unitario * qtd_clientes
    incluir_garcom = incluir_garcom or mesa_info.get("incluir_10", False)

    if pedidos_mesa.empty:
        subtotal = 0.0
        valor_real = 0.0
        desconto_total = 0.0
        qtd_itens = 0
        qtd_total = 0
        sem_itens = True
    else:
        subtotal = float(pedidos_mesa["subtotal"].sum())
        valor_real = float(
            pedidos_mesa["valor_com_desconto"].sum()
        )
        desconto_total = subtotal - valor_real
        qtd_itens = len(pedidos_mesa)
        qtd_total = int(pedidos_mesa["quantidade"].sum())
        sem_itens = False

    taxa_garcom = (
        (valor_real + cover) * 0.10
        if incluir_garcom
        else 0
    )

    total = valor_real + cover + taxa_garcom

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    largura = 48
    linhas = []

    linhas.append("=" * largura)
    linhas.append("COMANDA".center(largura))
    linhas.append("=" * largura)

    linhas.append(f"Mesa:     {mesa_id}")
    linhas.append(f"Garçom:   {garcom}")
    linhas.append(f"Clientes: {qtd_clientes}")
    linhas.append(f"Data:     {data_hora}")

    linhas.append("-" * largura)
    linhas.append(f"{'QTD':<5}{'ITEM':<28}{'VALOR':>15}")
    linhas.append("-" * largura)

    if not sem_itens:
        for _, item in pedidos_mesa.iterrows():
            qtd = int(item["quantidade"])
            nome = str(item["nome_prod"])
            valor = float(item["valor_com_desconto"])

            desconto_info = ""

            if item.get("cortesia", False):
                desconto_info = " (CORTESIA)"
            elif item.get("desconto_tipo") == "devolucao":
                desconto_info = " (DEVOLUCAO)"
            elif item.get("desconto_item", 0) > 0:
                desconto_info = (
                    f" (DESC: R$ {float(item['desconto_item']):.2f})"
                )

            nome_linhas = []

            while len(nome) > 20:
                nome_linhas.append(nome[:20])
                nome = nome[20:]

            nome_linhas.append(nome)

            linhas.append(
                f"{qtd:<5}"
                f"{nome_linhas[0]:<20}"
                f"{desconto_info:<10}"
                f"{f'R$ {valor:.2f}':>15}"
            )

            for nome_extra in nome_linhas[1:]:
                linhas.append(
                    f"{'':<5}{nome_extra:<20}"
                )
    else:
        linhas.append(
            f"{'-':<5}{'Nenhum item':<20}{'R$ 0.00':>15}"
        )

    linhas.append("-" * largura)
    linhas.append(
        f"{'Total de itens':<33}{qtd_itens:>15}"
    )
    linhas.append(
        f"{'Quantidade':<33}{qtd_total:>15}"
    )
    linhas.append("-" * largura)

    linhas.append(
        f"{'Subtotal bruto':<33}"
        f"{f'R$ {subtotal:.2f}':>15}"
    )

    if desconto_total > 0:
        linhas.append(
            f"{'Descontos':<33}"
            f"{f'- R$ {desconto_total:.2f}':>15}"
        )

    linhas.append(
        f"{'Valor líquido':<33}"
        f"{f'R$ {valor_real:.2f}':>15}"
    )

    if cover > 0:
        linhas.append(
            f"{'Cover':<33}"
            f"{f'R$ {cover:.2f}':>15}"
        )

    if incluir_garcom:
        linhas.append(
            f"{'10% Garçom':<33}"
            f"{f'R$ {taxa_garcom:.2f}':>15}"
        )

    linhas.append("=" * largura)
    linhas.append(
        f"{'TOTAL':<33}{f'R$ {total:.2f}':>15}"
    )
    linhas.append("=" * largura)

    linhas.append("")
    linhas.append(
        "Obrigado pela preferência!".center(largura)
    )
    linhas.append(
        "Volte sempre!".center(largura)
    )
    linhas.append("")
    linhas.append("=" * largura)

    return "\n".join(linhas)


def _html_comanda_pedido(
    id_pedido,
    origem_venda,
    pedidos,
    taxa_entrega=0.0
):
    pedidos = _preparar_pedidos(pedidos)

    origem_nome = {
        "takeaway": "Takeaway",
        "delivery": "Delivery"
    }.get(
        str(origem_venda).lower(),
        str(origem_venda).capitalize()
    )

    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    if pedidos.empty:
        itens_html = """
        <div class="item">
            <div class="item-info">
                <span class="quantidade">-</span>
                <span class="nome">Nenhum item finalizado</span>
            </div>
            <span class="valor">R$ 0.00</span>
        </div>
        """

        subtotal = 0.0
        valor_real = 0.0
        desconto_total = 0.0
        qtd_itens = 0
        qtd_total = 0
    else:
        subtotal = float(pedidos["subtotal"].sum())
        valor_real = float(
            pedidos["valor_com_desconto"].sum()
        )
        desconto_total = subtotal - valor_real
        qtd_itens = len(pedidos)
        qtd_total = int(pedidos["quantidade"].sum())

        itens_html = ""

        for _, item in pedidos.iterrows():
            nome = html.escape(str(item["nome_prod"]))
            qtd = int(item["quantidade"])
            valor = float(item["valor_com_desconto"])

            desconto_info = ""

            if item.get("cortesia", False):
                desconto_info = " (CORTESIA)"
            elif item.get("desconto_tipo") == "devolucao":
                desconto_info = " (DEVOLUCAO)"
            elif item.get("desconto_item", 0) > 0:
                desconto_info = (
                    f" (DESC: R$ {float(item['desconto_item']):.2f})"
                )

            itens_html += f"""
            <div class="item">
                <div class="item-info">
                    <span class="quantidade">{qtd}x</span>
                    <span class="nome">{nome}{desconto_info}</span>
                </div>
                <span class="valor">R$ {valor:.2f}</span>
            </div>
            """

    total = valor_real + taxa_entrega

    desconto_html = f"""
    <div class="linha-total" style="color:#ff4444;">
        <span>Descontos</span>
        <strong>- R$ {desconto_total:.2f}</strong>
    </div>
    """ if desconto_total > 0 else ""

    taxa_html = f"""
    <div class="linha-total">
        <span>Taxa de entrega</span>
        <strong>R$ {taxa_entrega:.2f}</strong>
    </div>
    """ if taxa_entrega > 0 else ""

    return f"""
    <div class="comanda">
        <div class="cabecalho">
            <div class="titulo">COMANDA</div>
        </div>

        <div class="separador"></div>

        <div class="informacoes">
            <div>
                <span>Pedido</span>
                <strong>{html.escape(str(id_pedido))}</strong>
            </div>

            <div>
                <span>Origem</span>
                <strong>{html.escape(origem_nome)}</strong>
            </div>

            <div>
                <span>Data</span>
                <strong>{data_hora}</strong>
            </div>
        </div>

        <div class="separador"></div>

        <div class="itens-header">
            <span>ITEM</span>
            <span>VALOR</span>
        </div>

        <div class="itens">
            {itens_html}
        </div>

        <div class="separador"></div>

        <div class="resumo">
            <div>
                <span>Total de itens</span>
                <strong>{qtd_itens}</strong>
            </div>

            <div>
                <span>Quantidade</span>
                <strong>{qtd_total}</strong>
            </div>
        </div>

        <div class="linha-total">
            <span>Subtotal bruto</span>
            <strong>R$ {subtotal:.2f}</strong>
        </div>

        {desconto_html}

        <div class="linha-total" style="font-weight:bold;">
            <span>Valor líquido</span>
            <strong>R$ {valor_real:.2f}</strong>
        </div>

        {taxa_html}

        <div class="separador"></div>

        <div class="total">
            <span>TOTAL</span>
            <strong>R$ {total:.2f}</strong>
        </div>

        <div class="separador"></div>

        <div class="rodape">
            <strong>Obrigado pela preferência!</strong>
            <span>Volte sempre!</span>
        </div>
    </div>
    """


def _impressao_comanda_pedido(
    id_pedido,
    origem_venda,
    pedidos,
    taxa_entrega=0.0
):
    pedidos = _preparar_pedidos(pedidos)

    origem_nome = {
        "takeaway": "Takeaway",
        "delivery": "Delivery"
    }.get(
        str(origem_venda).lower(),
        str(origem_venda).capitalize()
    )

    if pedidos.empty:
        subtotal = 0.0
        valor_real = 0.0
        desconto_total = 0.0
        qtd_itens = 0
        qtd_total = 0
        sem_itens = True
    else:
        subtotal = float(pedidos["subtotal"].sum())
        valor_real = float(
            pedidos["valor_com_desconto"].sum()
        )
        desconto_total = subtotal - valor_real
        qtd_itens = len(pedidos)
        qtd_total = int(pedidos["quantidade"].sum())
        sem_itens = False

    total = valor_real + taxa_entrega

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    largura = 48
    linhas = []

    linhas.append("=" * largura)
    linhas.append("COMANDA".center(largura))
    linhas.append("=" * largura)

    linhas.append(f"Pedido:   {id_pedido}")
    linhas.append(f"Origem:   {origem_nome}")
    linhas.append(f"Data:     {data_hora}")

    linhas.append("-" * largura)
    linhas.append(f"{'QTD':<5}{'ITEM':<28}{'VALOR':>15}")
    linhas.append("-" * largura)

    if not sem_itens:
        for _, item in pedidos.iterrows():
            qtd = int(item["quantidade"])
            nome = str(item["nome_prod"])
            valor = float(item["valor_com_desconto"])

            desconto_info = ""

            if item.get("cortesia", False):
                desconto_info = " (CORTESIA)"
            elif item.get("desconto_tipo") == "devolucao":
                desconto_info = " (DEVOLUCAO)"
            elif item.get("desconto_item", 0) > 0:
                desconto_info = (
                    f" (DESC: R$ {float(item['desconto_item']):.2f})"
                )

            nome_linhas = []

            while len(nome) > 20:
                nome_linhas.append(nome[:20])
                nome = nome[20:]

            nome_linhas.append(nome)

            linhas.append(
                f"{qtd:<5}"
                f"{nome_linhas[0]:<20}"
                f"{desconto_info:<10}"
                f"{f'R$ {valor:.2f}':>15}"
            )

            for nome_extra in nome_linhas[1:]:
                linhas.append(
                    f"{'':<5}{nome_extra:<20}"
                )
    else:
        linhas.append(
            f"{'-':<5}{'Nenhum item':<20}{'R$ 0.00':>15}"
        )

    linhas.append("-" * largura)
    linhas.append(
        f"{'Total de itens':<33}{qtd_itens:>15}"
    )
    linhas.append(
        f"{'Quantidade':<33}{qtd_total:>15}"
    )
    linhas.append("-" * largura)

    linhas.append(
        f"{'Subtotal bruto':<33}"
        f"{f'R$ {subtotal:.2f}':>15}"
    )

    if desconto_total > 0:
        linhas.append(
            f"{'Descontos':<33}"
            f"{f'- R$ {desconto_total:.2f}':>15}"
        )

    linhas.append(
        f"{'Valor líquido':<33}"
        f"{f'R$ {valor_real:.2f}':>15}"
    )

    if taxa_entrega > 0:
        linhas.append(
            f"{'Taxa de entrega':<33}"
            f"{f'R$ {taxa_entrega:.2f}':>15}"
        )

    linhas.append("=" * largura)
    linhas.append(
        f"{'TOTAL':<33}{f'R$ {total:.2f}':>15}"
    )
    linhas.append("=" * largura)

    linhas.append("")
    linhas.append(
        "Obrigado pela preferência!".center(largura)
    )
    linhas.append(
        "Volte sempre!".center(largura)
    )
    linhas.append("")
    linhas.append("=" * largura)

    return "\n".join(linhas)


def _renderizar_estilo_comanda(conteudo):
    st.html(
        f"""
        <style>
            * {{ box-sizing: border-box; }}

            .comanda-container {{
                width: 100%;
                display: flex;
                justify-content: center;
                padding: 10px 0;
                background: transparent;
            }}

            .comanda {{
                width: 100%;
                max-width: 420px;
                padding: 24px 20px;
                background: #fff3a3;
                color: #000000;
                font-family: "Courier New", Courier, monospace;
                font-size: 13px;
                line-height: 1.4;
                border-radius: 10px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.12);
            }}

            .cabecalho {{
                text-align: center;
                padding: 4px 0;
            }}

            .titulo {{
                font-size: 25px;
                font-weight: bold;
                letter-spacing: 4px;
            }}

            .separador {{
                width: 100%;
                border-top: 1px dashed #000000;
                margin: 15px 0;
            }}

            .informacoes {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px 20px;
            }}

            .informacoes div {{
                display: flex;
                flex-direction: column;
                min-width: 0;
            }}

            .informacoes span {{
                font-size: 10px;
                font-weight: normal;
                text-transform: uppercase;
                margin-bottom: 2px;
            }}

            .informacoes strong {{
                font-size: 13px;
                font-weight: bold;
                overflow-wrap: anywhere;
            }}

            .itens-header {{
                display: flex;
                justify-content: space-between;
                font-size: 10px;
                font-weight: bold;
                text-transform: uppercase;
                margin-bottom: 5px;
            }}

            .item {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                width: 100%;
                gap: 10px;
                padding: 5px 0;
            }}

            .item-info {{
                display: flex;
                flex: 1;
                min-width: 0;
                gap: 8px;
            }}

            .quantidade {{
                flex-shrink: 0;
                font-weight: bold;
                min-width: 25px;
            }}

            .nome {{
                overflow-wrap: anywhere;
                word-break: break-word;
            }}

            .valor {{
                flex-shrink: 0;
                white-space: nowrap;
                font-weight: bold;
            }}

            .resumo {{
                display: flex;
                justify-content: space-between;
                width: 100%;
                margin-bottom: 12px;
            }}

            .resumo div {{
                display: flex;
                flex-direction: column;
            }}

            .resumo div:last-child {{
                text-align: right;
            }}

            .resumo span {{
                font-size: 10px;
                text-transform: uppercase;
            }}

            .resumo strong {{
                font-size: 13px;
            }}

            .linha-total {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                width: 100%;
                font-size: 13px;
                padding: 4px 0;
            }}

            .linha-total strong {{
                font-weight: bold;
            }}

            .total {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                width: 100%;
                font-weight: bold;
                padding-top: 7px;
            }}

            .total span {{
                font-size: 16px;
            }}

            .total strong {{
                font-size: 22px;
            }}

            .rodape {{
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                gap: 4px;
                font-size: 11px;
            }}

            .rodape strong {{
                font-size: 12px;
            }}

            @media print {{
                @page {{
                    margin: 0;
                    size: auto;
                }}

                html, body {{
                    margin: 0 !important;
                    padding: 0 !important;
                    background: transparent !important;
                }}

                .comanda-container {{
                    display: block;
                    padding: 0 !important;
                    margin: 0 !important;
                    background: transparent !important;
                }}

                .comanda {{
                    width: 100%;
                    max-width: none;
                    padding: 10px;
                    margin: 0;
                    background: transparent !important;
                    color: #000000 !important;
                    box-shadow: none !important;
                    border: none !important;
                    border-radius: 0 !important;
                }}
            }}
        </style>

        <div class="comanda-container">
            {conteudo}
        </div>
        """
    )


def renderizar_comanda(mesa_id, pedidos_df, mesas_df):
    mesa_id_str = str(mesa_id).strip()

    mesa_info = mesas_df[
        mesas_df["id_mesa"].astype(str).str.strip()
        == mesa_id_str
    ]

    if mesa_info.empty:
        st.error(f"Mesa {mesa_id} não encontrada.")
        return

    mesa_info = mesa_info.iloc[0]

    aberto_em = mesa_info["aberto_em"]
    fechado_em = mesa_info["fechado_em"]

    aberto_dt = parse_data_hora(aberto_em)
    fechado_dt = parse_data_hora(fechado_em)

    pedidos_mesa = pedidos_df[
        pedidos_df["id_mesa"].astype(str).str.strip()
        == mesa_id_str
    ].copy()

    if not pedidos_mesa.empty:
        pedidos_mesa["criado_dt"] = pd.to_datetime(
            pedidos_mesa["criado_em"],
            format="%d/%m/%Y %H:%M:%S",
            errors="coerce"
        )

        pedidos_filtrados = pedidos_mesa[
            (pedidos_mesa["criado_dt"] >= aberto_dt)
            &
            (pedidos_mesa["criado_dt"] <= fechado_dt)
        ]
    else:
        pedidos_filtrados = pd.DataFrame()

    incluir_garcom = mesa_info.get(
        "incluir_10",
        False
    )

    comanda = gerar_comanda(
        mesa_id,
        pedidos_filtrados,
        mesa_info,
        incluir_garcom
    )

    comanda_impressao = gerar_comanda_impressao(
        mesa_id,
        pedidos_filtrados,
        mesa_info,
        incluir_garcom
    )

    if not comanda or not comanda_impressao:
        return

    _renderizar_estilo_comanda(comanda)

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "🖨️ Imprimir Comanda",
            use_container_width=True,
            type="primary"
        ):
            impressora = st.session_state.get(
                "impressora_salao",
                ""
            )

            if not impressora:
                st.warning(
                    "⚠️ Nenhuma impressora do salão foi configurada."
                )
            else:
                sucesso = imprimir_ticket(
                    comanda_impressao,
                    impressora
                )

                if sucesso:
                    st.success(
                        f"✅ Comanda enviada para {impressora}!"
                    )
                else:
                    st.error(
                        f"❌ Não foi possível imprimir na impressora {impressora}."
                    )


def renderizar_comanda_pedido(id_pedido, pedidos_df):
    pedidos = pedidos_df[
        pedidos_df["id_pedido"].astype(str).str.strip()
        == str(id_pedido).strip()
    ].copy()

    if pedidos.empty:
        st.warning(
            f"Pedido {id_pedido} não encontrado."
        )
        return

    origem_venda = str(
        pedidos["origem_venda"].iloc[0]
    ).lower()

    if origem_venda not in ["takeaway", "delivery"]:
        st.error(
            "Esta função é destinada apenas para Takeaway ou Delivery."
        )
        return

    taxa_entrega = 0.0

    if origem_venda == "delivery" and "taxa_entrega" in pedidos.columns:
        taxa_entrega = float(
            pd.to_numeric(
                pedidos["taxa_entrega"],
                errors="coerce"
            ).fillna(0).iloc[0]
        )

    comanda = _html_comanda_pedido(
        id_pedido,
        origem_venda,
        pedidos,
        taxa_entrega
    )

    comanda_impressao = _impressao_comanda_pedido(
        id_pedido,
        origem_venda,
        pedidos,
        taxa_entrega
    )

    _renderizar_estilo_comanda(comanda)

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "🖨️ Imprimir Comanda",
            use_container_width=True,
            type="primary",
            key=f"imprimir_comanda_{id_pedido}"
        ):
            impressora = st.session_state.get(
                "impressora_salao",
                ""
            )

            if not impressora:
                st.warning(
                    "⚠️ Nenhuma impressora do salão foi configurada."
                )
            else:
                sucesso = imprimir_ticket(
                    comanda_impressao,
                    impressora
                )

                if sucesso:
                    st.success(
                        f"✅ Comanda enviada para {impressora}!"
                    )
                else:
                    st.error(
                        f"❌ Não foi possível imprimir na impressora {impressora}."
                    )