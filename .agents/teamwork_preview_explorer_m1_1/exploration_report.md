# Codebase Exploration Report: Supervisor Feedback Inconsistencies

This report details the exact files, line ranges, current implementations, and recommended modifications to address the supervisor feedback regarding the LOGage 2026 Round 2 calculations, tables, charts, and compiled reports.

---

## 1. Q1.3 Customer Segment Order Frequency

### Exact Files and Line Ranges
* **Calculations & Data Processing:**
  * `src/logage2026/analysis.py` — Lines 801–827 (`_prepare_segment_order_lines`)
  * `src/logage2026/analysis.py` — Lines 830–891 (`build_q13_segment_profile_summary`)
* **Excel Report Generation:**
  * `src/logage2026/excel_reports.py` — Line 89 (Writes `q13_segment_profile_summary` to sheet `"Q1.3 Segment Profile"` in `write_summary_workbook`).
* **LaTeX Report Generation:**
  * `src/logage2026/notes.py` — Line 50 (Initializes `segments` Series dictionary).
  * `src/logage2026/notes.py` — Line 508 (Writes the "Order Frequency" table row).
* **Charts Generation:**
  * `src/logage2026/visuals.py` — Lines 525–548 (`_order_profile_chart` generates chart `q13_order_profile_comparison.png`).

### Technical Description of Current Implementation
* `_prepare_segment_order_lines` copies shipments with active analysis flags and groups them by `["customer_segment", "order_id"]`.
* `order_id` is defined in `src/logage2026/cleaning.py` line 412: `frame["order_id"] = frame["source_warehouse"] + "-" + frame["document_no"]`. This uniquely identifies orders by concatenated warehouse and document number, thus correctly counting distinct document numbers rather than total transaction rows.
* In `build_q13_segment_profile_summary`, customer order frequency is computed as:
  ```python
  customer_orders = known.groupby(["customer_segment", "customer_key"], dropna=False)["order_id"].nunique().reset_index()
  customer_orders["orders_per_month"] = customer_orders["order_id"] / 6.0
  avg_freq = customer_orders.groupby("customer_segment", dropna=False)["orders_per_month"].mean().rename(
      "avg_orders_per_customer_month"
  )
  ```
  This divides the total unique orders by `6.0` to calculate orders per month and then averages across all customers. It does not calculate frequency normalized by active months or reflect the actual 7-month duration of the Assignment Window (June 1 – December 31, 2025).

### Specific Recommendations
1. **Modify `build_q13_segment_profile_summary` in `src/logage2026/analysis.py`:**
   * Compute the active months for each customer by counting unique year-months from `created_date`:
     ```python
     known["year_month"] = known["created_date"].dt.to_period("M")
     customer_active_months = known.groupby(["customer_segment", "customer_key"], dropna=False)["year_month"].nunique().reset_index(name="active_months")
     customer_orders = known.groupby(["customer_segment", "customer_key"], dropna=False)["order_id"].nunique().reset_index(name="order_count")
     customer_freq = customer_orders.merge(customer_active_months, on=["customer_segment", "customer_key"])
     ```
   * Calculate **7-Month Normalized Frequency** (using `7.0` months):
     ```python
     customer_freq["freq_7m"] = customer_freq["order_count"] / 7.0
     ```
   * Calculate **Active Months Average Frequency** (using the count of active months):
     ```python
     customer_freq["freq_active"] = customer_freq["order_count"] / customer_freq["active_months"]
     ```
   * Group by segment and compute the average of both metrics across all customers:
     ```python
     avg_freq_7m = customer_freq.groupby("customer_segment", dropna=False)["freq_7m"].mean().rename("normalized_frequency_7m")
     avg_freq_active = customer_freq.groupby("customer_segment", dropna=False)["freq_active"].mean().rename("active_month_frequency")
     ```
   * Return both columns (`normalized_frequency_7m` and `active_month_frequency`) in the returned summary table.
2. **Modify `write_summary_workbook` in `src/logage2026/excel_reports.py`:**
   * No changes needed as the sheet `"Q1.3 Segment Profile"` will automatically include the new columns.
3. **Modify `write_notes` in `src/logage2026/notes.py`:**
   * Replace the single "Order Frequency (per customer/month)" row with two separate rows:
     * `\textbf{7-Month Normalized Frequency (per customer/month)} & {mt_prof['normalized_frequency_7m']:.2f} & {tt_prof['normalized_frequency_7m']:.2f} \\\\`
     * `\textbf{Active Months Average Frequency (per customer/month)} & {mt_prof['active_month_frequency']:.2f} & {tt_prof['active_month_frequency']:.2f} \\\\`
   * Update the report text to explain the difference between the two metrics (active-month frequency yields `7.10` for Modern Trade).
4. **Modify `_order_profile_chart` in `src/logage2026/visuals.py`:**
   * Update the plotted frequency column to `normalized_frequency_7m` or plot both metrics as separate bars in the panel.

---

## 2. Q1.1 ABC-Frequency & ABC-Volatility Matrices

