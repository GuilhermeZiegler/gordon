import os

def get_data_dir():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def get_caminhos():
    data_dir = get_data_dir()
    return {
        "produtos": os.path.join(data_dir, "produtos.pkl"),
        "mesas": os.path.join(data_dir, "mesas.pkl"),
        "pedidos": os.path.join(data_dir, "pedidos.pkl"),
        "insumos": os.path.join(data_dir, "insumos.pkl"),
        "ficha": os.path.join(data_dir, "ficha_tecnica.pkl"),
        "movimentacoes": os.path.join(data_dir, "movimentacoes.pkl"),
        "historico_pedidos": os.path.join(data_dir, "historico_pedidos.pkl"),
        "funcionarios": os.path.join(data_dir, "funcionarios.pkl"),
        "config": os.path.join(data_dir, "config.json"),
        "caixa": os.path.join(data_dir, "caixa.pkl"),
    }