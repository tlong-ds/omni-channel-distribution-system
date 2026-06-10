## 2026-06-10T05:45:40Z
You are teamwork_preview_worker. Your working directory is `/Users/bunnypro/Projects/LOGage2026/.agents/teamwork_preview_worker_m2_1/`.
Your task is to implement all supervisor feedback inconsistencies in the calculations, tables, charts, and compiled reports as requested.

MANDATORY INTEGRITY WARNING:
> DO NOT CHEAT. All implementations must be genuine. DO NOT
> hardcode test results, create dummy/facade implementations, or
> circumvent the intended task. A Forensic Auditor will independently
> verify your work. Integrity violations WILL be detected and your
> work WILL be rejected.

Please implement the following changes:

### 1. Customer Segment Order Frequency Recalculation (Q1.3)
- In `src/logage2026/analysis.py`, modify `build_q13_segment_profile_summary`:
  - Calculate `active_months` for each customer: count the number of unique year-months (`YYYY-MM`) present in the customer's transaction history (`created_date`).
  - Calculate the unique order count (`order_id`) for each customer.
  - Calculate **7-Month Normalized Frequency**: `order_count / 7.0`.
  - Calculate **Active Months Average Frequency**: `order_count / active_months`.
  - Compute the segment-level average of both metrics across all customers within each segment.
  - Include the columns `"normalized_frequency_7m"` and `"active_month_frequency"` in the returned summary DataFrame.
- In `src/logage2026/visuals.py`:
  - Update `_order_profile_chart` (which generates `q13_order_profile_comparison.png`) to plot the new frequency column or columns appropriately.
- In `src/logage2026/notes.py`:
  - Update the LaTeX compilation to write both metrics in the order profile comparison table.
  - Update the accompanying report text to discuss the difference between the 7-month normalized frequency and active-months average frequency (specifically noting that Modern Trade active-month frequency yields 7.10).
- In `src/logage2026/excel_reports.py`:
  - Verify that writing `q13_segment_profile_summary` to sheet `"Q1.3 Segment Profile"` handles the new columns correctly.

### 2. ABC-Frequency & ABC-Volatility Matrices (Q1.1)
- In `src/logage2026/analysis.py`:
  - In `build_abc_xyz`, rename `xyz_frequency` column to `abc_frequency`.
  - Map `abc_frequency` cumulative share to labels `"A"`, `"B"`, `"C"` instead of `"X"`, `"Y"`, `"Z"`.
  - Rename the combination column `abc_xyz_frequency` to `abc_frequency_matrix` (or keep the name but contain combinations like `"AA"`, `"AB"`, `"AC"`).
  - Define the Fast-Moving SKU group as **Class AA** (where `abc_quantity == "A"` and `abc_frequency == "A"`). Ensure `fast_moving_flag` is set based on this.
- In `src/logage2026/excel_reports.py`:
  - Rename Section C to `"C.  ABC-FREQUENCY MATRIX"`. Reindex and lookup cell counts using the new `"A"`, `"B"`, `"C"` frequency labels.
  - Rename Section E to `"E.  ABC-VOLATILITY MATRIX"`. Ensure it continues to map `abc_quantity` against `xyz_volatility` (`"X"`, `"Y"`, `"Z"`).
- In `src/logage2026/visuals.py`:
  - Update heatmap generation in `_abc_xyz_matrix_chart` to support both matrices: the ABC-Frequency matrix (using columns/index `"A"`, `"B"`, `"C"`, titled "ABC-Frequency SKU Count Matrix") and the ABC-Volatility matrix (using columns `"X"`, `"Y"`, `"Z"`, titled "ABC-Volatility SKU Count Matrix").
  - Rename the frequency distribution bar chart function/file to `_abc_frequency_bar` / `q11_abc_frequency_distribution.png` and use labels `"A"`, `"B"`, `"C"`.
