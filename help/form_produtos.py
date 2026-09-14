help_cod_prod = """
**Código único do produto**

| Formato | Exemplo |
|---------|---------|
| CAT-XXX | BUR-001, PIZ-002, REF-003 |
"""

help_nome = """
**Nome completo do produto**

| Exemplos |
|----------|
| Hambúrguer Duplo |
| Pizza Margherita |
| Coca-Cola 2L |
| Batata Frita Especial |
"""

help_desc = """
**Descrição detalhada do produto**

| Exemplos |
|----------|
| Pão, hambúrguer 180g, queijo cheddar, bacon, molho especial |
| Molho de tomate, mussarela, manjericão, azeite |
"""

help_tipo = """
**Tipo do produto**

| Tipo | Descrição |
|------|-----------|
| menu | Prato principal ou combo |
| adicional | Complementos e adicionais |
| bebida | Bebidas em geral |
| sobremesa | Doces e sobremesas |
| entrada | Aperitivos e entradas |
| acompanhamento | Guarnições e acompanhamentos |
| molho | Molhos especiais |
| porcao | Porções para compartilhar |
"""

help_categoria = """
**Categoria específica do produto**

| Categoria | Subcategorias |
|-----------|---------------|
| Hambúrgueres | Clássico, Duplo, Bacon, Vegano, Frango |
| Pizzas | Margherita, Calabresa, Frango, 4 Queijos |
| Pratos Feitos | Executivo, Prato do Dia, Parmegiana |
| Refrigerantes | Coca-Cola, Pepsi, Guaraná, Fanta, Sprite |
| Sucos | Laranja, Limão, Uva, Morango, Maracujá |
| Cervejas | Pilsen, IPA, Witbier, Stout, Lager |
| Vinhos | Tinto, Branco, Rosé, Espumante |
| Porções | Fritas, Onion Rings, Calabresa, Frango |
| Saladas | Verde, Caesar, Grega, Primavera |
| Sobremesas | Pudim, Mousse, Sorvete, Torta, Petit Gateau |
| Entradas | Pastéis, Bolinhos, Bruschetta, Polenta |
"""

help_p_venda = """
**Preço de venda ao cliente**

| Regra | Exemplo |
|-------|---------|
| Use números com duas casas decimais | 45.90, 32.00, 12.50 |
"""

help_p_custo = """
**Preço de custo do produto**

| Regra | Exemplo |
|-------|---------|
| Use números com duas casas decimais | 12.50, 8.75, 3.90 |
| Margem é calculada automaticamente | - |
"""

help_botao_salvar = """
**Salvar novo produto**

| Requisito | Descrição |
|-----------|-----------|
| Campos obrigatórios | Código e Nome |
| Ação | Produto será adicionado à lista |
"""

help_botao_alterar = """
**Alterar produto existente**

| Requisito | Descrição |
|-----------|-----------|
| Informe | CÓDIGO do produto a ser alterado |
| Ação | Produto será substituído pelo novo registro |
"""

help_botao_deletar = """
**Deletar produto**

| Requisito | Descrição |
|-----------|-----------|
| Informe | CÓDIGO do produto a ser removido |
| Atenção | Ação irreversível |
"""

help_botao_limpar = """
**Limpar formulário**

| Ação | Descrição |
|------|-----------|
| Remove | Todos os dados preenchidos |
| Útil | Para começar um novo cadastro |
"""

help_itens = {
    'cod_prod': help_cod_prod,
    'nome': help_nome,
    'desc': help_desc,
    'tipo': help_tipo,
    'categoria': help_categoria,
    'p_venda': help_p_venda,
    'p_custo': help_p_custo,
    'botao_salvar': help_botao_salvar,
    'botao_alterar': help_botao_alterar,
    'botao_deletar': help_botao_deletar,
    'botao_limpar': help_botao_limpar
}