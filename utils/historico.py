import pickle
import os
from datetime import datetime

def carregar_historico(caminho):
    if os.path.exists(caminho):
        with open(caminho, 'rb') as f:
            return pickle.load(f)
    return []

def salvar_historico(caminho, dados):
    with open(caminho, 'wb') as f:
        pickle.dump(dados, f)

def adicionar_ao_historico(caminho, novo_item):
    historico = carregar_historico(caminho)
    historico.append(novo_item)
    salvar_historico(caminho, historico)