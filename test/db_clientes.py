from test._common import separador, mostrar_tabela
from utils.db import ler_tabela
import pandas as pd


def run():
    separador("CLIENTES")

    df = ler_tabela("clientes")
    print(f"  total: {len(df)}")

    if df.empty:
        return

    lat = df["latitude"].astype(str).str.strip().replace("nan", "").replace("None", "")
    com_coord = (lat != "").sum()
    sem_coord = (lat == "").sum()

    print(f"  com coordenadas: {com_coord}")
    print(f"  sem coordenadas: {sem_coord}")

    separador("CLIENTES — cadastrados hoje")
    if "data_cadastro" in df.columns:
        df["data_cadastro_dt"] = pd.to_datetime(df["data_cadastro"], errors="coerce")
        hoje = df[df["data_cadastro_dt"].dt.date == pd.Timestamp.now().date()]
        mostrar_tabela(hoje, ["id_cliente", "nome_cliente", "telefone_principal", "bairro", "cidade", "data_cadastro"])

    separador("CLIENTES — últimos 10 cadastrados")
    if "data_cadastro" in df.columns:
        df_ord = df.sort_values("data_cadastro", ascending=False).head(10)
        mostrar_tabela(df_ord, ["id_cliente", "nome_cliente", "telefone_principal", "bairro", "latitude", "longitude"])