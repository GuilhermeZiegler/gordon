from test import db_overview
from test import db_hoje
from test import db_pedidos
from test import db_caixa
from test import db_mesas
from test import db_clientes
from test import db_produtos
from test import db_movimentacoes
from test import db_delivery


def main():
    db_overview.run()
    db_hoje.run()
    db_pedidos.run()
    db_caixa.run()
    db_mesas.run()
    db_clientes.run()
    db_produtos.run()
    db_movimentacoes.run()
    db_delivery.run()


if __name__ == "__main__":
    main()