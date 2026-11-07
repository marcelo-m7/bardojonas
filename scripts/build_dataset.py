"""Derive a publishable product-purchase snapshot from a private workbook.

Only the commercial product tables in NOVEMBRO are read. This script never
copies administrative headers, employee information or cloned monthly tabs.
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

import openpyxl


MONEY = Decimal("0.01")
BEER_BRANDS = {
    "BRAHMA": "Brahma",
    "SKOL": "Skol",
    "SUB-ZERO": "Sub-Zero",
    "BOHEMIA": "Bohemia",
    "CARACU": "Caracu",
    "DEVASSA": "Devassa",
    "HEINEKEN": "Heineken",
    "ITAIPAVA": "Itaipava",
    "CRYSTAL": "Crystal",
    "LOKAL": "Lokal",
    "PETRA": "Petra",
}
PUBLIC_SUPPLIERS = {
    "AMBEV": "Ambev", "AMBERV": "Ambev",
    "COROA": "COROA", "EXTRA DISTRBUIDORA": "Extra Distribuidora",
    "EXTRA DISTRIBUIDORA": "Extra Distribuidora",
    "FORTE DISTRIBUIDORA": "Forte Distribuidora",
    "GRUPO PETRÓPOLIS": "Grupo Petrópolis",
    "LIPPAUS DISTRIBUIDORA": "Lippaus Distribuidora",
    "RESISTÊNCIA DISTRIBUIDORA": "Resistência Distribuidora",
    "UAI": "UAI",
}
PURCHASE_FIELDS = [
    "source_sheet", "source_row", "sku", "nome_produto", "categoria", "marca",
    "volume_ml", "unidade_comercial", "fornecedor", "quantidade_packs", "unidades_por_pack",
    "unidades_compradas", "preco_pack_brl", "custo_compra_brl",
    "preco_venda_unitario_brl", "receita_potencial_brl", "margem_potencial_brl",
]
BEER_FIELDS = ["sku", "nome_produto", "marca", "volume_ml"]


def number(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value or value in {"-", "?", "??"} or value.startswith("#"):
            return None
        value = value.replace(",", ".")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def money_text(value: Decimal | None) -> str:
    return "" if value is None else str(value.quantize(MONEY, rounding=ROUND_HALF_UP))


def whole_text(value: Decimal | None) -> str:
    if value is None or value != value.to_integral_value():
        raise ValueError(f"Expected integral non-null quantity, got {value}")
    if value < 0:
        raise ValueError("Negative quantities are not valid purchases")
    return str(int(value))


def supplier_public(value: object, pseudonyms: dict[str, str]) -> str:
    name = str(value or "").strip()
    upper = name.upper()
    if upper in PUBLIC_SUPPLIERS:
        return PUBLIC_SUPPLIERS[upper]
    if not name:
        raise ValueError("Missing supplier name")
    # Fail closed: unidentified individuals or businesses are never published
    # under their original names. The source-to-pseudonym mapping lives only
    # in memory and is deliberately not committed to the public repository.
    if upper not in pseudonyms:
        pseudonyms[upper] = f"Fornecedor local {chr(65 + len(pseudonyms))}"
    return pseudonyms[upper]


def category_and_brand(name: str) -> tuple[str, str]:
    upper = name.upper()
    for prefix, brand in BEER_BRANDS.items():
        if upper.startswith(prefix):
            return "cerveja", brand
    if upper.startswith("CACHAÇA"):
        return "destilado", "Cachaça"
    if upper.startswith("TNT"):
        return "energético", "TNT"
    if upper.startswith("ÁGUA"):
        return "água", "Campino"
    return "refrigerante", ""


def parse_volume(name: str) -> str:
    match = re.search(r"(\d+)\s*ML", name, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"(\d+)\s*LITROS?", name, flags=re.IGNORECASE)
    return str(int(match.group(1)) * 1000) if match else ""


def sku_for(name: str) -> str:
    source = re.sub(r"\s*\(\d+\)", "", name.upper())
    source = re.sub(
        r"(\d+)\s*LITROS?",
        lambda match: f"{int(match.group(1)) * 1000}ML",
        source,
    )
    source = unicodedata.normalize("NFKD", source).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")


def _commercial_rows(sheet):
    in_table = False
    for row in sheet.iter_rows():
        values = [cell.value for cell in row]
        first = str(values[0] or "").strip() if values else ""
        second = str(values[1] or "").strip() if len(values) > 1 else ""
        if first.lower() == "produto" and second.lower().startswith("empresa fornecedora"):
            in_table = True
            continue
        if first.upper() in {"COMPRA TOTAL", "LUCRO TOTAL"} or not first:
            in_table = False
        if not in_table or len(values) < 10 or not first:
            continue
        yield row[0].row, values


def _write_csv(destination: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_dataset(source_xlsx: Path, output_dir: Path) -> dict[str, int]:
    """Build cleaned CSVs, never retaining the source workbook in output_dir."""
    book = openpyxl.load_workbook(source_xlsx, read_only=True, data_only=True)
    if "NOVEMBRO" not in book:
        raise ValueError("Source workbook does not contain NOVEMBRO")
    purchases: list[dict[str, str]] = []
    catalog: dict[str, dict[str, str]] = {}
    pseudonyms: dict[str, str] = {}

    for row_number, cells in _commercial_rows(book["NOVEMBRO"]):
        name = str(cells[0]).strip()
        packs, units_pack = number(cells[2]), number(cells[3])
        if packs is None or units_pack is None:
            raise ValueError(f"Missing quantity at source row {row_number}")
        if units_pack <= 0:
            raise ValueError(f"Invalid pack size at source row {row_number}")
        units = packs * units_pack
        category, brand = category_and_brand(name)
        sku = sku_for(name)
        pack_price = number(cells[4])
        purchase_cost = number(cells[5])
        selling_price = number(cells[6])
        revenue = units * selling_price if selling_price is not None else None
        # A missing pack price is not evidence of zero economic cost.
        margin = (
            revenue - purchase_cost
            if revenue is not None and purchase_cost is not None and pack_price is not None
            else None
        )
        purchase = {
            "source_sheet": "NOVEMBRO",
            "source_row": str(row_number),
            "sku": sku,
            "nome_produto": name,
            "categoria": category,
            "marca": brand,
            "volume_ml": parse_volume(name),
            "unidade_comercial": (
                "porcao_volume_indefinido"
                if category == "destilado" and "5 LITROS" in name.upper()
                and units_pack == 70 else "embalagem"
            ),
            "fornecedor": supplier_public(cells[1], pseudonyms),
            "quantidade_packs": whole_text(packs),
            "unidades_por_pack": whole_text(units_pack),
            "unidades_compradas": whole_text(units),
            "preco_pack_brl": money_text(pack_price),
            "custo_compra_brl": money_text(purchase_cost),
            "preco_venda_unitario_brl": money_text(selling_price),
            "receita_potencial_brl": money_text(revenue),
            "margem_potencial_brl": money_text(margin),
        }
        purchases.append(purchase)
        if category == "cerveja" and units > 0:
            catalog.setdefault(
                sku, {field: purchase[field] for field in BEER_FIELDS}
            )
    _write_csv(output_dir / "compras_2019.csv", PURCHASE_FIELDS, purchases)
    _write_csv(output_dir / "cervejas.csv", BEER_FIELDS, [
        catalog[key] for key in sorted(catalog)
    ])
    return {"compras": len(purchases), "cervejas": len(catalog)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Private local XLSX")
    parser.add_argument("--output", default=Path("data/public"), type=Path)
    args = parser.parse_args()
    print(build_dataset(args.source, args.output))
