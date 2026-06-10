# Project: LOGage 2026 Round 2 Inconsistencies Resolution

## Architecture
- Core pipeline flow:
  1. `cleaning.py` normalizes raw transaction logs, sku master data, and distributors.
  2. `analysis.py` computes metrics: SKU ABC-XYZ, Customer segments, Travel metrics, network evaluation, etc.
  3. `visuals.py` generates PNG charts.
  4. `excel_reports.py` writes Excel workbooks (`cleaned_data.xlsx`, `summary_tables.xlsx`).
  5. `notes.py` writes LaTeX files compiled to PDFs.
  6. `run_analysis.py` orchestrates the complete execution.

## Code Layout
- `run_analysis.py` - main pipeline entry point
- `src/logage2026/config.py` - configuration and path definitions
- `src/logage2026/loading.py` - data loading routines
- `src/logage2026/cleaning.py` - data cleaning routines
- `src/logage2026/analysis.py` - metrics and logic calculation
- `src/logage2026/visuals.py` - data visualization and charts
- `src/logage2026/excel_reports.py` - spreadsheet reports generator
- `src/logage2026/notes.py` - LaTeX documentation and text generation

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & Analysis | Investigate existing codebase and identify changes for Q1.3, Q1.1, Q2.1 narratives/formulas | None | IN_PROGRESS |
| 2 | Q1.3 Segment & Q1.1 ABC Matrix Fixes | Update distinct document logic, 7-month & active average calculations, ABC-Frequency/Volatility matrices | M1 | PLANNED |
| 3 | Q2.1 Travel SLA & RDC Fixes | Correct RDC narrative, implement travel time verification formula, and model SLA coverage comparison | M2 | PLANNED |
| 4 | E2E Verification & Compilation | Compile LaTeX reports to PDF, run `python run_analysis.py` smoke test and verify output files | M3 | PLANNED |

## Interface Contracts
### `analysis.py` -> `run_analysis.py`
- Calculation functions must return standard Pandas DataFrames or dictionaries of computed metrics.
- Modified calculations must not break existing function signatures or parameter counts.

### `excel_reports.py` / `visuals.py` / `notes.py` -> outputs
- Must consume the exact DataFrames produced by the revised analysis methods.
- Naming conventions like `ABC-Frequency` and `ABC-Volatility` must be aligned across Excel sheets, charts, and LaTeX documents.
