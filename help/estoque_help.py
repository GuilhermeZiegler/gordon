help_id_insumo = """
**ID do Insumo**

| Campo | Descrição |
|-------|-----------|
| Formato | INS-001 |
| Uso | Identificador único do insumo |
"""

help_nome = """
**Nome do Insumo**

| Campo | Descrição |
|-------|-----------|
| Obrigatório | Sim |
| Exemplo | Carne Moída |
| Uso | Identificação do insumo no sistema |
"""

help_categoria_insumo = """
**Categoria do Insumo**

| Campo | Descrição |
|-------|-----------|
| Obrigatório | Sim |
| Exemplo | Carnes, Frios, Padaria |
| Uso | Agrupar insumos por tipo |
"""

help_unidade_compra = """
**Unidade de Compra**

| Campo | Descrição |
|-------|-----------|
| Valores | kg, g, L, ml, un, cx, pct |
| Uso | Define a unidade de medição do insumo |
"""

help_preco_unitario = """
**Preço Unitário**

| Campo | Descrição |
|-------|-----------|
| Valores | R$ |
| Uso | Custo do insumo por unidade |
"""

help_botao_salvar = """
**Salvar Insumo**

| Requisito | Descrição |
|-----------|-----------|
| Campos | Todos obrigatórios |
| Ação | Adiciona novo insumo ao estoque |
"""

help_botao_alterar = """
**Alterar Insumo**

| Requisito | Descrição |
|-----------|-----------|
| Informe | ID do insumo a ser alterado |
| Ação | Atualiza dados do insumo existente |
"""

help_botao_deletar = """
**Deletar Insumo**

| Requisito | Descrição |
|-----------|-----------|
| Informe | ID do insumo a ser removido |
| Atenção | Ação irreversível |
"""

help_botao_limpar = """
**Limpar Formulário**

| Ação | Descrição |
|------|-----------|
| Remove | Todos os dados preenchidos |
| Útil | Para começar um novo cadastro |
"""

help_inventario = """
📝 **Inventário**

| Etapa | Descrição |
|-------|-----------|
| 1 | Conta fisicamente o estoque de um insumo |
| 2 | Informa a quantidade real contada |
| 3 | Sistema calcula a divergência entre estoque e inventário |
| 4 | Inventário é atualizado para o valor informado |
| 5 | Divergência é registrada para análise |
"""

help_itens = {
    'id_insumo': help_id_insumo,
    'nome': help_nome,
    'categoria_insumo': help_categoria_insumo,
    'unidade_compra': help_unidade_compra,
    'preco_unitario': help_preco_unitario,
    'botao_salvar': help_botao_salvar,
    'botao_alterar': help_botao_alterar,
    'botao_deletar': help_botao_deletar,
    'botao_limpar': help_botao_limpar,
    'help_inventario': help_inventario
}