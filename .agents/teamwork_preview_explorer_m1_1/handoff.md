# Handoff Report: Codebase Exploration for Supervisor Feedback Inconsistencies

## 1. Observation
- **Q1.3 Segment Profiling:**
  - In `src/logage2026/analysis.py`, segment profiling is performed in `build_q13_segment_profile_summary` (lines 830–891).
  - The order frequency is calculated at lines 878–882:
    ```python
    customer_orders = known.groupby(["customer_segment", "customer_key"], dropna=False)["order_id"].nunique().reset_index()
    customer_orders["orders_per_month"] = customer_orders["order_id"] / 6.0
    avg_freq = customer_orders.groupby("customer_segment", dropna=False)["orders_per_month"].mean().rename(
        "avg_orders_per_customer_month"
    )
    ```
  - In `src/logage2026/notes.py` at line 508:
    ```python
    f"\\textbf{{Order Frequency (per customer/month)}} & {mt_prof['avg_orders_per_customer_month']:.2f} & {tt_prof['avg_orders_per_customer_month']:.2f} \\\\"
    ```
- **Q1.1 ABC-XYZ/ABC-Volatility Matrices:**
  - In `src/logage2026/analysis.py` at lines 179–181:
    ```python
    sku["xyz_frequency"] = sku["frequency_cumulative_share"].apply(
        lambda x: classify_cumulative_share(x, labels=("X", "Y", "Z"))
    )
    ```
  - In `src/logage2026/analysis.py` at lines 187–190:
    ```python
    sku["fast_moving_flag"] = (
        sku["abc_quantity"].eq(FAST_MOVING_ABC_QUANTITY)
        & sku["xyz_frequency"].eq(FAST_MOVING_XYZ_FREQUENCY)
    ).astype(int)
    ```
  - In `src/logage2026/excel_reports.py` at line 290:
    ```python
    ws[f"B{r}"] = "C.  COMBINED ABC-XYZ MATRIX — FREQUENCY"
    ```
  - In `src/logage2026/excel_reports.py` at line 348:
    ```python
    ws[f"B{r}"] = "E.  COMBINED ABC-XYZ MATRIX — VOLATILITY"
    ```
  - In `src/logage2026/visuals.py` at lines 294–313: `_abc_xyz_matrix_chart` hardcodes `columns=["X", "Y", "Z"]` for reindexing (line 297).
- **Q2.1 Coordinated Two-RDC Assessment:**
  - In `outputs/round2/notes/part2_question_summary.tex` (lines 41–45) and `src/logage2026/notes.py` (lines 607–611):
    ```latex
    \textbf{Important context: Non-overlapping operating timelines}
    \begin{itemize}
      \item \textbf{My Phuoc} (Primary RDC: Jun to Nov 2025 (6 months)): The \textit{primary} warehouse, operational across the full 6-month analysis window. All June--November 2025 throughput flowed through My Phuoc.
      \item \textbf{Vinh Loc} (New RDC: Dec 2025 only (1 month)): A \textit{new} warehouse that came online in December 2025 only. Raw volume totals are therefore \textbf{not directly comparable} between the two facilities.
    \end{itemize}
    ```
  - The routing logic is described at lines 674–679 in `src/logage2026/notes.py`:
    ```latex
    \textbf{Recommended order split logic:} Given this concentration, the dispatch decision tree should be:
    \begin{enumerate}
      \item If delivery district is within 25 km of Vinh Loc $\rightarrow$ dispatch from \textbf{Vinh Loc} (B2C-optimized lane).
      \item If delivery district is within 35 km of My Phuoc but $>$25 km from Vinh Loc $\rightarrow$ dispatch from \textbf{My Phuoc} (B2B bulk lane).
      \item If district is $>$25 km from both RDCs $\rightarrow$ \textbf{route via dark store} (pending network expansion).
    \end{enumerate}
    ```
