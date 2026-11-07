"""Validate genuine daily sales observations before adding them to the dataset."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from pathlib import Path

from scripts.import_sqlite import SALES_FIELDS, _read_csv, _sale_observations


def validate_sales_csv(path: Path, valid_skus: set[str]) -> list[dict]:
    """Return typed daily aggregate observations; raise on invalid entries."""
    rows = _read_csv(path, SALES_FIELDS)
    validated = _sale_observations(rows, valid_skus)
    return [
        {
            "data": observed_date,
            "sku": sku,
            "quantidade_vendida": quantity,
            "preco_unitario_brl": (Decimal(cents) / Decimal("100")).quantize(Decimal("0.01")),
            "origem_registo": source,
        }
        for observed_date, sku, quantity, cents, source in validated
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sales_csv", type=Path)
    parser.add_argument("--catalog", type=Path, default=Path("data/public/cervejas.csv"))
    args = parser.parse_args()
    with args.catalog.open(encoding="utf-8", newline="") as handle:
        valid = {row["sku"] for row in csv.DictReader(handle)}
    result = validate_sales_csv(args.sales_csv, valid)
    print(f"Valid observations: {len(result)}")