- In `src/logage2026/notes.py`:
  - Update LaTeX text and tables to use the new naming conventions (`abc_frequency`, Class AA, Class AB, etc.) and fetch values using the renamed columns.

### 3. Coordinated Two-RDC Assessment (Q2.1)
- In `src/logage2026/notes.py`:
  - Reframe the discussion of non-overlapping operating timelines: present it as a retrospective data limitation of the historical dataset rather than a permanent operational restriction.
  - Describe the future strategy where both RDCs operate dynamically together.
  - Compute the actual routed order and volume splits for HCMC:
    - Vinh Loc RDC: distance to Vinh Loc <= 25 km.
    - My Phuoc RDC: distance to My Phuoc <= 35 km and distance to Vinh Loc > 25 km.
    - Dark Store: distance to Vinh Loc > 25 km and distance to My Phuoc > 35 km.
  - Include these splits (order share % and volume share %) in the text/tables.

### 4. Travel Time Formula & Dark Store SLA Recalculation (Q2.1)
- In `src/logage2026/analysis.py`:
  - Modify `build_network_model_evaluation` to implement the travel time verification formula:
    $$\text{Travel Time (min)} = \frac{\text{Distance (km)}}{\text{Speed (km/h)}} \times 60 \times \text{Traffic Factor} + \text{Pick-Pack} + \text{Dispatch Buffer} + \text{Service Time}$$
    - Speed = 30.0 km/h
    - RDC overhead = 90 min (for Vinh Loc RDC)
    - Dark Store overhead = 35 min (for DS1 and DS2)
    - Traffic factor: 1.8 (inner-city), 1.4 (suburban), 1.2 (outer)
  - Map HCMC districts to traffic zones:
    - Inner-city (1.8): `Quận 1`, `Quận 3`, `Quận 4`, `Quận 5`, `Quận 6`, `Quận 10`, `Quận 11`, `Gò Vấp`, `Bình Thạnh`, `Phú Nhuận`, `Tân Bình`, `Tân Phú`.
    - Suburban (1.4): `Thủ Đức`, `Bình Tân`, `Bình Chánh`, `Quận 7`, `Quận 8`, `Quận 12`, `Hóc Môn`, `Nhà Bè`.
    - Outer (1.2): `Củ Chi`.
  - Model 2 Dark Stores:
    - DS1 (Tân Phú): coordinates `(10.7848, 106.6267)`
    - DS2 (Quận 1): coordinates `(10.7735, 106.6982)`
  - Compare **Baseline (Vinh Loc only)** vs. **2 Dark Stores (Vinh Loc + DS1 + DS2)**:
    - Baseline: each district is served by Vinh Loc RDC. Distance is `avg_dist_vinh_loc`. Travel time uses Vinh Loc RDC overhead (90 min).
    - 2 Dark Stores: each district is routed to the nearest among Vinh Loc RDC, DS1, and DS2. Distance is `min(avg_dist_vinh_loc, dist_ds1, dist_ds2)`. Overhead is 90 min if Vinh Loc is nearest, and 35 min if DS1 or DS2 is nearest.
    - Check SLAs: 2H SLA met if travel time <= 120 min, 4H SLA met if travel time <= 240 min.
    - Calculate and output: 4H SLA coverage (quantity-weighted), 2H SLA coverage (quantity-weighted), weighted distance savings (km and % reduction), and dark store daily throughput (total quantity routed to DS1 and DS2 divided by the number of active transaction days in the HCMC dataset, or a standard 214 operational days - make it clear in the report).
- In `src/logage2026/excel_reports.py`:
  - Export this comparative results table to a new sheet `"Q2.1 Dark Store SLA"` in `summary_tables.xlsx`.
- In `src/logage2026/notes.py`:
  - Dynamically write this comparison table and the travel time formula into the LaTeX report.

Verify that `run_analysis.py` runs without errors after all changes are integrated, and all outputs are updated under `outputs/round2/`.

Update `progress.md` in your working directory at every step and send a message when done.
