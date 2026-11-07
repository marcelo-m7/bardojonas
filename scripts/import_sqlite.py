"""Import the public dataset and optional real daily sales into SQLite."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


SCHEMA = Path(__file__).resolve().parents[1] / "database/schema.sql"
SALES_FIELDS = [
    "data", "sku", "quantidade_vendida", "preco_unitario_brl", "origem_registo"
]


def _read_csv(path: Path, required_fields: list[str] | None = None) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if required_fields is not None and reader.fieldnames != required_fields:
            raise ValueError(f"Invalid CSV columns in {path.name}: expected {required_fields}")
        rows = list(reader)
    for index, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"Invalid CSV structure on row {index} of {path.name}")
    return rows


def _cents(value: str) -> int | None:
    if value == "":
        return None
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid monetary value: {value}") from exc
    if not amount.is_finite() or amount * 100 != (amount * 100).to_integral_value():
        raise ValueError(f"Invalid currency precision: {value}")
    return int(amount * 100)


def _sale_observations(
    rows: list[dict[str, str]], valid_skus: set[str]
) -> list[tuple[str, str, int, int, str]]:
    output: list[tuple[str, str, int, int, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, row in enumerate(rows, 2):
        recorded = row["data"].strip()
        try:
            if date.fromisoformat(recorded).isoformat() != recorded:
                raise ValueError
        except ValueError as exc:
            raise ValueError(f"Invalid date on sales row {index}: {recorded}") from exc
        sku = row["sku"].strip()
        if sku not in valid_skus:
            raise ValueError(f"Unknown SKU on sales row {index}: {sku}")
        try:
            amount = int(row["quantidade_vendida"])
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid quantity on sales row {index}") from exc
        if amount <= 0:
            raise ValueError(f"Invalid quantity on sales row {index}")
        price = _cents(row["preco_unitario_brl"].strip())
        if price is None or price < 0:
            raise ValueError(f"Invalid price on sales row {index}")
        origin = row["origem_registo"].strip()
        if not origin:
            raise ValueError(f"Missing observation source on sales row {index}")
        key = (recorded, sku, origin)
        if key in seen:
            raise ValueError(f"Duplicate daily sale: {key}")
        seen.add(key)
        output.append((recorded, sku, amount, price, origin))
    return output


def import_database(
    db_path: Path,
    data_dir: Path,
    sales_csv: Path | None = None,
) -> None:
    """Create or refresh the public snapshot; only ingest supplied real sales."""
    purchases = _read_csv(data_dir / "compras_2019.csv")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        with connection:
            for row in purchases:
                volume = int(row["volume_ml"]) if row["volume_ml"] else None
                connection.execute(
                    """INSERT INTO produtos (
                         sku, nome_produto, categoria, marca, volume_ml, unidade_comercial
                       ) VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(sku) DO UPDATE SET
                         nome_produto=excluded.nome_produto,
                         categoria=excluded.categoria,
                         marca=excluded.marca,
                         volume_ml=excluded.volume_ml,
                         unidade_comercial=excluded.unidade_comercial""",
                    (row["sku"], row["nome_produto"], row["categoria"], row["marca"],
                     volume, row["unidade_comercial"]),
                )
                connection.execute(
                    "INSERT INTO fornecedores (nome) VALUES (?) ON CONFLICT(nome) DO NOTHING",
                    (row["fornecedor"],),
                )
                supplier_id = connection.execute(
                    "SELECT id FROM fornecedores WHERE nome = ?", (row["fornecedor"],)
                ).fetchone()[0]
                connection.execute(
                    """INSERT INTO compras (
                         source_sheet, source_row, sku, fornecedor_id,
                         quantidade_packs, unidades_por_pack, unidades_compradas,
                         preco_pack_centavos, custo_compra_centavos, preco_venda_centavos,
                         receita_potencial_centavos, margem_potencial_centavos
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(source_sheet, source_row) DO UPDATE SET
                         sku=excluded.sku, fornecedor_id=excluded.fornecedor_id,
                         quantidade_packs=excluded.quantidade_packs,
                         unidades_por_pack=excluded.unidades_por_pack,
                         unidades_compradas=excluded.unidades_compradas,
                         preco_pack_centavos=excluded.preco_pack_centavos,
                         custo_compra_centavos=excluded.custo_compra_centavos,
                         preco_venda_centavos=excluded.preco_venda_centavos,
                         receita_potencial_centavos=excluded.receita_potencial_centavos,
                         margem_potencial_centavos=excluded.margem_potencial_centavos""",
                    (
                        row["source_sheet"], int(row["source_row"]), row["sku"], supplier_id,
                        int(row["quantidade_packs"]), int(row["unidades_por_pack"]),
                        int(row["unidades_compradas"]),
                        _cents(row["preco_pack_brl"]), _cents(row["custo_compra_brl"]),
                        _cents(row["preco_venda_unitario_brl"]),
                        _cents(row["receita_potencial_brl"]),
                        _cents(row["margem_potencial_brl"]),
                    ),
                )
            if sales_csv is not None:
                valid = {row["sku"] for row in _read_csv(data_dir / "cervejas.csv")}
                for values in _sale_observations(_read_csv(sales_csv, SALES_FIELDS), valid):
                    connection.execute(
                        """INSERT INTO vendas_diarias
                           (data, sku, quantidade_vendida, preco_unitario_centavos, origem_registo)
                           VALUES (?, ?, ?, ?, ?)
                           ON CONFLICT(data, sku, origem_registo) DO UPDATE SET
                             quantidade_vendida=excluded.quantidade_vendida,
                             preco_unitario_centavos=excluded.preco_unitario_centavos""",
                        values,
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("output/bardojonas.sqlite3"))
    parser.add_argument("--data", type=Path, default=Path("data/public"))
    parser.add_argument("--sales", type=Path, default=None)
    args = parser.parse_args()
    import_database(args.db, args.data, args.sales)
    print(f"Imported public snapshot into {args.db}")
