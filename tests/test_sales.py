import csv
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from scripts.validate_sales import validate_sales_csv


ROOT = Path(__file__).resolve().parents[1]
VALID_SKUS = {"brahma-600ml", "skol-300ml"}


def make_sales(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "data", "sku", "quantidade_vendida", "preco_unitario_brl", "origem_registo"
        ])
        writer.writeheader()
        writer.writerows(rows)


def test_empty_daily_template_is_not_a_sale():
    result = validate_sales_csv(
        ROOT / "data/coleta/vendas_diarias_modelo.csv", VALID_SKUS
    )
    assert result == []


def test_real_observation_is_typed_and_retained(tmp_path):
    path = tmp_path / "vendas.csv"
    make_sales(path, [{
        "data": "2026-11-09", "sku": "brahma-600ml",
        "quantidade_vendida": "4", "preco_unitario_brl": "8.50",
        "origem_registo": "caderno"
    }])

    assert validate_sales_csv(path, VALID_SKUS) == [{
        "data": "2026-11-09", "sku": "brahma-600ml",
        "quantidade_vendida": 4, "preco_unitario_brl": Decimal("8.50"),
        "origem_registo": "caderno"
    }]


@pytest.mark.parametrize("date_text,quantity,sku", [
    ("2026-02-30", "3", "brahma-600ml"),
    ("2026-11-09", "0", "brahma-600ml"),
    ("2026-11-09", "-2", "brahma-600ml"),
    ("2026-11-09", "3", "cerveja-inexistente"),
])
def test_invalid_observations_cannot_enter_dataset(tmp_path, date_text, quantity, sku):
    path = tmp_path / "vendas.csv"
    make_sales(path, [{
        "data": date_text, "sku": sku, "quantidade_vendida": quantity,
        "preco_unitario_brl": "8.50", "origem_registo": "caderno"
    }])
    with pytest.raises(ValueError):
        validate_sales_csv(path, VALID_SKUS)


def test_reject_duplicate_daily_sale_lines(tmp_path):
    path = tmp_path / "vendas.csv"
    row = {
        "data": "2026-11-09", "sku": "brahma-600ml",
        "quantidade_vendida": "4", "preco_unitario_brl": "8.50",
        "origem_registo": "caderno"
    }
    make_sales(path, [row, row])
    with pytest.raises(ValueError, match="Duplicate"):
        validate_sales_csv(path, VALID_SKUS)


@pytest.mark.parametrize("body", [
    "",
    "produto,quantidade\n",
    "data,sku,quantidade_vendida,preco_unitario_brl,origem_registo\n"
    "2026-11-09,brahma-600ml,3,8.50\n",
    "data,sku,quantidade_vendida,preco_unitario_brl,origem_registo\n"
    "2026-11-09,brahma-600ml,3,8.50,caderno,extra\n",
    "data,sku,sku,preco_unitario_brl,origem_registo\n",
])
def test_invalid_csv_structure_is_rejected(tmp_path, body):
    source = tmp_path / "invalid.csv"
    source.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError, match="CSV"):
        validate_sales_csv(source, VALID_SKUS)


def test_documented_module_cli_accepts_header_only_template():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.validate_sales",
         "data/coleta/vendas_diarias_modelo.csv"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Valid observations: 0" in result.stdout
