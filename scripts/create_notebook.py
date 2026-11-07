"""Compile the versioned notebook cell sources into a Jupyter .ipynb file."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat


ROOT = Path(__file__).resolve().parents[1]
cells = []


def md(content: str) -> None:
    cell = nbformat.v4.new_markdown_cell(dedent(content).strip())
    cell["id"] = f"md-{len(cells):03d}"
    cells.append(cell)


def code(content: str) -> None:
    cell = nbformat.v4.new_code_cell(dedent(content).strip())
    cell["id"] = f"code-{len(cells):03d}"
    cells.append(cell)


md(
    """
    # Bar do Jonas: estrutura comercial, custos e margens potenciais das bebidas

    **Unidade Curricular:** Análise de Dados e Visualização da Informação — UAlg
    **Autor:** Marcelo Santos — a79433@ualg.pt
    **Fonte:** demonstrativo privado do Bar do Jonas, fornecido pelo titular e convertido num
    dataset comercial público anonimizado em `data/public/`.
    O ficheiro original menciona o período 24/11/2019–24/12/2019, mas cada linha **não**
    dispõe de data individual de transação. O snapshot é identificado pela aba `NOVEMBRO`.

    **Declaração de utilização de IA:** foram utilizadas ferramentas de IA (ChatGPT/OpenAI)
    para apoiar o desenho do modelo, a programação da extração/normalização, a elaboração
    inicial do código de análise, dos testes e da redação explicativa. O autor deve rever,
    executar, compreender e validar todas as análises e conclusões antes da entrega.

    **Reprodutibilidade:** Python 3.11+, bibliotecas em `requirements.txt`; executar
    todas as células pela ordem. O notebook utiliza caminhos relativos e os CSVs públicos
    incluídos no repositório. Não precisa do Excel privado, Odoo ou internet.

    **Definição crucial:** `quantidade_packs` e `unidades_compradas` descrevem compras;
    `receita_potencial_brl` estima o valor caso todas as unidades compradas fossem vendidas
    aos preços da planilha. **Não são vendas efetivamente comprovadas.**
    """
)

md(
    """
    ## 1. Perguntas de investigação

    1. Como se distribui o catálogo de cervejas por marcas, volumes e fornecedores?
    2. Quais as marcas com maior **volume adquirido** no período documentado?
    3. Como variam preço de venda anunciado, custo unitário e margem potencial?
    4. Existe associação entre volume da embalagem e preço por 100 ml?
    5. Que limitações impedem inferir procura, sazonalidade ou faturamento realizado?

    A unidade de observação comercial é uma **linha produto–fornecedor de compra**.
    Para comparações de atributos das cervejas, agregamos os registos por SKU,
    evitando tratar fornecedores repetidos como produtos independentes.
    """
)

code(
    """
    from pathlib import Path
    import sys
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy.stats import spearmanr
    from IPython.display import display

    sns.set_theme(style="whitegrid", palette="crest")
    plt.rcParams.update({"figure.figsize": (10, 5), "axes.titlesize": 13})

    PROJECT_ROOT = Path.cwd().resolve()
    if not (PROJECT_ROOT / "data/public/compras_2019.csv").exists():
        PROJECT_ROOT = PROJECT_ROOT.parent
    DATA_DIR = PROJECT_ROOT / "data/public"
    assert (DATA_DIR / "compras_2019.csv").exists(), "CSV público em falta"
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    print(f"Dados encontrados em: {DATA_DIR.relative_to(PROJECT_ROOT)}")
    """
)

md(
    """
    ## 2. Aquisição, preparação e auditoria

    Os CSVs foram extraídos da aba `NOVEMBRO`; as demais abas contêm conteúdo
    replicado e **não foram convertidas em meses de vendas**. A coluna `source_row`
    mantém uma referência auditável à linha do documento privado, sem divulgar
    CNPJ, contactos, salários ou dados de clientes.
    """
)

code(
    """
    compras = pd.read_csv(DATA_DIR / "compras_2019.csv")
    catalogo = pd.read_csv(DATA_DIR / "cervejas.csv")

    colunas_monetarias = [
        "preco_pack_brl", "custo_compra_brl", "preco_venda_unitario_brl",
        "receita_potencial_brl", "margem_potencial_brl"
    ]
    for coluna in colunas_monetarias:
        compras[coluna] = pd.to_numeric(compras[coluna], errors="coerce")
    for coluna in ["quantidade_packs", "unidades_por_pack", "unidades_compradas", "volume_ml"]:
        compras[coluna] = pd.to_numeric(compras[coluna], errors="coerce")
    assert not compras.duplicated(["source_sheet", "source_row"]).any()
    assert compras["unidades_compradas"].eq(
        compras["quantidade_packs"] * compras["unidades_por_pack"]
    ).all()

    cervejas = compras.loc[compras["categoria"].eq("cerveja")].copy()
    assert len(compras) == 59
    assert catalogo["sku"].nunique() == 22
    assert int(cervejas["unidades_compradas"].sum()) == 3948
    assert np.isclose(cervejas["custo_compra_brl"].sum(), 16706.60)
    assert np.isclose(cervejas["receita_potencial_brl"].sum(), 24936.00)
    assert np.isclose(cervejas["margem_potencial_brl"].sum(), 8229.40)

    print("CONTROLOS: 59 linhas; 22 cervejas; 3948 unidades")
    print(f"Receita potencial das cervejas: R$ {cervejas['receita_potencial_brl'].sum():,.2f}")
    display(compras.head(5))
    """
)

code(
    """
    qualidade = pd.DataFrame({
        "missing": compras.isna().sum(),
        "tipo": compras.dtypes.astype(str),
    }).sort_values("missing", ascending=False)
    print("Valores em falta por coluna e tipo:")
    display(qualidade)
    print("Linhas duplicadas (aba + linha da origem):",
          int(compras.duplicated(["source_sheet", "source_row"]).sum()))
    print("Abas presentes no CSV:", compras["source_sheet"].unique().tolist())
    """
)

md(
    """
    **Interpretação da limpeza.** O identificador da linha de origem preserva a
    proveniência. Valores em falta na coluna de volume para produtos sem
    mililitros explícitos (como algumas águas) permanecem ausentes. Não devem
    ser imputados valores inventados. A ausência de duplicação de linhas não
    significa que produtos repetidos sejam erro: podem representar compras
    legítimas do mesmo item a fornecedores distintos.
    """
)

md(
    """
    ## 3. Junções e tabelas de frequência

    O catálogo só inclui SKUs de cervejas com aquisição positiva. A junção
    `many_to_one` verifica que cada linha de compra encontra exatamente um
    produto no catálogo.
    """
)

code(
    """
    cervejas_join = cervejas.merge(
        catalogo[["sku", "nome_produto"]].rename(
            columns={"nome_produto": "nome_catalogo"}
        ),
        on="sku", how="left", validate="many_to_one", indicator=True
    )
    assert cervejas_join["_merge"].eq("both").all()
    print("Distribuição de linhas de compra por categoria:")
    display(compras.groupby("categoria", as_index=False).agg(
        linhas=("sku", "size"), unidades=("unidades_compradas", "sum")
    ).sort_values("linhas", ascending=False))
    print("Tabela cruzada: marca × volume (SKUs distintos):")
    display(pd.crosstab(catalogo["marca"], catalogo["volume_ml"]))
    """
)

md(
    """
    ## 4. Comparação entre cervejas

    Agrupamos as linhas comerciais por SKU antes de analisar preços e margem,
    preservando o total real de unidades compradas. `Preço de venda` é um
    preço de tabela declarado no demonstrativo; a receita e a margem resultam
    de hipóteses comerciais, não de faturação efetiva.
    """
)

code(
    """
    sku_stats = (
        cervejas.groupby(["sku", "marca", "volume_ml"], as_index=False)
        .agg(
            unidades_adquiridas=("unidades_compradas", "sum"),
            custo_brl=("custo_compra_brl", "sum"),
            receita_potencial_brl=("receita_potencial_brl", "sum"),
            margem_potencial_brl=("margem_potencial_brl", "sum"),
            n_fornecedores=("fornecedor", "nunique")
        )
    )
    sku_stats["preco_venda_unitario_brl"] = (
        sku_stats["receita_potencial_brl"] / sku_stats["unidades_adquiridas"]
    )
    sku_stats["custo_unitario_brl"] = (
        sku_stats["custo_brl"] / sku_stats["unidades_adquiridas"]
    )
    sku_stats["preco_por_100ml_brl"] = (
        sku_stats["preco_venda_unitario_brl"] / sku_stats["volume_ml"] * 100
    )
    sku_stats["margem_potencial_pct"] = (
        sku_stats["margem_potencial_brl"] / sku_stats["receita_potencial_brl"] * 100
    )
    assert len(sku_stats) == 22
    display(sku_stats.sort_values("unidades_adquiridas", ascending=False).head(10))
    """
)

code(
    """
    por_marca = (
        sku_stats.groupby("marca", as_index=False)
        .agg(
            skus=("sku", "count"),
            unidades_adquiridas=("unidades_adquiridas", "sum"),
            custo_brl=("custo_brl", "sum"),
            receita_potencial_brl=("receita_potencial_brl", "sum"),
            margem_potencial_brl=("margem_potencial_brl", "sum")
        )
        .sort_values("unidades_adquiridas", ascending=False)
    )
    display(por_marca)
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(data=por_marca, x="unidades_adquiridas", y="marca", ax=ax, color="#178e99")
    ax.set(title="Cervejas: unidades adquiridas por marca", xlabel="Unidades compradas", ylabel="")
    plt.tight_layout()
    plt.show()
    """
)

md(
    """
    **Interpretação:** a Brahma lidera o volume comprado (1.518 unidades);
    seguem Itaipava (684) e Heineken (402). Estes valores descrevem o
    **abastecimento documentado**, não preferências observadas de clientes.
    Não podemos concluir que a Brahma foi a mais vendida.
    """
)

md(
    """
    ## 5. Estatística univariada e multivariada

    O preço unitário aumenta naturalmente quando a embalagem contém mais
    líquido. Por isso, a comparação mais justa usa também **R$ por 100 ml**.
    As correlações são exploratórias, calculadas sobre 22 SKUs distintos;
    não medem causalidade nem representam todos os bares de Vitória.
    """
)

code(
    """
    colunas = [
        "volume_ml", "preco_venda_unitario_brl", "preco_por_100ml_brl",
        "custo_unitario_brl", "margem_potencial_pct", "unidades_adquiridas"
    ]
    display(sku_stats[colunas].describe().T.round(2))
    rho, pvalor = spearmanr(
        sku_stats["volume_ml"], sku_stats["preco_por_100ml_brl"], nan_policy="omit"
    )
    print(f"Spearman volume × preço por 100 ml: rho={rho:.3f}, p={pvalor:.4f}, n={len(sku_stats)}")
    """
)

code(
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    sns.scatterplot(
        data=sku_stats, x="volume_ml", y="preco_por_100ml_brl",
        hue="marca", size="unidades_adquiridas", sizes=(30, 200), ax=axes[0]
    )
    axes[0].set(
        title="Preço de tabela por 100 ml e tamanho",
        xlabel="Volume da embalagem (ml)", ylabel="R$ por 100 ml"
    )
    axes[0].legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=7)
    sns.histplot(data=sku_stats, x="margem_potencial_pct", bins=8, ax=axes[1], color="#209783")
    axes[1].set(title="Distribuição das margens potenciais", xlabel="Margem potencial (%)", ylabel="Número de SKUs")
    fig.tight_layout()
    plt.show()
    """
)

