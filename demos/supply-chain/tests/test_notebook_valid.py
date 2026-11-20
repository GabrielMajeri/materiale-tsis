"""Structural and syntax validation for notebooks/supply_chain_lab.ipynb."""

from __future__ import annotations

import ast
from pathlib import Path

import nbformat


def test_lab_notebook_is_valid_nbformat_and_syntax() -> None:
    nb_path = Path(__file__).resolve().parent.parent / "notebooks" / "supply_chain_lab.ipynb"
    assert nb_path.exists(), f"Missing notebook at {nb_path}"

    nb = nbformat.read(nb_path, as_version=4)
    nbformat.validate(nb)
    assert len(nb.cells) >= 12

    full_text = "\n".join(cell.source for cell in nb.cells)
    for ex_num in (1, 2, 3, 4):
        assert f"Exercise {ex_num}" in full_text

    # Verify students are not instructed to call asyncio.run() inside Jupyter
    code_cells = [cell for cell in nb.cells if cell.cell_type == "code"]
    md_cells = [cell for cell in nb.cells if cell.cell_type == "markdown"]
    assert len(code_cells) >= 6
    assert len(md_cells) >= 6

    for idx, cell in enumerate(code_cells):
        source = cell.source.strip()
        assert source, f"Code cell {idx} is empty"
        assert "asyncio.run(" not in source, f"Code cell {idx} should use top-level await, not asyncio.run()"
        compile(source, f"supply_chain_lab_cell_{idx}.py", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
