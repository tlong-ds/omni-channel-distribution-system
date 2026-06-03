# Repository Guidelines

## Project Structure & Module Organization
Core code lives in `src/logage2026/`. Keep responsibilities separated by module: `loading.py` reads the Excel inputs, `cleaning.py` normalizes source data, `analysis.py` builds tables and validation checks, `visuals.py` renders charts, and `notes.py` writes markdown summaries. Use `run_analysis.py` as the main entry point for the full Round 2 pipeline.

Source documents stay at the repository root, including the three Excel inputs, `vietnam_provinces.json`, and supporting notes such as `notebook.ipynb` and `note.md`. Generated artifacts belong under `outputs/round2/` in `cleaned/`, `tables/`, `charts/`, and `notes/`.

## Build, Test, and Development Commands
Run the full workflow with:

```bash
python run_analysis.py
```

This regenerates cleaned CSVs, summary tables, charts, and notes under `outputs/round2/`.

For targeted cleaning work, use the module CLI:

```bash
python src/logage2026/cleaning.py --all
python src/logage2026/cleaning.py --sku
python src/logage2026/cleaning.py --shipment
```

Use a virtual environment and install the Python dependencies actually imported here, notably `pandas`, `numpy`, `matplotlib`, `openpyxl`, and `vietnamadminunits`.

## Coding Style & Naming Conventions
Follow existing Python style: 4-space indentation, type hints where useful, and small single-purpose functions. Use `snake_case` for functions, variables, and output filenames such as `warehouse_region_summary.csv`. Keep constants uppercase in `config.py` or near the top of a module.

Prefer explicit paths from `src/logage2026/config.py` instead of hardcoding file locations in new modules.

## Testing Guidelines
There is no dedicated `tests/` directory yet. Treat `python run_analysis.py` as the required smoke test and do not commit changes that break its built-in `verify_outputs()` checks. When adding non-trivial logic, create focused `pytest` tests in a new `tests/` package and name files `test_<module>.py`.

## Commit & Pull Request Guidelines
Recent history uses short, imperative subjects such as `fix: update all modules...`, `reprocess data`, and `update new results`. Keep commits concise, scoped, and descriptive; use a `fix:` prefix for bug fixes when appropriate.

Pull requests should state which input assumptions changed, which modules were touched, and which outputs in `outputs/round2/` were regenerated. Include screenshots only when chart changes matter visually.
