import csv
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_private_workbooks_and_raw_sales_are_gitignored():
    for target in [
        "data/private/demonstrativo_original.xlsx",
        "data/coleta/vendas_diarias.csv",
        "output/bardojonas.sqlite3",
    ]:
        check = subprocess.run(
            ["git", "check-ignore", "-q", target], cwd=ROOT, check=False
        )
        assert check.returncode == 0, f"Private/generated path may be committed: {target}"


def test_public_data_has_no_business_contacts_or_personal_ledger():
    sources = list((ROOT / "data/public").glob("*.csv"))
    assert len(sources) == 2
    for file in sources:
        text = file.read_text(encoding="utf-8")
        assert not re.search(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", text)
        assert not re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
        assert not re.search(r"\(\d{2}\)\s*\d[\d.\- ]{7,}", text)
        assert not re.search(r"\b(?:sal[aá]rio|hora extra|colaborador|cpf)\b", text, re.I)
    with (ROOT / "data/public/compras_2019.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    individual_suppliers = [
        row["fornecedor"] for row in rows
        if row["fornecedor"].startswith("Fornecedor local")
    ]
    assert set(individual_suppliers) == {"Fornecedor local A", "Fornecedor local B"}


def test_public_repository_has_no_recorded_sales_or_raw_spreadsheet():
    tracked = subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True
    ).splitlines()
    assert not any(path.endswith((".xlsx", ".xls")) for path in tracked)
    model = (ROOT / "data/coleta/vendas_diarias_modelo.csv").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(model) == 1
    assert not (ROOT / "data/public/vendas_2019.csv").exists()


def test_extraction_code_does_not_publish_private_supplier_mapping():
    source = (ROOT / "scripts/build_dataset.py").read_text(encoding="utf-8")
    assert "PRIVATE_SUPPLIERS" not in source
    assert "PUBLIC_SUPPLIERS" in source
