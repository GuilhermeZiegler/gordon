import os
import socket
import textwrap
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

try:
    import win32print
    _WIN32 = True
except ImportError:
    win32print = None
    _WIN32 = False


def _parse_endereco(endereco):
    if not endereco:
        return None

    endereco = str(endereco).strip()

    if ":" in endereco:
        host, porta = endereco.rsplit(":", 1)
        try:
            return host.strip(), int(porta.strip())
        except ValueError:
            return None

    return endereco, 9100


def imprimir_rede(texto, endereco, timeout=5):
    parsed = _parse_endereco(endereco)

    if not parsed:
        return False

    host, porta = parsed

    try:
        with socket.create_connection((host, porta), timeout=timeout) as s:
            s.sendall(texto.encode("cp850", errors="replace"))
        return True
    except Exception as e:
        print(f"[print] falha socket {host}:{porta}: {e}")
        return False


def imprimir_ticket(texto, endereco=None):
    if endereco:
        if imprimir_rede(texto, endereco):
            return True

    if _WIN32:
        try:
            nome = endereco or win32print.GetDefaultPrinter()
            if nome:
                hprinter = win32print.OpenPrinter(nome)
                try:
                    win32print.StartDocPrinter(hprinter, 1, ("Ticket", None, "RAW"))
                    win32print.StartPagePrinter(hprinter)
                    win32print.WritePrinter(hprinter, texto.encode("cp850", errors="replace"))
                    win32print.EndPagePrinter(hprinter)
                    win32print.EndDocPrinter(hprinter)
                finally:
                    win32print.ClosePrinter(hprinter)
                return True
        except Exception as e:
            print(f"[print] falha win32print: {e}")

    return gerar_pdf(texto)


def listar_impressoras():
    if not _WIN32:
        return []

    try:
        impressoras = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        return [p[2] for p in impressoras]
    except Exception as e:
        print(f"Erro ao listar impressoras: {e}")
        return []


def gerar_pdf(texto):
    try:
        os.makedirs("data/tickets", exist_ok=True)

        arquivo = os.path.join(
            "data",
            "tickets",
            f"teste_impressao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        largura = 80 * 2.83465
        margem = 5 * 2.83465
        fonte_tamanho = 9
        altura_linha = 4.5 * 2.83465

        linhas = []

        for linha in textwrap.dedent(texto).strip().splitlines():
            linha = linha.rstrip()

            if not linha:
                linhas.append("")
                continue

            while stringWidth(linha, "Courier", fonte_tamanho) > largura - (margem * 2):
                limite = max(
                    1,
                    int(
                        len(linha)
                        * (largura - margem * 2)
                        / stringWidth(linha, "Courier", fonte_tamanho)
                    )
                )
                linhas.append(linha[:limite])
                linha = linha[limite:]

            linhas.append(linha)

        altura = (len(linhas) * altura_linha) + (margem * 2)

        pdf = canvas.Canvas(
            arquivo,
            pagesize=(largura, altura)
        )

        pdf.setFont("Courier", fonte_tamanho)

        y = altura - margem - fonte_tamanho

        for linha in linhas:
            pdf.drawString(margem, y, linha)
            y -= altura_linha

        pdf.save()

        print(f"PDF gerado: {arquivo}")
        return True

    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        return False


def gerar_ticket_pedido(pedido_id, mesa, itens, observacao_global=""):
    if not itens:
        return None

    ticket = f"""
========================================
               PEDIDO
========================================
Pedido: {pedido_id}
Mesa: {mesa}
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
----------------------------------------
"""

    for item in itens:
        ticket += f"{item['quantidade']:>2}x {item['nome_prod']}"

        if item.get("observacao"):
            ticket += f"  (obs: {item['observacao']})"

        ticket += "\n"

    if observacao_global:
        ticket += f"\nObservacoes: {observacao_global}\n"

    ticket += """
----------------------------------------
========================================
"""

    return ticket


def gerar_ticket_cozinha(pedido_id, mesa, itens, observacao_global=""):
    itens_cozinha = [
        item for item in itens
        if item.get('tipo_venda', 'menu') == 'menu'
    ]

    if not itens_cozinha:
        return None

    ticket = f"""
========================================
               COZINHA
========================================
Pedido: {pedido_id}
Mesa: {mesa}
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
----------------------------------------
"""

    for item in itens_cozinha:
        ticket += f"{item['quantidade']:>2}x {item['nome_prod']}"

        if item.get("observacao"):
            ticket += f"  (obs: {item['observacao']})"

        ticket += "\n"

    if observacao_global:
        ticket += f"\nObservacoes: {observacao_global}\n"

    ticket += """
----------------------------------------
========================================
"""

    return ticket


def gerar_ticket_bar(pedido_id, mesa, itens, observacao_global=""):
    itens_bar = [
        item for item in itens
        if item.get('tipo_venda', '') in ['bar', 'ambos']
    ]

    if not itens_bar:
        return None

    ticket = f"""
========================================
                 BAR
========================================
Pedido: {pedido_id}
Mesa: {mesa}
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
----------------------------------------
"""

    for item in itens_bar:
        ticket += f"{item['quantidade']:>2}x {item['nome_prod']}"

        if item.get("observacao"):
            ticket += f"  (obs: {item['observacao']})"

        ticket += "\n"

    if observacao_global:
        ticket += f"\nObservacoes: {observacao_global}\n"

    ticket += """
----------------------------------------
========================================
"""

    return ticket


def gerar_ticket_cancelamento(pedido_id, mesa, itens, local="COZINHA"):
    if not itens:
        return None

    ticket = f"""
========================================
         CANCELAMENTO - {local}
========================================
Pedido: {pedido_id}
Mesa: {mesa}
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
----------------------------------------
"""

    for item in itens:
        ticket += f"{item['quantidade']:>2}x {item['nome_prod']}"

        if item.get("observacao"):
            ticket += f"  (obs: {item['observacao']})"

        ticket += "\n"

    ticket += """
----------------------------------------
========================================
"""

    return ticket


def salvar_ticket_arquivo(ticket, pedido_id, itens=None, observacao_global="", mesa=""):
    try:
        pasta = "data/tickets/cozinha"
        os.makedirs(pasta, exist_ok=True)

        filename = (
            f"{pasta}/"
            f"ticket_{pedido_id}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(ticket)

        return filename

    except Exception as e:
        print(f"Erro ao salvar ticket: {e}")
        return None


def salvar_ticket_bar_arquivo(ticket, pedido_id, itens=None, observacao_global="", mesa=""):
    try:
        pasta = "data/tickets/bar"
        os.makedirs(pasta, exist_ok=True)

        filename = (
            f"{pasta}/"
            f"ticket_bar_{pedido_id}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(ticket)

        return filename

    except Exception as e:
        print(f"Erro ao salvar ticket: {e}")
        return None