# Dicionário de dados e proveniência

## Unidade de observação

`compras_2019.csv` contém uma linha por **produto–fornecedor** no snapshot da
aba `NOVEMBRO`. Várias linhas do mesmo produto são aquisições a fornecedores
distintos, não duplicados automáticos. Uma linha com 12 unidades **não** equivale
a 12 transações independentes. O snapshot não tem data por linha.

## `data/public/compras_2019.csv`

| Campo | Tipo | Definição |
| --- | --- | --- |
| `source_sheet` | texto | Nome da aba original, sempre `NOVEMBRO` |
| `source_row` | inteiro | Linha Excel original, sem divulgar as restantes colunas |
| `sku` | texto | Chave normalizada, sem o número de unidades do pack no nome |
| `nome_produto` | texto | Nome comercial conforme o demonstrativo |
| `categoria` | texto | Cerveja, refrigerante, energético, água ou destilado |
| `marca` | texto | Marca identificável no nome; vazio quando não inferível |
| `volume_ml` | inteiro opcional | Volume declarado na apresentação de origem (ml), se explícito; não necessariamente o da porção comercializada |
| `unidade_comercial` | categoria | `embalagem` para unidades embaladas ou `porcao_volume_indefinido` para os dois destilados vendidos em unidades comerciais de volume não documentado |
| `fornecedor` | texto | Entidade fornecedora normalizada ou pseudónimo de pessoa |
| `quantidade_packs` | inteiro >= 0 | Quantidade de packs comprados |
| `unidades_por_pack` | inteiro > 0 | Quantas unidades comerciais são contabilizadas por pack/recipiente na planilha; podem ser porções, não embalagens |
| `unidades_compradas` | inteiro >= 0 | `quantidade_packs × unidades_por_pack`, no sentido de unidades comerciais contabilizadas; não equivale sempre ao número de garrafas adquiridas |
| `preco_pack_brl` | decimal opcional | Preço de compra por pack, em reais |
| `custo_compra_brl` | decimal opcional | Custo total da linha, em reais |
| `preco_venda_unitario_brl` | decimal opcional | Preço de venda tabelado por unidade, em reais |
| `receita_potencial_brl` | decimal opcional | `unidades_compradas × preco_venda_unitario_brl`, **não vendas reais** |
| `margem_potencial_brl` | decimal opcional | `receita_potencial_brl − custo_compra_brl`, antes de despesas |

Os valores monetários são exportados com ponto decimal e duas casas. Campo vazio
significa **desconhecido**, não zero. O script não transforma fórmulas Excel
incorretas em resultados financeiros válidos e recalcula as métricas potenciais
a partir das quantidades e preços observados.

**Atenção às cachaças de 5 litros.** O demonstrativo associa 70 unidades
comerciais a cada recipiente de 5 litros. Essas unidades podem representar
doses, mas o volume de cada porção não foi verificado. Por isso, conservamos
`volume_ml=5000` como tamanho da **embalagem de origem** e assinalamos
`unidade_comercial=porcao_volume_indefinido`; não assumimos que foram adquiridas
2.800 ou 1.680 garrafas de 5 litros. A comparação visual de preços por 100 ml
restringe-se às **cervejas**, cuja unidade comercial é uma embalagem.

Os nomes de fornecedores foram padronizados: `Amberv` para `Ambev` e
`Extra Distrbuidora` para `Extra Distribuidora`. Entradas referentes a pessoas
físicas foram substituídas por `Fornecedor local A` e `Fornecedor local B`.
Nenhuma informação de contacto, CNPJ ou salário foi importada.

## `data/public/cervejas.csv`

| Campo | Tipo | Definição |
| --- | --- | --- |
| `sku` | texto único | Identificador comercial do produto |
| `nome_produto` | texto | Nome original de uma linha de compra positiva |
| `marca` | texto | Marca associada ao SKU |
| `volume_ml` | inteiro | Volume indicado no nome do produto |

O catálogo só contém os **22 SKUs de cervejas adquiridas** na única amostra
histórica fiável, sem estilos, teor alcoólico ou códigos de barras não verificados.

## `data/coleta/vendas_diarias_modelo.csv`

| Campo | Tipo | Definição |
| --- | --- | --- |
| `data` | texto `AAAA-MM-DD` | Dia real de observação |
| `sku` | texto | Chave de `cervejas.csv` |
| `quantidade_vendida` | inteiro positivo | Unidades comprovadamente vendidas naquele dia |
| `preco_unitario_brl` | decimal >= 0 | Preço efetivo praticado, em reais |
| `origem_registo` | texto | Fonte original rastreável (sem nomes pessoais) |

O ficheiro modelo contém apenas a linha de cabeçalho. Para evitar duplicação,
o validador exige no máximo uma linha por `data`, `sku` e `origem_registo`.
O bar deve consolidar as ocorrências desse conjunto antes da importação.

## Modelo relacional SQLite

- `produtos(sku)`: catálogo de todos os produtos do snapshot, incluindo a
  modalidade da unidade comercial para evitar equiparar porções a embalagens.
- `fornecedores(id)`: fornecedor comercial normalizado.
- `compras(source_sheet, source_row)`: observação comercial, ligada a produto e fornecedor.
- `vendas_diarias(id)`: apenas observações futuras fornecidas explicitamente, ligadas a produto.

Os preços e totais na base relacional são armazenados em centavos inteiros para
comparações monetárias exatas.

## Limitações estatísticas

Há uma única fotografia comercial e 59 linhas de produto/fornecedor, das quais
29 são de cervejas e representam 22 SKUs únicos. As abas copiadas não constituem
séries temporais. Qualquer correlação entre atributos de SKU é exploratória;
não há base para concluir quais cervejas venderam mais ou para inferir lucro líquido.
