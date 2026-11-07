from pathlib import Path
from importlib import reload
import os
import subprocess
import sys

import matplotlib
import nbformat

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]


def test_notebook_executes_fresh_and_reconciles_controls(capsys, monkeypatch):
    notebook = nbformat.read(ROOT / "notebooks/analise_bardojonas.ipynb", as_version=4)
    shown = []
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(plt, "show", lambda: shown.append(len(plt.get_fignums())))
    # Execute code cells in one fresh namespace. The managed test container
    # rejects ZeroMQ binds, which prevents a normal nbclient kernel startup.
    namespace = {"__name__": "__main__"}
    for cell in notebook.cells:
        if cell.cell_type == "code":
            exec(compile(cell.source, "<notebook>", "exec"), namespace)
    combined = capsys.readouterr().out
    assert "CONTROLOS: 59 linhas; 22 cervejas; 3948 unidades" in combined
    assert "Série temporal de vendas indisponível" in combined
    assert len(shown) >= 2
    plt.close("all")


def test_notebook_generator_has_stable_cell_ids():
    import scripts.create_notebook as notebook_source

    first = [cell["id"] for cell in notebook_source.cells]
    second = [cell["id"] for cell in reload(notebook_source).cells]
    assert first == second


def test_notebook_can_import_project_modules_when_opened_from_notebooks_dir():
    source = """from pathlib import Path
import nbformat
n = nbformat.read('analise_bardojonas.ipynb', as_version=4)
ns = {'__name__': '__main__'}
exec(compile(n.cells[2].source, '<setup>', 'exec'), ns)
from scripts.validate_sales import validate_sales_csv
print('module import succeeded')
"""
    env = dict(os.environ, PYTHONPATH="", MPLBACKEND="Agg", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        [sys.executable, "-c", source], cwd=ROOT / "notebooks", env=env,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "module import succeeded" in result.stdout