- **Q2.1 Travel Time & Dark Store SLA Recalculation:**
  - In `src/logage2026/analysis.py`, lines 1312–1340 (`build_network_model_evaluation`) only contains:
    ```python
    df["est_delivery_min"] = (df["best_rdc_km"] / 25 * 60).round(0).astype(int)
    df["can_meet_2h_sla"] = df["best_rdc_km"] <= DARK_STORE_THRESHOLD_KM
    df["sla_status"] = np.where(
        df["can_meet_2h_sla"],
        "Adequate",
        "Needs Dark Store"
    )
    ```
  - There is no implementation of the detailed travel time formula, traffic zones/factors, or the Baseline (Vinh Loc only) vs. 2 Dark Stores scenario comparison.

## 2. Logic Chain
- **Step 1 (Q1.3):** The current division of orders by `6.0` in `analysis.py:879` ignores that the assignment window spans 7 months (June 1 – Dec 31, 2025) and lacks active-month normalization. To fix this, we must compute both `normalized_frequency_7m` and `active_month_frequency` per customer and average them across the segment, updating the LaTeX table and text to discuss both.
- **Step 2 (Q1.1):** The current code classifies both order frequency and demand volatility as "X, Y, Z", causing terminology confusion. To fix this, order frequency must be classified as `abc_frequency` (with labels "A", "B", "C") and the fast-moving group defined as Class AA. The matrix charts, Excel dashboard (Sections C and E), and LaTeX report must be updated to align with these names.
- **Step 3 (Q2.1 narrative):** Stating that My Phuoc and Vinh Loc have non-overlapping timelines in the historical data while presenting a coordinated order split logic creates a logical contradiction. To resolve this, we must frame the non-overlapping timelines as a retrospective data limitation and explicitly analyze the future strategy where both RDCs operate simultaneously. We must also calculate the actual routed order and volume splits dynamically to make the routing split analysis data-driven.
- **Step 4 (Q2.1 Travel Time SLA):** The current SLA suitability checks use a simple 25 km threshold and a linear speed model. We must implement the travel time formula, HCMC district traffic zone classifications, and coordinates for the 2 Dark Stores (Tân Phú for western corridor, Quận 1 for CBD) to compare Baseline vs 2 Dark Stores on 4H SLA, 2H SLA, weighted distance savings, and daily throughput.

## 3. Caveats
- *Assumptions:* We assume the traffic zones for HCMC districts are classified into:
  - Inner-city (1.8): Quận 1, Quận 3, Quận 4, Quận 5, Quận 6, Quận 10, Quận 11, Gò Vấp, Bình Thạnh, Phú Nhuận, Tân Bình, Tân Phú.
  - Suburban (1.4): Thủ Đức, Bình Tân, Bình Chánh, Quận 7, Quận 8, Quận 12, Hóc Môn, Nhà Bè.
  - Outer (1.2): Củ Chi.
- *Dark Store Coordinates:* We assume Dark Store 1 coordinates are placed at the center of Tân Phú (10.7848, 106.6267) and Dark Store 2 at Quận 1 (10.7735, 106.6982) based on the historical average coordinates.

## 4. Conclusion
We have completed a comprehensive read-only exploration of the codebase, identifying the exact files and line ranges where updates are required to resolve the supervisor feedback. We documented specific recommended code modifications and narrative edits in `/Users/bunnypro/Projects/LOGage2026/.agents/teamwork_preview_explorer_m1_1/exploration_report.md`.

## 5. Verification Method
- **Inspect Report:** Verify `/Users/bunnypro/Projects/LOGage2026/.agents/teamwork_preview_explorer_m1_1/exploration_report.md` exists and contains detailed sections for each of the 4 requirements.
- **Run Pipeline:** Execute the workflow script:
  ```bash
  ./logage_env/bin/python run_analysis.py
  ```
  to verify that the pipeline runs successfully in the virtual environment.