md(
    """
    **Interpretação:** a associação entre volume e preço por 100 ml
    tende a ser negativa nesta amostra: embalagens maiores costumam oferecer
    preços relativos menores. O coeficiente de Spearman quantifica a relação
    monotónica, mas os resultados refletem as condições comerciais de um
    período histórico e apenas 22 produtos. A margem é **bruta e potencial**:
    não desconta energia, aluguer, perdas, impostos ou mão de obra.
    """
)

md(
    """
    ## 6. Fornecedores e produtos com múltiplas origens
    """
)

code(
    """
    por_fornecedor = (
        compras.groupby("fornecedor", as_index=False)
        .agg(
            linhas=("sku", "size"),
            skus=("sku", "nunique"),
            custo_total_brl=("custo_compra_brl", "sum")
        )
        .sort_values("custo_total_brl", ascending=False)
    )
    display(por_fornecedor)
    varios_fornecedores = sku_stats.loc[sku_stats["n_fornecedores"] > 1]
    print(f"SKUs de cerveja presentes em mais de um fornecedor: {len(varios_fornecedores)}")
    display(varios_fornecedores[["sku", "n_fornecedores", "unidades_adquiridas"]])
    """
)

md(
    """
    **Interpretação:** o mesmo SKU pode aparecer em fornecedores diferentes,
    o que permite comparar fontes de abastecimento. Os nomes de fornecedores
    individuais foram substituídos por identificadores genéricos no dataset
    público. Comparações de custo devem considerar quantidade por pack e
    volume para não confundir formatos de compra diferentes.
    """
)

