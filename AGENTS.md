# LOGage 2026 — Agent Guide

**Domain**: This repo solves the *LOGage 2026* supply-chain examination (Round 2). The scenario is an omni-channel distributor running two warehouses (My Phuoc, Vinh Loc) that must profile outbound flow, design fulfillment strategy, and optimize warehouse operations. All analysis answers explicit exam questions Q1.1–Q3.2.

| Part | Questions | What the code produces |
|------|-----------|----------------------|
| 1 — Network Profiling | Q1.1 ABC-XYZ, Q1.2 Distribution heatmap, Q1.3 Order profile (Modern Trade vs Traditional) | ABC-XYZ matrix, province/region demand tables, segment profile comparisons, missing-data diagnostics |
| 2 — Fulfillment Strategy | Q2.1 Network model evaluation, Q2.2 Safety stock & inventory pooling | Safety stock per Class A SKU, lead-time sensitivity, HCMC district analysis, channel-flow summary |
| 3 — Warehouse Ops | Q3.1 Slotting optimization, Q3.2 Omni-channel pick-and-pack process | Slotting plan, pick-profile, travel-time metrics, flowchart image |

## Pipeline entrypoint
```bash
python run_analysis.py
```
Regenerates cleaned CSVs (`data/cleaned/`), tables (`outputs/tables/`), charts (`outputs/charts/`), notes (`outputs/notes/`), and Excel workbooks (`outputs/summary_table.xlsx`, `data/cleaned/cleaned_data.xlsx`).

## Module roles
- `loading.py` — reads 3 Excel files from `data/raw/`
- `cleaning.py` — normalizes SKU master, distributors, shipments; decorated with `@log_quality` (appends to `data.log`)
- `analysis.py` — builds all summary tables (Q1.1–Q2.1, Part 3 slotting)
- `geography.py` — address parsing via `vietnamadminunits`, province mapping, distance calculations
- `visuals.py` — matplotlib charts (uses `outputs/.matplotlib/` as config dir)
- `notes.py` — writes LaTeX `.tex` files and runs `pdflatex` via subprocess
- `excel_reports.py` — styled openpyxl workbooks

## Module CLI
```bash
python src/logage2026/cleaning.py --sku --distributor --shipment
python src/logage2026/cleaning.py --all
```
Also supports `--geography` for a geocoding demo.

## Inputs at repo root
- `customer_segment_overrides.csv` — manual segment overrides
- `vietnam_provinces.json` — GeoJSON boundaries (used by visuals)
- `LOGage2026_Q1.1_ABC_XYZ_Analysis.xlsx` — reference workbook (not regenerated)

## Notable code conventions
- Every `src/logage2026/*.py` module appends `sys.path` to reach the repo root (`parents[2]`)
- `config.py` is the single source of truth for all paths and thresholds
- Part 1 notes go to `outputs/notes/part1_question_summary.tex`, Part 2 → `part2_question_summary.tex`, Part 3 → `part3_question_summary.tex`
- `data.log` is appended to by the `@log_quality` decorator; do not commit it
- Analysis uses `Int64`/`Float64` nullable dtypes, not numpy `int`/`float`

## Verification
Smoke test: `python run_analysis.py`. It prints row/SKU/KPI totals; compare against `run_analysis.py` constants (e.g. `EXPECTED_ASSIGNMENT_ROWS`). No test framework is set up yet — create `tests/` with `pytest` if adding non-trivial logic.

## Git style
Short imperative subjects, `fix:` prefix for bug fixes. Keep commits scoped and descriptive.
