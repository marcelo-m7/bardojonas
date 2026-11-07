import csv
import sqlite3
from pathlib import Path

import pytest

from scripts.import_sqlite import import_database


ROOT = Path(__file__).resolve().parents[1]


def query(db_path: Path, statement: str, args: tuple = ()):
    with sqlite3.connect(db_path) as connection:
        return connection.execute(statement, args).fetchall()


def test_import_is_idempotent_and_reconciles_original_snapshot(tmp_path):
    database = tmp_path / "jonas.sqlite3"
    source = ROOT / "data/public"
    import_database(database, source)
    import_database(database, source)

    assert query(database, "SELECT COUNT(*) FROM produtos")[0][0] == 50
    assert query(database, "SELECT COUNT(*) FROM compras")[0][0] == 59
    assert query(database, "SELECT COUNT(*) FROM vendas_diarias")[0][0] == 0
    assert query(database, "SELECT COUNT(*) FROM produtos WHERE categoria='cerveja'")[0][0] == 22
    assert query(database, "SELECT COUNT(*) FROM compras WHERE sku='brahma-1000ml'")[0][0] == 2
    assert query(database, "SELECT COUNT(*) FROM compras WHERE sku NOT IN (SELECT sku FROM produtos)")[0][0] == 0
    assert query(database, "SELECT SUM(unidades_compradas) FROM compras WHERE sku IN (SELECT sku FROM produtos WHERE categoria='cerveja')")[0][0] == 3948
    assert query(database, "SELECT SUM(custo_compra_centavos), SUM(receita_potencial_centavos), SUM(margem_potencial_centavos) FROM compras WHERE sku IN (SELECT sku FROM produtos WHERE categoria='cerveja')")[0] == (1670660, 2493600, 822940)


def test_real_daily_sales_imported_only_from_supplied_observations(tmp_path):
    database = tmp_path / "jonas.sqlite3"
    sales = tmp_path / "vendas.csv"
    with sales.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "data", "sku", "quantidade_vendida", "preco_unitario_brl", "origem_registo"
        ])
        writer.writeheader()
        writer.writerow({
            "data": "2026-11-08", "sku": "brahma-600ml", "quantidade_vendida": "3",
            "preco_unitario_brl": "8.50", "origem_registo": "caderneta_balencao"
        })

    import_database(database, ROOT / "data/public", sales_csv=sales)
    import_database(database, ROOT / "data/public", sales_csv=sales)

    assert query(database, "SELECT data, sku, quantidade_vendida, preco_unitario_centavos FROM vendas_diarias") == [
        ("2026-11-08", "brahma-600ml", 3, 850)
    ]


def test_invalid_sales_are_rejected_and_not_partially_saved(tmp_path):
    database = tmp_path / "jonas.sqlite3"
    sales = tmp_path / "vendas.csv"
    sales.write_text(
        "data,sku,quantidade_vendida,preco_unitario_brl,origem_registo\n"
        "2026-11-08,brahma-600ml,3,8.50,caderneta\n"
        "2026-02-30,brahma-600ml,2,8.50,caderneta\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid date"):
        import_database(database, ROOT / "data/public", sales_csv=sales)

    assert query(database, "SELECT COUNT(*) FROM vendas_diarias")[0][0] == 0


def test_importer_rejects_wrong_header_and_nonbeer_sales(tmp_path):
    database = tmp_path / "jonas.sqlite3"
    sales = tmp_path / "vendas.csv"
    sales.write_text("sku,quantidade\n", encoding="utf-8")
    with pytest.raises(ValueError, match="CSV"):
        import_database(database, ROOT / "data/public", sales_csv=sales)

    sales.write_text(
        "data,sku,quantidade_vendida,preco_unitario_brl,origem_registo\n"
        "2026-11-08,cachaca-pura-amarela-5000ml,3,8.50,caderno\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Unknown SKU"):
        import_database(database, ROOT / "data/public", sales_csv=sales)


def test_product_attributes_are_refreshed_on_reimport(tmp_path):
    database = tmp_path / "jonas.sqlite3"
    source = tmp_path / "dataset"
    source.mkdir()
    source.joinpath("compras_2019.csv").write_bytes(
        (ROOT / "data/public/compras_2019.csv").read_bytes()
    )
    source.joinpath("cervejas.csv").write_bytes(
        (ROOT / "data/public/cervejas.csv").read_bytes()
    )
    import_database(database, source)

    rows = list(csv.DictReader(source.joinpath("compras_2019.csv").open(encoding="utf-8")))
    for row in rows:
        if row["sku"] == "brahma-600ml":
            row["nome_produto"] = "BRAHMA 600ML — nome corrigido"
    with source.joinpath("compras_2019.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    import_database(database, source)
    assert query(database, "SELECT nome_produto FROM produtos WHERE sku='brahma-600ml'") == [
        ("BRAHMA 600ML — nome corrigido",)
    ]
    assert query(database, "SELECT unidade_comercial FROM produtos WHERE sku='cachaca-pura-amarela-5000ml'") == [
        ("porcao_volume_indefinido",)
    ]