md(
    """
    ## 7. Séries temporais: condição para análise futura

    Uma série temporal legítima exige observações com datas reais.
    As abas `DEZEMBRO`, `JANEIRO` e `FEVEREIRO` não constituem
    novas amostras independentes. Apenas se o bar passar a registar
    vendas diárias num CSV, usando o modelo em `data/coleta/`, será
    possível estudar evolução, dias da semana ou sazonalidade.
    """
)

code(
    """
    from scripts.validate_sales import validate_sales_csv

    arquivo_vendas = PROJECT_ROOT / "data/coleta/vendas_diarias.csv"
    if arquivo_vendas.exists():
        vendas_reais = validate_sales_csv(arquivo_vendas, set(catalogo["sku"]))
    else:
        vendas_reais = []
    if vendas_reais:
        vendas_df = pd.DataFrame(vendas_reais)
        vendas_df["data"] = pd.to_datetime(vendas_df["data"])
        serie = vendas_df.groupby("data")["quantidade_vendida"].sum().sort_index()
        fig, ax = plt.subplots(figsize=(10, 4))
        serie.plot(ax=ax, marker="o")
        ax.set(title="Unidades efetivamente vendidas por dia", xlabel="Data", ylabel="Unidades")
        plt.tight_layout()
        plt.show()
        display(serie.to_frame("unidades_vendidas"))
    else:
        print("Série temporal de vendas indisponível: nenhum registo diário real fornecido.")
    """
)