### Exact Files and Line Ranges
* **Calculations:**
  * `src/logage2026/analysis.py` — Lines 129–230 (`build_abc_xyz`)
  * `src/logage2026/analysis.py` — Lines 232–243 (`build_abc_xyz_matrix_summary`)
  * `src/logage2026/analysis.py` — Lines 249–267 (`build_fast_moving_summary`)
* **Excel Report Generation:**
  * `src/logage2026/excel_reports.py` — Lines 290–324 (Writes Frequency matrix section)
  * `src/logage2026/excel_reports.py` — Lines 348–374 (Writes Volatility matrix section)
* **LaTeX Report Generation:**
  * `src/logage2026/notes.py` — Lines 61–67 (Reads frequency matrix cells)
  * `src/logage2026/notes.py` — Lines 158–167 (Defines counts for specific matrix intersections)
  * `src/logage2026/notes.py` — Lines 278–360 (Writes out ABC-XYZ classification sections)
* **Charts Generation:**
  * `src/logage2026/visuals.py` — Lines 274–292 (`_xyz_frequency_bar` generates `q11_xyz_frequency_distribution.png`)
  * `src/logage2026/visuals.py` — Lines 294–314 (`_abc_xyz_matrix_chart` generates heatmaps)

### Technical Description of Current Implementation
* Currently, both order frequency and demand volatility are classified under the "XYZ" label.
* `xyz_frequency` classifies SKUs by order frequency share using "X", "Y", "Z" labels.
* `xyz_volatility` classifies SKUs by demand coefficient of variation (CV) using "X", "Y", "Z" labels.
* This duplicate "XYZ" usage creates terminology confusion. The joint frequency matrix is labeled as "Combined ABC-XYZ Matrix — Frequency" and the fast-moving group is defined as Class A-X.

### Specific Recommendations
1. **Modify `build_abc_xyz` in `src/logage2026/analysis.py`:**
   * Rename the order frequency classification column to `abc_frequency`.
   * Use labels `"A"`, `"B"`, `"C"` instead of `"X"`, `"Y"`, `"Z"`.
   * Define the **Fast-Moving SKU group** as **Class AA** (representing intersection of quantity Class A and frequency Class A).
   * Update `fast_moving_flag` to:
     ```python
     sku["fast_moving_flag"] = (
         sku["abc_quantity"].eq("A")
         & sku["abc_frequency"].eq("A")
     ).astype(int)
     ```
2. **Modify `_abc_xyz_matrix_chart` in `src/logage2026/visuals.py`:**
   * Check the columns of the input DataFrame:
     * If the second column is `abc_frequency`, reindex using `columns=["A", "B", "C"]` and label the X-axis "ABC Frequency Class". Title the chart "ABC-Frequency SKU Count Matrix".
     * If the second column is `xyz_volatility`, reindex using `columns=["X", "Y", "Z"]` and label the X-axis "XYZ Volatility Class". Title the chart "ABC-Volatility SKU Count Matrix".
   * Rename the frequency distribution chart function to `_abc_frequency_bar` and change its labels to "A", "B", "C". Save it as `q11_abc_frequency_distribution.png`.
3. **Modify `src/logage2026/excel_reports.py`:**
   * Rename Section C to `"C.  ABC-FREQUENCY MATRIX"`. Reindex the columns to `["A", "B", "C"]`. Update headers to `["", "A (High Freq)", "B (Med Freq)", "C (Low Freq)", ...]` and lookup values in `matrix_freq` accordingly.
   * Rename Section E to `"E.  ABC-VOLATILITY MATRIX"`. Keep columns as `["X", "Y", "Z"]` (Stable, Seasonal, Erratic).
4. **Modify `src/logage2026/notes.py`:**
   * Update the cell parser to use `row['abc_frequency']` instead of `row['xyz_frequency']`.
   * Look up counts for cell `('A', 'A')` (Class AA) and rename groups: Class AA instead of A-X, Class AB/AC instead of A-Y/A-Z, Class BA/CA instead of B-X/C-X, and Class CC instead of C-Z.
   * Update all LaTeX labels, captions, and section titles to match these new nomenclatures.

---

## 3. Q2.1 Coordinated Two-RDC Assessment

### Exact Files and Line Ranges
* **LaTeX Report Generation:**
  * `src/logage2026/notes.py` — Lines 607–618 (Warehouse timeline assessment)
  * `src/logage2026/notes.py` — Lines 674–679 (Routing logic description)

### Technical Description of Current Implementation
* The report highlights that My Phuoc and Vinh Loc had non-overlapping active windows in the historical dataset (June–November vs. December 2025).
* It then introduces a dynamic warehouse routing model that splits HCMC orders between the two warehouses based on distance thresholds, creating a logical contradiction (non-overlapping facilities cannot dynamically coordinate).

### Specific Recommendations
1. **Modify `write_notes` in `src/logage2026/notes.py`:**
   * Reframe the non-overlapping operating timelines: state that this is a **retrospective data limitation** of the historical dataset, rather than a permanent operational structure.
   * Add explicit analysis describing the **future strategy** where both RDCs operate simultaneously and coordinate dynamically under the order-split routing logic.
