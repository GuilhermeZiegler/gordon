from install.popular_historico_pedidos import popular_historico_pedidos
from install.popular_historico_delivery import popular_historico_delivery
from install.popular_historico_mesas import popular_historico_mesas
from install.popular_historico_estoque import popular_historicos_estoque
from install.popular_historico_caixa import popular_historico_caixa


def seed_all():
    popular_historico_pedidos()
    popular_historico_delivery()
    popular_historico_mesas()
    popular_historicos_estoque()
    popular_historico_caixa()
    print("Seed completo.")


if __name__ == "__main__":
    seed_all()