md(
    """
    ## 8. Conclusões, limitações e continuidade

    A análise identificou **59 linhas comerciais**, das quais **29 linhas
    de abastecimento de cervejas**, representando **22 SKUs de cerveja** e
    **3.948 unidades adquiridas**. O custo associado foi R$ 16.706,60.
    A receita teórica de R$ 24.936,00 e a margem bruta teórica de
    R$ 8.229,40 só se aplicariam sob a hipótese de venda integral aos
    preços de tabela, antes de outras despesas.

    O dataset mostra diversidade de marcas, volumes e fornecedores, e
    permite comparar estrutura de preços e compras. Não permite inferir
    vendas, clientes, frequência de consumo, procura, tendências temporais
    ou lucros líquidos. Resultados correlacionais são exploratórios e
    sensíveis ao número reduzido de SKUs.

    **Próximo passo operacional:** recolher vendas diárias reais durante
    várias semanas, com data, SKU, quantidade, preço efetivo e origem do
    registo. A junção futura ocorrerá pela chave `sku`. O dataset público
    e o notebook permanecerão executáveis mesmo sem esses registos.

    **Origem e ética:** material comercial do próprio Bar do Jonas
    disponibilizado pelo titular, tratado e anonimizado para esta finalidade;
    nenhum registo laboral ou contacto pessoal foi publicado. A publicação
    livre do dataset tratado não elimina a necessidade de o docente
    avaliar a adequação da sua dimensão e proveniência ao enunciado.
    """
)


def main() -> None:
    notebook = nbformat.v4.new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
    )
    output = ROOT / "notebooks/analise_bardojonas.ipynb"
    output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, output)
    print(f"Generated {output.relative_to(ROOT)} ({len(cells)} cells)")


if __name__ == "__main__":
    main()
