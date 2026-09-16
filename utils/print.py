import socket
import os
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