2. **Dynamize RDCs Order Split:**
   * In `build_network_model_evaluation` or `notes.py`, calculate the exact number of orders and volume share from the HCMC dataset that fall under each routing condition:
     1. **Vinh Loc RDC**: delivery address is within 25 km of Vinh Loc.
     2. **My Phuoc RDC**: address is within 35 km of My Phuoc and > 25 km from Vinh Loc.
     3. **Dark Store**: address is > 25 km from Vinh Loc and > 35 km from My Phuoc.
   * Output these dynamic shares (percentage and count of orders/quantity) in the LaTeX report table and text.

---

## 4. Q2.1 Travel Time Formula & Dark Store SLA Recalculation

### Exact Files and Line Ranges
* **Calculations:**
  * `src/logage2026/analysis.py` — Lines 1312–1340 (`build_network_model_evaluation` needs implementation of the travel time formula and scenario comparison).
* **Excel Report:**
  * `src/logage2026/excel_reports.py` — Line 96 (Writes the HCMC districts sheet). We must add a comparison section or sheet for Baseline vs. 2 Dark Stores.
* **LaTeX Report:**
  * `src/logage2026/notes.py` — Lines 80–90 (Calculates RDC/Dark Store SLA indicators).
  * `src/logage2026/notes.py` — Lines 634–650 (SLA assessment text).

### Technical Description of Current Implementation
* Travel times are currently estimated using a simplistic linear speed-to-distance model: `(df["best_rdc_km"] / 25 * 60)`. It does not apply traffic factors, pick-pack overhead, dispatch buffers, or service times.
* Suits for SLA coverage are determined using a simple distance threshold (`best_rdc_km <= 25` km).
* There is no comparative modeling for a Baseline (Vinh Loc only) vs. 2 Dark Stores.

### Specific Recommendations
1. **Implement Travel Time Formula in `src/logage2026/analysis.py`:**
   * Add the travel time calculation helper:
     ```python
     def get_travel_time(distance, speed, traffic_factor, overhead):
         if pd.isna(distance):
             return np.nan
         return (distance / speed) * 60 * traffic_factor + overhead
     ```
   * Classify HCMC districts into traffic zones:
     * **Inner-city (Traffic Factor = 1.8):** `Quận 1`, `Quận 3`, `Quận 4`, `Quận 5`, `Quận 6`, `Quận 10`, `Quận 11`, `Gò Vấp`, `Bình Thạnh`, `Phú Nhuận`, `Tân Bình`, `Tân Phú`.
     * **Suburban (Traffic Factor = 1.4):** `Thủ Đức`, `Bình Tân`, `Bình Chánh`, `Quận 7`, `Quận 8`, `Quận 12`, `Hóc Môn`, `Nhà Bè`.
     * **Outer (Traffic Factor = 1.2):** `Củ Chi`.
2. **Model 2 Dark Stores:**
   * Define coordinates of the 2 Dark Stores:
     * **Dark Store 1 (Bình Tân / Tân Phú corridor):** Coordinates of Tân Phú (10.7848, 106.6267).
     * **Dark Store 2 (District 1 / District 3 / Phú Nhuận CBD):** Coordinates of Quận 1 (10.7735, 106.6982).
   * Calculate distances from each district's average coordinates to both dark stores using the Haversine formula.
3. **Compare Scenarios:**
   * **Baseline Scenario (Vinh Loc RDC only):**
     * Distance is `avg_dist_vinh_loc`.
     * Overhead is `90.0` min.
     * `Travel_Time_Baseline = get_travel_time(avg_dist_vinh_loc, 30.0, traffic_factor, 90.0)`
     * SLA check: 2H met if `<= 120` min; 4H met if `<= 240` min.
   * **2 Dark Stores Scenario (Vinh Loc RDC + DS1 + DS2):**
     * Route each district to the nearest node among Vinh Loc RDC, DS1, and DS2.
     * Distance is `min(avg_dist_vinh_loc, dist_ds1, dist_ds2)`.
     * Overhead is `90.0` min (if Vinh Loc is nearest) or `35.0` min (if DS1 or DS2 is nearest).
     * `Travel_Time_2DS = get_travel_time(distance, 30.0, traffic_factor, overhead)`
     * SLA check: 2H met if `<= 120` min; 4H met if `<= 240` min.
4. **Compile Comparative Outputs:**
   * Calculate **4H SLA Coverage**, **2H SLA Coverage** (using quantity share of districts meeting the SLAs), **Weighted Distance Savings** in km and percentage, and **Dark Store Daily Throughput** (assigned volume / operational days).
   * Return these comparison metrics from `build_network_model_evaluation`.
   * Export the comparison metrics to a dedicated sheet/section in `summary_tables.xlsx` via `excel_reports.py`.
   * Include the travel time formula and comparison results table dynamically in `notes.py` for the LaTeX report.
