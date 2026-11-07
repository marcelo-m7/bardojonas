# Bar do Jonas — análise de dados reais de produtos e abastecimento

Este repositório contém um conjunto de dados comerciais históricos do **Bar do Jonas**,
em Maria Ortiz, Vitória (ES), e um projeto académico de **Análise de Dados e Visualização
da Informação** da Universidade do Algarve.

**Autor:** Marcelo Santos — a79433@ualg.pt
**Projeto relacionado:** [BotecoPRO](https://github.com/marcelo-m7/BotecoPRO)
(inspiração para as entidades; nenhuma dependência operacional de Odoo).

## O que os dados realmente mostram

| Controlo do demonstrativo histórico | Valor |
| --- | ---: |
| Linhas de produto e fornecedor | 59 |
| Produtos comerciais distintos | 50 |
| Linhas referentes a cervejas | 29 |
| Cervejas distintas adquiridas | 22 |
| Unidades de cervejas adquiridas | 3.948 |
| Custo de compra das cervejas | R$ 16.706,60 |
| Receita *potencial* se todas as unidades fossem vendidas | R$ 24.936,00 |
| Margem bruta *potencial*, antes de despesas | R$ 8.229,40 |

**Importante:** o demonstrativo contém produtos comprados, fornecedores, custos e
preços de tabela. A receita potencial é calculada como `unidades_compradas ×
preco_venda_unitario_brl`. O ficheiro **não** contém registos de venda individual,
faturação confirmada nem datas diárias por produto. Nunca interpretar estes totais
como vendas ou lucro líquido realizado.

### Proveniência

Fonte primária: demonstrativo de rentabilidade do estabelecimento, disponibilizado
pelo titular e identificado no original pelo período **24/11/2019 a 24/12/2019**.
O snapshot comercial foi extraído exclusivamente da aba `NOVEMBRO`. A duplicação
das tabelas em `DEZEMBRO`, `JANEIRO` e `FEVEREIRO` não permite inferir quatro
meses independentes. O rótulo temporal do original não equivale a uma data
observada em cada linha.

Este repositório **público** disponibiliza apenas uma versão derivada e anonimizada
das colunas comerciais necessárias à análise. O XLSX original não é distribuído
porque inclui dados empresariais de contacto e informações laborais alheias ao estudo.
Nomes pessoais que constavam como fornecedores foram substituídos por identificadores
genéricos. A linha original é referenciada por `source_sheet` e `source_row`, para
facilitar auditorias internas.

Os CSVs são livremente acessíveis para consulta académica neste repositório. A
utilização do dataset e a declaração de IA devem ser apresentadas no trabalho.
A adequação da dimensão e proveniência do conjunto de dados às regras da UC
deve ser confirmada com o docente.

## Estrutura

| Caminho | Utilização |
| --- | --- |
| [`data/public/compras_2019.csv`](data/public/compras_2019.csv) | Snapshot de 59 linhas de compras por produto/fornecedor |
| [`data/public/cervejas.csv`](data/public/cervejas.csv) | Catálogo normalizado de 22 SKUs adquiridos |
| [`data/coleta/vendas_diarias_modelo.csv`](data/coleta/vendas_diarias_modelo.csv) | Cabeçalho de recolha futura; **zero vendas fictícias** |
| [`database/schema.sql`](database/schema.sql) | Modelo relacional de produtos, fornecedores, compras e vendas diárias |
| [`notebooks/analise_bardojonas.ipynb`](notebooks/analise_bardojonas.ipynb) | Notebook exploratório e interpretativo |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | Definições, unidades e regras de normalização |
| `scripts/` | Extração opcional, importação SQLite, validação e construção do notebook |
| `tests/` | Reconciliação, integridade, execução e privacidade |

## Como executar

Requisitos: **Python 3.11+**, Jupyter e as bibliotecas em `requirements.txt`.
Na raiz do projeto:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
jupyter notebook notebooks/analise_bardojonas.ipynb
```

No Windows, ativar o ambiente virtual com `.venv\Scripts\activate`.
Executar todas as células do notebook desde o início. O trabalho lê apenas os CSVs
em `data/public/`, com caminhos relativos; não precisa de credenciais, internet,
Odoo ou do demonstrativo privado.

Para recriar o modelo relacional local, sem alterar os dados publicados:

```bash
python scripts/import_sqlite.py --db output/bardojonas.sqlite3
```

O SQLite armazena valores monetários em **centavos inteiros**, evitando erros
de arredondamento de ponto flutuante. O importador é idempotente.

### Reprocessamento opcional do original privado

Somente o titular do estabelecimento, com acesso à fonte, pode executar:

```bash
python scripts/build_dataset.py --source "/caminho/privado/demonstrativo.xlsx" --output data/public
python scripts/create_notebook.py
```

Não publicar o original, uma cópia não anonimizada, ficheiros de salários,
contactos ou dados pessoais. A reprodução académica normal **não exige** esta etapa:
os CSVs tratados acompanham o projeto.

## Recolher vendas reais daqui em diante

1. Copiar o modelo `data/coleta/vendas_diarias_modelo.csv` para
   `data/coleta/vendas_diarias.csv` (este último está ignorado pelo Git).
2. Registar **uma linha por dia, SKU e fonte de registo**, com:
   - `data`: `AAAA-MM-DD`, correspondente ao dia realmente observado;
   - `sku`: identificador existente em `data/public/cervejas.csv`;
   - `quantidade_vendida`: número inteiro positivo de unidades realmente vendidas;
   - `preco_unitario_brl`: preço efetivamente praticado, com ponto decimal;
   - `origem_registo`: referência verificável, como caderno, caixa ou POS.
3. Validar as observações antes de as utilizar:

```bash
python -m scripts.validate_sales data/coleta/vendas_diarias.csv
python scripts/import_sqlite.py --db output/bardojonas.sqlite3 --sales data/coleta/vendas_diarias.csv
```

O notebook passa a mostrar uma série temporal apenas quando esse ficheiro
contém **registos observados válidos**. Não adicionar datas estimadas, séries
geradas por IA ou vendas deduzidas das compras.

## Verificação e limites

- Os testes reconciliam as 59 linhas, os 22 SKUs de cervejas, as 3.948 unidades e
  os três totais monetários identificados.
- Testam duplicação de fornecedores, idempotência, validação de vendas e exclusão
  de dados pessoais do dataset público.
- O notebook inclui limpeza, junção, agrupamentos, tabela cruzada, estatística
  descritiva e correlação de Spearman, visualizações e interpretação crítica.
- A correlação envolve apenas 22 produtos: não autoriza inferência causal ou
  extrapolação para o comércio local.
- Uma análise temporal de vendas não é possível sem dados adicionais reais;
  essa ausência é reportada explicitamente.
- Duas cachaças de recipientes de 5 litros aparecem com 70 unidades comerciais
  por recipiente: o volume indicado é o da **embalagem de origem**, e não de
  uma dose individual. O volume de eventual porção vendida é desconhecido.

Na [GitHub Actions](.github/workflows/verify.yml), os testes também executam
o notebook num kernel Jupyter limpo e verificam que o ficheiro gerado está atualizado.
Em ambientes que proíbem sockets ZeroMQ, o teste local executa as células
sequencialmente num namespace Python novo e verifica os gráficos.

**Uso de IA:** a declaração exigida pelo enunciado está na primeira célula do
notebook; o autor deve compreender e validar os resultados antes de submeter.
