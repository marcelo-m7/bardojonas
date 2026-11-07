import csv
from decimal import Decimal
from pathlib import Path

import openpyxl

from scripts.build_dataset import build_dataset


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_published_snapshot_matches_original_business_controls():
    rows = read_csv(ROOT / "data/public/compras_2019.csv")
    beers = [row for row in rows if row["categoria"] == "cerveja"]
    catalog = read_csv(ROOT / "data/public/cervejas.csv")

    assert len(rows) == 59
    assert len(beers) == 29
    assert len(catalog) == 22
    assert len({row["sku"] for row in beers}) == 22
    assert {row["source_sheet"] for row in rows} == {"NOVEMBRO"}
    assert sum(int(row["unidades_compradas"]) for row in beers) == 3948
    assert sum(Decimal(row["custo_compra_brl"]) for row in beers) == Decimal("16706.60")
    assert sum(Decimal(row["receita_potencial_brl"]) for row in beers) == Decimal("24936.00")
    assert sum(Decimal(row["margem_potencial_brl"]) for row in beers) == Decimal("8229.40")


def test_extraction_preserves_two_suppliers_and_ignores_cloned_months(tmp_path):
    source = tmp_path / "private.xlsx"
    book = openpyxl.Workbook()
    main = book.active
    main.title = "NOVEMBRO"
    main.append(["PRODUTOS DA AMBERV"])
    main.append(
        ["Produto", "Empresa Fornecedora", "Quant. Comprada", "Unidades/Pack",
         "Valor do Pack", "Valor de Compra", "Valor de Venda", "Total em Vendas",
         "Lucro/Pack", "Lucro total"]
    )
    main.append(["BRAHMA 600ML", "Amberv", 2, 12, 60, 120, 7, 168, 24, 48])
    main.append(["BRAHMA 600ML", "Pessoa de Exemplo X", 1, 12, 72, 72, 7, 84, 12, 12])
    main.append(["COMPRA TOTAL", 192])
    clone = book.create_sheet("JANEIRO")
    for row in main:
        clone.append([cell.value for cell in row])
    book.save(source)

    result = build_dataset(source, tmp_path / "out")
    rows = read_csv(tmp_path / "out/compras_2019.csv")
    catalog = read_csv(tmp_path / "out/cervejas.csv")

    assert result == {"compras": 2, "cervejas": 1}
    assert len(rows) == 2
    assert len(catalog) == 1
    assert [row["unidades_compradas"] for row in rows] == ["24", "12"]
    assert rows[0]["fornecedor"] == "Ambev"
    assert rows[1]["fornecedor"] == "Fornecedor local A"
    assert rows[0]["sku"] == rows[1]["sku"] == "brahma-600ml"
    assert all(row["source_sheet"] == "NOVEMBRO" for row in rows)


def test_unknown_supplier_names_are_pseudonymized_consistently(tmp_path):
    source = tmp_path / "private.xlsx"
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "NOVEMBRO"
    sheet.append(["Produto", "Empresa Fornecedora", "Quant. Comprada", "Unidades/Pack",
                  "Valor do Pack", "Valor de Compra", "Valor de Venda", "Total em Vendas",
                  "Lucro/Pack", "Lucro total"])
    for name in ["Pessoa de Exemplo X", "Pessoa de Exemplo Y", "Pessoa de Exemplo X"]:
        sheet.append(["BRAHMA 600ML", name, 1, 12, 72, 72, 7, 84, 12, 12])
    book.save(source)

    build_dataset(source, tmp_path / "out")
    rows = read_csv(tmp_path / "out/compras_2019.csv")
    assert [row["fornecedor"] for row in rows] == [
        "Fornecedor local A", "Fornecedor local B", "Fornecedor local A"
    ]
    assert all("Pessoa de Exemplo" not in str(row) for row in rows)


def test_bulk_spirit_unit_is_not_presented_as_individual_five_litre_bottle():
    rows = read_csv(ROOT / "data/public/compras_2019.csv")
    bulk = [row for row in rows if row["nome_produto"].startswith("CACHAÇA")
            and "5 LITROS" in row["nome_produto"]]
    assert len(bulk) == 2
    assert {row["unidades_por_pack"] for row in bulk} == {"70"}
    assert {row["volume_ml"] for row in bulk} == {"5000"}
    assert {row["unidade_comercial"] for row in bulk} == {"porcao_volume_indefinido"}


def test_invalid_price_is_missing_not_invented_zero(tmp_path):
    source = tmp_path / "private.xlsx"
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "NOVEMBRO"
    sheet.append(["Produto", "Empresa Fornecedora", "Quant. Comprada", "Unidades/Pack",
                  "Valor do Pack", "Valor de Compra", "Valor de Venda", "Total em Vendas",
                  "Lucro/Pack", "Lucro total"])
    sheet.append(["SKOL 300ML", "Amberv", 0, 24, "-", 0, 4, 0, "#VALUE!", 0])
    book.save(source)

    build_dataset(source, tmp_path / "out")
    rows = read_csv(tmp_path / "out/compras_2019.csv")

    assert len(rows) == 1
    assert rows[0]["preco_pack_brl"] == ""
    assert rows[0]["custo_compra_brl"] == "0.00"
    assert rows[0]["margem_potencial_brl"] == ""
    assert read_csv(tmp_path / "out/cervejas.csv") == []
