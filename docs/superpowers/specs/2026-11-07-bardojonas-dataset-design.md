# Bar do Jonas — Dataset e Análise Académica (desenho aprovado)

**Data:** 2026-11-07
**Responsável:** Marcelo Santos
**Repositório:** `marcelo-m7/bardojonas`

## Objetivo

Publicar um dataset académico verificável, inspirado nas entidades de catálogo e operações do BotecoPRO, para análise exploratória com Python/Pandas na UC Análise de Dados e Visualização da Informação. Recolher novos dados reais do bar de forma incremental, sem fabricar vendas históricas.

## Origem e limitações

- Fonte primária privada fornecida pelo titular: demonstrativo de rentabilidade do Bar do Jonas, intitulado `Demonstrativo 24_11_2019 a 24_12_2019.xlsx`.
- A aba `NOVEMBRO` contém 59 linhas de produto/fornecedor, 50 designações distintas, das quais 29 linhas referentes a cervejas e 22 produtos de cerveja distintos com compras positivas.
- Nas abas `DEZEMBRO`, `JANEIRO` e `FEVEREIRO` há repetições idênticas. As compras de cervejas também repetem exatamente os números de novembro. Não serão tratadas como períodos mensais independentes.
- O ficheiro regista compras em packs, custo, preço unitário de venda e receita/lucro **potenciais** para a venda integral dessas unidades. Não contém transações de venda verificadas.
- A designação temporal resulta do nome do ficheiro, não de uma data individual por linha. Não serão imputadas datas diárias fictícias.
- Os dados atuais são limitados para séries temporais e inferências sobre procura. Essa limitação será explícita no notebook; a análise temporal depende de futuros registos reais.

## Abordagem escolhida

**B — base histórica + recolha incremental real**, escolhida pelo utilizador. A opção A (somente histórico estático) restringe a análise à comparação de produtos e custos; integração direta com BotecoPRO/Odoo foi preterida nesta fase para garantir execução académica autónoma e não depender de sistemas privados.

## Entregáveis

1. `data/public/compras_2019.csv`: snapshot revisto, com uma linha por produto/fornecedor e referências à linha original. Inclui quantidade de packs, unidades por pack, custo total, preço de venda unitário, receita potencial e margem potencial; sem dados pessoais.
2. `data/public/cervejas.csv`: catálogo normalizado das 22 referências efetivamente adquiridas, com marca, denominação e volume. Dados desconhecidos (ex. teor alcoólico) permanecem ausentes.
3. `data/coleta/vendas_diarias_modelo.csv`: apenas cabeçalho para registos futuros (`data,sku,quantidade_vendida,preco_unitario_brl,origem_registo`); nunca pré-preencher transações inventadas.
4. `database/schema.sql` e `scripts/import_sqlite.py`: tabelas relacionais `produtos`, `fornecedores`, `compras` e `vendas_diarias`, com chaves, unidades coerentes e ligações, sem misturar compras e vendas.
5. `notebooks/analise_bardojonas.ipynb`: notebook reprodutível a partir dos CSVs públicos, com limpeza, joins, groupby/pivot, estatística uni e multivariada, gráficos e interpretação, declaração de IA e limitações.
6. `README.md`, `requirements.txt`, `tests/`: instruções, dicionário de dados, proveniência, verificações e fluxo de atualização.

## Política de publicação

- O repositório é **público**. Nunca publicar o XLSX original, CNPJ, contacto, e-mail, dados laborais/remuneração, credenciais ou dados de clientes.
- Anonimizar referências a pessoas físicas identificáveis nos fornecedores, preservando um identificador estável.
- Publicar apenas as colunas comerciais estritamente necessárias à análise. Registar origem no README e no CSV sem expor o ficheiro bruto.
- Não converter `receita_potencial_brl` em `vendas_reais` nem contar uma compra de 12 unidades como 12 transações independentes.
- O dataset derivado ficará acessível publicamente; a avaliação da suficiência do dataset e da proveniência cabe ao docente.
- Incluir declaração sobre ferramentas de IA no início do notebook, conforme o enunciado.

## Critérios de aceitação

- Os 59 registos comerciais de novembro são preservados sem duplicação das abas copiadas.
- O catálogo tem 22 SKUs de cerveja com compras positivas, e o total de unidades de cerveja é 3.948.
- Reconciliação das cervejas: custo R$ 16.706,60, receita **potencial** R$ 24.936,00 e margem bruta **potencial** R$ 8.229,40 (antes de despesas).
- Dados monetários e quantidades tipados como números; ausência de dados distinguida de zero e erros de fórmula não transportados.
- A execução integral do notebook funciona numa sessão limpa, com caminhos relativos.
- O modelo de recolha não contém vendas fictícias e rejeita datas/quantidades inválidas.
- A pesquisa por informações pessoais no conteúdo publicável é negativa.
- Trabalho entregue numa branch separada e PR em rascunho, sem merge automático.
