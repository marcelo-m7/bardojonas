PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS produtos (
    sku TEXT PRIMARY KEY,
    nome_produto TEXT NOT NULL,
    categoria TEXT NOT NULL,
    marca TEXT NOT NULL DEFAULT '',
    volume_ml INTEGER CHECK (volume_ml IS NULL OR volume_ml > 0),
    unidade_comercial TEXT NOT NULL CHECK (
        unidade_comercial IN ('embalagem', 'porcao_volume_indefinido')
    )
);

CREATE TABLE IF NOT EXISTS fornecedores (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS compras (
    source_sheet TEXT NOT NULL,
    source_row INTEGER NOT NULL CHECK (source_row > 0),
    sku TEXT NOT NULL REFERENCES produtos(sku),
    fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id),
    quantidade_packs INTEGER NOT NULL CHECK (quantidade_packs >= 0),
    unidades_por_pack INTEGER NOT NULL CHECK (unidades_por_pack > 0),
    unidades_compradas INTEGER NOT NULL CHECK (unidades_compradas >= 0),
    preco_pack_centavos INTEGER CHECK (preco_pack_centavos IS NULL OR preco_pack_centavos >= 0),
    custo_compra_centavos INTEGER CHECK (custo_compra_centavos IS NULL OR custo_compra_centavos >= 0),
    preco_venda_centavos INTEGER CHECK (preco_venda_centavos IS NULL OR preco_venda_centavos >= 0),
    receita_potencial_centavos INTEGER CHECK (receita_potencial_centavos IS NULL OR receita_potencial_centavos >= 0),
    margem_potencial_centavos INTEGER,
    PRIMARY KEY (source_sheet, source_row),
    CHECK (unidades_compradas = quantidade_packs * unidades_por_pack)
);

CREATE INDEX IF NOT EXISTS idx_compras_produto ON compras(sku);
CREATE INDEX IF NOT EXISTS idx_compras_fornecedor ON compras(fornecedor_id);

CREATE TABLE IF NOT EXISTS vendas_diarias (
    id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    sku TEXT NOT NULL REFERENCES produtos(sku),
    quantidade_vendida INTEGER NOT NULL CHECK (quantidade_vendida > 0),
    preco_unitario_centavos INTEGER NOT NULL CHECK (preco_unitario_centavos >= 0),
    origem_registo TEXT NOT NULL CHECK (length(trim(origem_registo)) > 0),
    UNIQUE (data, sku, origem_registo)
);

CREATE INDEX IF NOT EXISTS idx_vendas_diarias_data ON vendas_diarias(data);
