import random

from install.seed.ceps import CEPS_UBATUBA

NOMES = [
    'Ana', 'Beatriz', 'Bruno', 'Carlos', 'Camila', 'Carla', 'Daniel', 'Daniela',
    'Diego', 'Eduarda', 'Eduardo', 'Felipe', 'Fernanda', 'Gabriel', 'Gabriela',
    'Gustavo', 'Helena', 'Igor', 'Isabela', 'João', 'Juliana', 'Larissa',
    'Leonardo', 'Leticia', 'Lucas', 'Luiza', 'Marcos', 'Mariana', 'Mateus',
    'Nathalia', 'Nicolas', 'Patricia', 'Paulo', 'Rafael', 'Renata', 'Ricardo',
    'Roberta', 'Rodrigo', 'Sabrina', 'Sofia', 'Thiago', 'Vanessa', 'Vinicius',
    'Amanda', 'André', 'Bruna', 'Caio', 'Carolina', 'Davi', 'Emily',
    'Enzo', 'Fábio', 'Giovana', 'Guilherme', 'Heloisa', 'Ivan', 'Jéssica',
    'Julia', 'Kaique', 'Lara', 'Manuela', 'Murilo', 'Otávio',
    'Pedro', 'Priscila', 'Rebeca', 'Samuel', 'Sara', 'Tomás', 'Valentina',
    'Vitor', 'Yasmin', 'Alice', 'Arthur', 'Bianca', 'Cecília',
    'Emanuelly', 'Fernando', 'Gael', 'Heitor', 'Isadora', 'Joaquim',
    'Laura', 'Lorenzo', 'Maria', 'Noah', 'Oliver', 'Ravi', 'Théo', 'Zoe'
]

SOBRENOMES = [
    'Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves',
    'Pereira', 'Lima', 'Gomes', 'Costa', 'Ribeiro', 'Martins', 'Carvalho',
    'Almeida', 'Lopes', 'Soares', 'Fernandes', 'Vieira', 'Barbosa', 'Rocha',
    'Dias', 'Nascimento', 'Andrade', 'Moreira', 'Nunes', 'Marques', 'Machado',
    'Mendes', 'Freitas', 'Cardoso', 'Ramos', 'Gonçalves', 'Santana',
    'Teixeira', 'Araújo', 'Correia', 'Cavalcanti', 'Monteiro', 'Moura',
    'Batista', 'Pinto', 'Duarte', 'Campos', 'Cunha', 'Miranda', 'Reis',
    'Borges', 'Neves', 'Pacheco'
]

REFERENCIAS = [
    'Próximo ao mercado', 'Ao lado da praça', 'Em frente à escola',
    'Perto da padaria', 'Após o posto de gasolina', 'Antes da ponte',
    'Ao lado do campo', 'Próximo à igreja', 'Em frente ao hospital',
    'Na esquina', 'Ao lado do bar', 'Perto da praia', ''
]

COMPLEMENTOS = ['', '', '', 'Casa', 'Apto 101', 'Apto 202', 'Bloco A', 'Fundos']

CIDADE = 'Ubatuba'
ESTADO = 'SP'


def gerar_clientes(quantidade=200):
    random.seed(42)

    clientes = []
    nomes_usados = set()

    while len(clientes) < quantidade:
        nome = f"{random.choice(NOMES)} {random.choice(SOBRENOMES)}"

        if nome in nomes_usados:
            continue
        nomes_usados.add(nome)

        num_id = len(clientes) + 1
        id_cliente = f"CLI-{num_id:03d}"

        cep, logradouro, bairro = random.choice(CEPS_UBATUBA)
        numero = random.randint(1, 2000)

        telefone_ddd = random.choice([12, 11, 13])
        telefone = f"({telefone_ddd}) {random.randint(90000, 99999)}-{random.randint(1000, 9999)}"

        tem_sec = random.random() < 0.25
        telefone_sec = (
            f"({telefone_ddd}) {random.randint(90000, 99999)}-{random.randint(1000, 9999)}"
            if tem_sec else ''
        )

        email_local = (
            nome.lower()
            .replace(' ', '.')
            .replace('á', 'a').replace('ã', 'a').replace('â', 'a')
            .replace('é', 'e').replace('ê', 'e')
            .replace('í', 'i')
            .replace('ó', 'o').replace('õ', 'o').replace('ô', 'o')
            .replace('ú', 'u')
            .replace('ç', 'c')
        )
        email = f"{email_local}{num_id}@email.com"

        clientes.append({
            'id_cliente': id_cliente,
            'nome_cliente': nome,
            'telefone_principal': telefone,
            'telefone_secundario': telefone_sec,
            'email': email,
            'cep': cep,
            'logradouro': logradouro,
            'numero': str(numero),
            'complemento': random.choice(COMPLEMENTOS),
            'bairro': bairro,
            'cidade': CIDADE,
            'estado': ESTADO,
            'referencia': random.choice(REFERENCIAS),
            'data_cadastro': f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d} 10:00:00",
            'ativo': True,
            'latitude': '',
            'longitude': ''
        })

    return clientes


CLIENTES = gerar_clientes(200)