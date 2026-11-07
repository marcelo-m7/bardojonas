# Bar do Jonas Academic Dataset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar um dataset anonimizado de compras do Bar do Jonas, um modelo relacional e notebook académico reprodutível, preparando a recolha futura de vendas reais.

**Architecture:** A única fonte observada é a aba `NOVEMBRO` de um XLSX privado. Dados comerciais publicáveis são normalizados em CSVs; SQLite torna o modelo relacional consultável, e o notebook trabalha sem sistemas externos. Uma tabela vazia recebe registos de vendas futuras, sem fabricar série temporal.

**Tech Stack:** Python 3.11+, stdlib SQLite/CSV, pandas, matplotlib, seaborn, scipy, pytest e Jupyter.

**Spec:** [`docs/superpowers/specs/2026-11-07-bardojonas-dataset-design.md`](../specs/2026-11-07-bardojonas-dataset-design.md)

## Global Constraints

- O repositório `marcelo-m7/bardojonas` é público; não publicar o XLSX original nem campos pessoais.
- Uma linha de compra representa um produto/fornecedor, não uma venda realizada.
- Utilizar somente a aba `NOVEMBRO` para o snapshot, sem duplicar meses copiados.
- CSVs públicos são entrada suficiente para reproduzir o notebook a partir de uma sessão limpa.
- Os totais de custo, receita e margem são potenciais e nunca identificados como vendas reais.
- Alterações numa branch `feat/dataset-bardojonas`; PR draft, sem merge.

## Review Focus

1. Linha duplicada do mesmo SKU em fornecedores diferentes: importar como compras distintas e agregar no catálogo (teste na Task 2).
2. Custo de pack ausente, traços ou erros `#VALUE!`: não converter em zero real nem propagar erro (teste na Task 1).
3. Fonte com várias abas clonadas: snapshot não produz meses artificiais (teste na Task 1).
4. Quantidade ou data inválida em novos registos: rejeitar no importador (teste na Task 3).
5. Ficheiro privado inclui CNPJ/contacto/salário: nenhum dado privado nos artefactos publicados (teste na Task 4).

---

### Task 1: Dados comerciais tratados e reconciliação

**Files:**
- Create: `data/public/compras_2019.csv`
- Create: `data/public/cervejas.csv`
- Create: `scripts/build_dataset.py`
- Test: `tests/test_dataset.py`

**Interfaces:**
- Consumes: XLSX privado apenas na preparação local, num caminho de entrada explícito; nunca no fluxo obrigatório do notebook.
- Produces: `build_dataset(source_xlsx: Path, output_dir: Path) -> dict[str, int]` e CSVs estáveis, com `source_row`, nomes comerciais, fornecedor publicável, preços e quantidades numéricas.

- [ ] **Step 1: Escrever testes de reconciliação e não duplicação.** Verificar 59 linhas, 22 SKUs comprados, 3.948 unidades, R$ 16.706,60 de custo, R$ 24.936,00 de receita potencial e R$ 8.229,40 de margem potencial.
- [ ] **Step 2: Executar `pytest tests/test_dataset.py -v` e confirmar falha inicial por implementação ausente.**
- [ ] **Step 3: Implementar extração exclusiva de `NOVEMBRO`, identificação de blocos `Produto/Empresa Fornecedora`, coerção numérica com `Decimal`, nomes seguros e escrita determinística em CSV.** Não copiar tabelas de despesas, contactos ou salários.
- [ ] **Step 4: Executar os testes, inspecionar amostras do CSV e confirmar totais.**
- [ ] **Step 5: Commit `feat: add validated anonymized historical dataset`.**

### Task 2: Modelo relacional SQLite

**Files:**
- Create: `database/schema.sql`
- Create: `scripts/import_sqlite.py`
- Test: `tests/test_sqlite.py`

**Interfaces:**
- Consumes: os CSVs da Task 1 e, opcionalmente, `data/coleta/vendas_diarias_modelo.csv`.
- Produces: `import_database(db_path: Path, data_dir: Path, sales_csv: Path | None = None) -> None`; tabelas com PK/FK e importação idempotente.

- [ ] **Step 1: Escrever testes para integridade, idempotência, fornecedores distintos para o mesmo SKU, zero vendas reais e consultas agrupadas.**
- [ ] **Step 2: Executar `pytest tests/test_sqlite.py -v` e confirmar falha inicial.**
- [ ] **Step 3: Implementar schema normalizado e importador transacional.** Chaves comerciais estáveis; vendas futuras separadas das compras antigas.
- [ ] **Step 4: Executar testes e uma consulta SQL de reconciliação.**
- [ ] **Step 5: Commit `feat: add relational model and deterministic imports`.**

### Task 3: Coleta diária e análise académica

**Files:**
- Create: `data/coleta/vendas_diarias_modelo.csv`
- Create: `scripts/validate_sales.py`
- Create: `notebooks/analise_bardojonas.ipynb`
- Create: `requirements.txt`
- Test: `tests/test_sales.py`
- Test: `tests/test_notebook.py`

**Interfaces:**
- Consumes: CSVs públicos da Task 1, registos futuros opcionais.
- Produces: `validate_sales_csv(path: Path, valid_skus: set[str]) -> list[dict]` e notebook executável de ponta a ponta.

- [ ] **Step 1: Escrever testes para CSV vazio válido, datas ISO, quantidades positivas, SKU desconhecido e distinção de vendas reais versus potencial.**
- [ ] **Step 2: Executar `pytest tests/test_sales.py tests/test_notebook.py -v` e confirmar falha inicial.**
- [ ] **Step 3: Criar validador e template vazio.** Datas e preços precisam de entrada observada; não gerar dados fictícios.
- [ ] **Step 4: Criar notebook com declaração IA, objetivos, limpeza, transformações, gráficos comparativos, estatística, interpretação e limitações da ausência de série temporal.**
- [ ] **Step 5: Executar notebook limpo via `jupyter nbconvert --execute --to notebook` ou `nbclient`, verificar gráficos, totais e saída.**
- [ ] **Step 6: Commit `feat: add prospective sales capture and reproducible analysis`.**

### Task 4: Proveniência, instruções e revisão de privacidade

**Files:**
- Create: `README.md`
- Create: `docs/data_dictionary.md`
- Modify: `.gitignore`
- Test: `tests/test_privacy.py`

**Interfaces:**
- Consumes: outputs anteriores.
- Produces: instruções de instalação/execução, descrição da origem, das limitações e da recolha diária, sem dependência de XLSX privado.

- [ ] **Step 1: Criar teste de ausência de padrões de CNPJ, telefone, e-mail, salários e nomes pessoais nas publicações.**
- [ ] **Step 2: Executar teste e confirmar falha inicial se houver arquivo publicável incorreto.**
- [ ] **Step 3: Documentar fonte, autorização do proprietário, dicionário, processo de recolha e limitações estatísticas; ignorar dados privados e bases SQLite geradas.**
- [ ] **Step 4: Executar suíte completa, notebook limpo, inspeção de arquivos versionados e `git diff --check`.**
- [ ] **Step 5: Commit `docs: document provenance and safe public reproducibility`; abrir PR draft para `main`.**

## Self-review

- Cobertura: histórico, anonimização, SQLite, recolha real, notebook, testes, divulgação e PR draft mapeados às Tasks 1–4.
- Tipos: `Path` e importadores coerentes com as Tasks; notebook lê apenas CSVs públicos.
- Risco residual: 59 linhas de compras representam um snapshot pequeno; não prometer análise temporal antes de novos dados reais.
