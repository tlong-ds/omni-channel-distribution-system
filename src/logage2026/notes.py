import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.logage2026.config import NOTES_DIR


NOTE_FILENAME = "part1_question_summary.md"


def write_notes(
    shipments: pd.DataFrame,
    abc_xyz: pd.DataFrame,
    abc_xyz_matrix: pd.DataFrame,
    fast_moving_summary: pd.DataFrame,
    classification_metadata: pd.DataFrame,
    missing_data_summary: pd.DataFrame,
    geography_coverage_summary: pd.DataFrame,
    warehouse_region_summary: pd.DataFrame,
    customer_cluster_summary: pd.DataFrame,
    warehouse_imbalance_summary: pd.DataFrame,
    q12_region_orders_quantity_summary: pd.DataFrame,
    q12_province_cluster_summary: pd.DataFrame,
    q12_province_demand_summary: pd.DataFrame,
    q12_province_warehouse_dominance_summary: pd.DataFrame,
    q12_urban_provincial_summary: pd.DataFrame,
    q12_warehouse_imbalance_visual_summary: pd.DataFrame,
    q13_segment_profile_summary: pd.DataFrame,
    q13_segment_packaging_summary: pd.DataFrame,
    q13_segment_geographic_spread_summary: pd.DataFrame,
) -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    metadata = classification_metadata.iloc[0] if not classification_metadata.empty else None
    missing = missing_data_summary.loc[
        missing_data_summary["source_warehouse"].eq("All")
        & missing_data_summary["document_type"].eq("All")
    ]
    missing_row = missing.iloc[0] if not missing.empty else None
    
    geo_cov = geography_coverage_summary.iloc[0] if not geography_coverage_summary.empty else None
    fast_mov = fast_moving_summary.iloc[0] if not fast_moving_summary.empty else None
    
    # Extract segments
    segments = {row['customer_segment']: row for _, row in q13_segment_profile_summary.iterrows()}
    mt_prof = segments.get("Modern Trade")
    tt_prof = segments.get("Traditional Trade / Distributor")
    
    # Extract segment packaging shares
    mt_pkg = q13_segment_packaging_summary[q13_segment_packaging_summary['customer_segment'] == 'Modern Trade']
    tt_pkg = q13_segment_packaging_summary[q13_segment_packaging_summary['customer_segment'] == 'Traditional Trade / Distributor']
    
    mt_pkg_shares = {row['packaging_unit']: row['quantity_share'] for _, row in mt_pkg.iterrows()}
    tt_pkg_shares = {row['packaging_unit']: row['quantity_share'] for _, row in tt_pkg.iterrows()}
    
    # Build dictionary of matrix cells
    matrix_dict = {}
    for _, row in abc_xyz_matrix.iterrows():
        matrix_dict[(row['abc_quantity'], row['xyz'])] = {
            'sku_count': int(row['sku_count']),
            'quantity': float(row['quantity']),
        }
        
    def get_cell_text(abc, xyz):
        cell = matrix_dict.get((abc, xyz))
        if cell is None:
            return "0 SKUs (0.00%)"
        sku_count = cell['sku_count']
        total_skus = len(abc_xyz)
        sku_share = sku_count / total_skus if total_skus else 0.0
        return f"{sku_count} SKUs ({sku_share:.2%})"
        
    total_skus = len(abc_xyz)
    class_a_skus = len(abc_xyz[abc_xyz['abc_quantity'] == 'A'])
    class_b_skus = len(abc_xyz[abc_xyz['abc_quantity'] == 'B'])
    class_c_skus = len(abc_xyz[abc_xyz['abc_quantity'] == 'C'])
    
    fast_mov_sku_share = fast_mov['sku_count'] / total_skus if total_skus else 0.0

    text = [
        "# Round 2 Executive Summary & Narrative Analysis",
        "",
        "## Executive Summary",
        "",
        "This report provides the outbound flow analysis, customer profiling, and geographic demand mapping for the Round 2 competition based on the transaction logs spanning June to December 2025. The core analysis focuses on the 6-month Assignment Window (July 1 – December 31, 2025), which contains **43,894 shipment rows**, **355,364.80 units of outbound demand**, and **19,653.78 CBM of volume**.",
        "",
        "Key takeaways include:",
        "1. **Extreme Assortment Concentration**: A tiny fraction of SKUs drives the vast majority of volume and warehouse activities. A dedicated 'Fast-Moving' group of 59 SKUs accounts for 65.06% of outbound quantity and 49.61% of order frequency.",
        "2. **ERP Centralized Invoicing Distortion**: Geographic demand analyses reveal that My Phuoc seemingly dominates 92.22% of resolved volume. However, this is an artificial bias caused by centralized ERP invoicing. In reality, Vinh Loc's raw outbound shipments account for 28.75% of total volume, but 80.10% of its transactions have missing customer names and are excluded from standard maps. Using **Approach A (Statistical Scaling)**, we restore and analyze the true 71.25% My Phuoc vs 28.75% Vinh Loc volume split.",
        "3. **Clear Segment Profiles**: Modern Trade orders are large, consolidated, and heavily palletized (69.17% of quantity). Traditional Trade orders are smaller, highly fragmented (51.49% carton / 8.07% loose), and spread across 57 provinces, presenting different operational picking requirements.",
        "",
        "---",
        "",
        "## Q1.1 Demand Pattern Classification (ABC-XYZ Analysis)",
        "",
        "The product assortment was analyzed across two dimensions using a joint ABC-XYZ matrix based on outbound volume (Quantity) and transaction frequency (Order Frequency) over the last 6 months of 2025. The overall concentration of shipped volume across SKUs is shown in Figure \\ref{fig:q11-abc-qty-dist}.",
        "",
        "![Q1.1 ABC quantity distribution\\label{fig:q11-abc-qty-dist}](../charts/q11_abc_quantity_distribution.png)",
        "",
        "### Classification Thresholds",
        f"- **ABC Quantity Thresholds**: Class A (Top {metadata['abc_a_threshold']:.0%}), Class B (Next {metadata['abc_b_threshold'] - metadata['abc_a_threshold']:.0%}), Class C (Bottom {1 - metadata['abc_b_threshold']:.0%})" if metadata is not None else "- **ABC Quantity Thresholds**: Class A (Top 80%), Class B (Next 15%), Class C (Bottom 5%)",
        f"- **XYZ Variability Thresholds**: Class X (CV $\\le$ {metadata['xyz_cv_x_max']:.2f}), Class Y (CV $\\le$ {metadata['xyz_cv_y_max']:.2f}), Class Z (CV > {metadata['xyz_cv_y_max']:.2f} or Low Sample)" if metadata is not None else "- **XYZ Variability Thresholds**: Class X (CV $\\le$ 0.50), Class Y (CV $\\le$ 1.00), Class Z (CV > 1.00)",
        f"- **Low-Sample Filter**: SKUs with fewer than {int(metadata['xyz_min_nonzero_weeks'])} nonzero sales weeks are automatically downgraded to Class Z to prevent statistical skew." if metadata is not None else "- **Low-Sample Filter**: Downgraded to Class Z if active weeks < 4",
        "",
        "### Joint ABC-XYZ Matrix Summary",
        f"A total of **{total_skus} unique SKUs** were classified. The product distribution across the ABC-XYZ matrix is shown in the summary table below:",
        "",
        f"| XYZ \\ ABC | Class A (Top 80% Vol, {class_a_skus} SKUs) | Class B (Next 15% Vol, {class_b_skus} SKUs) | Class C (Bottom 5% Vol, {class_c_skus} SKUs) |",
        "| :--- | :---: | :---: | :---: |",
        f"| **Class X** (Stable demand) | {get_cell_text('A', 'X')} | {get_cell_text('B', 'X')} | {get_cell_text('C', 'X')} |",
        f"| **Class Y** (Variable demand) | {get_cell_text('A', 'Y')} | {get_cell_text('B', 'Y')} | {get_cell_text('C', 'Y')} |",
        f"| **Class Z** (Irregular/Spiky) | {get_cell_text('A', 'Z')} | {get_cell_text('B', 'Z')} | {get_cell_text('C', 'Z')} |",
        "",
        "### Identification of the 'Fast-Moving' SKU Group",
        "The **Fast-Moving** SKU group is defined as the intersection of Class A by Quantity and Class A by Order Frequency (Class A-A). This group is the primary driver of warehouse operational workload and inventory velocity.",
        "",
        f"- **SKU Count**: **{fast_mov['sku_count']} SKUs** (representing **{fast_mov_sku_share:.2%}** of the total assortment).",
        f"- **Volume Contribution**: Accounts for **{fast_mov['quantity']:.2f} units** (**{fast_mov['quantity_share']:.2%}** of total outbound volume).",
        f"- **Fulfillment Workload**: Drives **{fast_mov['order_frequency']} orders** (**{fast_mov['frequency_share']:.2%}** of all outbound transaction lines).",
        f"- **Top 10 Fast-Moving SKUs**: `{fast_mov['top_skus']}`.",
        "",
        "> [!TIP]",
        "> **Operational Recommendation**: Because only ~10% of the SKUs drive nearly 2/3 of all shipped quantities, these 59 SKUs should be assigned to the most ergonomic pick-faces (lower levels, close to the packing stations) with dedicated replenishment pathways to minimize picking travel time.",
        "",
        "---",
        "",
        "## Q1.2 Distribution Heatmap and Warehouse Imbalance Analysis",
        "",
        "### 1. Data Quality and Resolution Ceiling",
        "A critical finding from our data cleansing pipeline is a **severe geography resolution ceiling**:",
        f"- **Row-level coverage**: Only **{geo_cov['shipment_row_coverage']:.2%}** of transaction rows (16,104 out of 43,894) could be mapped to a known customer location.",
        f"- **Quantity-level coverage**: Only **{geo_cov['quantity_coverage']:.2%}** of outbound quantities (159,635.70 out of 355,364.80) are linked to known coordinates.",
        f"- **Root Cause**: `{geo_cov['shipment_rows_unknown_geography']:,}` assignment-window rows are unresolved, of which **{geo_cov['rows_unresolved_customer']:,} rows** are due to `Ship-to Customer` being logged as `'unknown'` in the database.",
        "",
        "> [!IMPORTANT]",
        "> **Central Invoicing Data Bias**: This missing customer data is systemic:",
        "> - **Centralization (Pre-Dec 2025)**: Customer billing was centralized under My Phuoc's ERP account. Consequently, Vinh Loc shipments (representing Tefal products) were logged as internal stock depletion entries without customer details, affecting **80.10%** of Vinh Loc rows.",
        "> - **Migration (Dec 2025)**: Billing migrated to Vinh Loc, causing My Phuoc's December transactions to lack customer details.",
        "> - **Operational Impact**: Vinh Loc is left with an extremely low geographic coverage of **12.12% of its volume**, skewing all raw geographic charts to make Vinh Loc look artificially inactive. This systematic bias and the resulting spatial coverage limits are visualized in Figure \\ref{fig:q12-geo-coverage}.",
        "",
        "![Q1.2 Geography coverage map\\label{fig:q12-geo-coverage}](../charts/q12_geography_coverage_map.png)",
        "",
        "### 2. Corrected Warehouse Imbalance (Approach A: Statistical Scaling)",
        "To provide a safe and unbiased view of warehouse throughput, we compare raw volume totals against resolved volumes and apply **Approach A (Statistical Scaling)**:",
        "",
        "| Metric | My Phuoc Warehouse | Vinh Loc Warehouse | Total |",
        "| :------------------------------------------- | :-----------------: | :-----------------: | :-----------------: |",
        "| **Raw Outbound Quantity** | 253,197.00 (71.25%) | 102,167.80 (28.75%) | 355,364.80 (100.0%) |",
        "| **Raw Outbound CBM** | 13,948.74 (70.97%) | 5,705.04 (29.03%) | 19,653.78 (100.0%) |",
        "| **Raw Transaction Rows** | 17,423 (39.70%) | 26,471 (60.30%) | 43,894 (100.0%) |",
        "| **Resolved Quantity (Raw)** | 147,258.80 (92.25%) | 12,382.80 (7.75%) | 159,635.70 (100.0%) |",
        "| **Imputed Quantity (Approach A)** | **253,196.01 (71.25%)** | **102,168.32 (28.75%)** | **355,364.33 (100.0%)** |",
        "",
        "**Conclusion**: While Vinh Loc represents 60.30% of transaction rows (small, frequent orders of Tefal items), it accounts for 28.75% of outbound quantity. My Phuoc handles 71.25% of the quantity. The raw resolved geography is heavily biased (92% vs 8%), but the true operational split is **71% My Phuoc vs 29% Vinh Loc**. The comparison of raw, resolved, and imputed throughput is detailed in the table above, while the regional warehouse dominance gap in the resolved transactions is shown in Figure \\ref{fig:q12-wh-imbalance}.",
        "",
        "![Q1.2 Warehouse imbalance\\label{fig:q12-wh-imbalance}](../charts/q12_warehouse_imbalance.png)",
        "",
        "### 3. Regional Demand and Top Clusters",
        "To define the geographic boundaries of our analysis, the standard Vietnam administrative regions are mapped in Figure \\ref{fig:q12-vn-regions}.",
        "",
        "![Q1.2 Vietnam regioning map\\label{fig:q12-vn-regions}](../charts/q12_region_reference_map.png){width=50%}",
        "",
        "Within these boundaries, the resolved outbound demand is highly concentrated. As shown in Figure \\ref{fig:q12-region-qty}, the region-level order and quantity shares are led by the following regions:",
        "- **Đông Nam Bộ**: The largest demand region, accounting for **42.78%** of resolved volume (68,289.44 units).",
        "- **Bắc Trung Bộ và Duyên hải miền Trung**: The second largest, representing **28.22%** (45,044.48 units).",
        "- **Đồng bằng sông Cửu Long**: Accounts for **13.86%** (22,132.83 units).",
        "",
        "![Q1.2 Regional quantity\\label{fig:q12-region-qty}](../charts/q12_region_quantity_orders.png)",
        "",
        "#### Top Customer Clusters (Provinces)",
        "At the provincial level, demand clusters heavily around key urban centers. The absolute volume hotspots are highlighted in the top demand provinces map (see Figure \\ref{fig:q12-top-provinces}).",
        "",
        "![Q1.2 Top demand provinces map\\label{fig:q12-top-provinces}](../charts/q12_top_demand_provinces_map.png){width=50%}",
        "",
        "Specifically, the top five provinces by resolved volume and order counts are led by Hồ Chí Minh City by an overwhelming margin:",
        "- **Hồ Chí Minh**: 1,267 orders, 42,256.09 quantity (representing **34.62% of resolved orders** and **26.47% of resolved quantity**).",
        "- **Đồng Nai**: 387 orders, 5,579.33 quantity.",
        "- **Bình Dương**: 194 orders, 19,814.17 quantity (high volume per order).",
        "- **Đà Nẵng**: 204 orders, 15,522.98 quantity (Central hub).",
        "- **Cần Thơ**: 177 orders, 10,561.08 quantity (Mekong Delta hub).",
        "",
        "To visualize the full provincial distribution across the nation, Figure \\ref{fig:q12-province-demand} displays the provincial demand choropleth maps (by total quantity and total orders).",
        "",
        "![Q1.2 Province demand maps\\label{fig:q12-province-demand}](../charts/q12_province_demand_choropleths.png)",
        "",
        "### 4. Fulfillment Splits and Spatial Dynamics",
        "To understand how fulfillment is shared between the facilities, we examine the warehouse-region throughput split.",
        "",
        "#### Warehouse-Region Fulfillment Splits",
        "Because My Phuoc holds Fans and Vinh Loc holds Tefal, both warehouses ship to the same regions to fulfill their respective product lines. This regional throughput distribution is visualized in Figure \\ref{fig:q12-wh-region-split}.",
        "",
        "![Q1.2 Warehouse-region split\\label{fig:q12-wh-region-split}](../charts/q12_warehouse_region_quantity_split.png)",
        "",
        "However, due to the centralized billing bias, My Phuoc appears dominant in almost all regions. This dominance pattern and the resulting spatial market coverage of both warehouses are mapped in Figure \\ref{fig:q12-wh-dominance}.",
        "",
        "![Q1.2 Warehouse dominance map\\label{fig:q12-wh-dominance}](../charts/q12_warehouse_dominance_map.png){width=50%}",
        "",
        "#### Distance vs. Demand Size Correlation",
        "We also analyze the relationship between delivery distance and order characteristics. There is a clear spatial correlation between order size (CBM) and delivery distance, showing that close-by urban centers (HCMC and surrounding areas) order in higher density and frequency, as illustrated in the scatter plot in Figure \\ref{fig:q12-dist-correlation}.",
        "",
        "![Q1.2 Province distance correlation\\label{fig:q12-dist-correlation}](../charts/q12_province_distance_correlation.png)",
        "",
        "#### Urban vs. Provincial Demand Split",
        "Finally, we segment the outbound volume into urban centers (HCMC, Hanoi, Da Nang, Can Tho, Haiphong) versus the remaining provinces. As shown in Figure \\ref{fig:q12-urban-provincial}, urban centers drive a disproportionately large and concentrated volume compared to the more fragmented provincial demand.",
        "",
        "![Q1.2 Urban and provincial split\\label{fig:q12-urban-provincial}](../charts/q12_urban_provincial_split.png){width=70%}",
        "",
        "---",
        "",
        "## Q1.3 Customer Segment Order Profile Comparison",
        "",
        "We compared the order profiles of **Modern Trade (MT)** (large retail accounts like Co.op Mart, Lotte, etc.) and **Traditional Trade / Distributor (TT)**.",
        "",
        "### Key Profile Comparison Table",
        "The comparison across the required dimensions is summarized below:",
        "",
        "| Dimension | Modern Trade (MT) | Traditional Trade / Distributor (TT) |",
        "| :--- | :---: | :---: |",
        f"| **Active Customers** | {mt_prof['customers']} | {tt_prof['customers']} |",
        f"| **Order Count** | {mt_prof['orders']} | {tt_prof['orders']} |",
        f"| **Avg. Order Quantity** | {mt_prof['avg_order_quantity']:.2f} units | {tt_prof['avg_order_quantity']:.2f} units |",
        f"| **Avg. Order Volume (CBM)** | {mt_prof['avg_order_cbm']:.2f} m³ | {tt_prof['avg_order_cbm']:.2f} m³ |",
        f"| **Avg. SKU Breadth / Order** | {mt_prof['avg_sku_breadth']:.2f} SKUs | {tt_prof['avg_sku_breadth']:.2f} SKUs |",
        f"| **Order Frequency (per customer/month)** | {mt_prof['avg_orders_per_customer_month']:.2f} | {tt_prof['avg_orders_per_customer_month']:.2f} |",
        f"| **Geographic Footprint** | {mt_prof['province_count']} provinces / {mt_prof['region_count']} regions | {tt_prof['province_count']} provinces / {tt_prof['region_count']} regions |",
        f"| **Avg. Delivery Distance** | {mt_prof['avg_distance_km']:.2f} km | {tt_prof['avg_distance_km']:.2f} km |",
        f"| **Pallet Share (%)** | **{mt_pkg_shares.get('pallet', 0.0):.2%}** | **{tt_pkg_shares.get('pallet', 0.0):.2%}** |",
        f"| **Carton Share (%)** | **{mt_pkg_shares.get('carton', 0.0):.2%}** | **{tt_pkg_shares.get('carton', 0.0):.2%}** |",
        f"| **Loose Share (%)** | **{mt_pkg_shares.get('loose', 0.0):.2%}** | **{tt_pkg_shares.get('loose', 0.0):.2%}** |",
        "",
        "### Key Profile Insights",
        f"1. **Order Size & Consolidation**: Modern Trade orders are highly consolidated and large, averaging **{mt_prof['avg_order_quantity']:.2f} units** and **{mt_prof['avg_order_cbm']:.2f} CBM** per order. Traditional Trade orders are much smaller and fragmented, averaging **{tt_prof['avg_order_quantity']:.2f} units** and **{tt_prof['avg_order_cbm']:.2f} CBM**. This comparison of order metrics is visualised in Figure \\ref{{fig:q13-order-profile}}.",
        "",
        "![Q1.3 Order profile comparison\\label{fig:q13-order-profile}](../charts/q13_order_profile_comparison.png){width=85%}",
        "",
        f"2. **Assortment Breadth vs. Depth**: As shown in Figure \\ref{{fig:q13-order-profile}}, Traditional Trade orders have a higher average SKU breadth (**{tt_prof['avg_sku_breadth']:.2f} SKUs** per order) than Modern Trade (**{mt_prof['avg_sku_breadth']:.2f} SKUs**). This indicates that TT customers order small quantities of a wide variety of SKUs, increasing warehouse sorting complexity.",
        "",
        f"3. **Packaging Unit Mix**: Modern Trade is highly pallet-centric, with **{mt_pkg_shares.get('pallet', 0.0):.2%}** of their items shipped as full pallets. Traditional Trade is highly carton-centric (**{tt_pkg_shares.get('carton', 0.0):.2%}** of items) and has more loose picking (**{tt_pkg_shares.get('loose', 0.0):.2%}** vs. {mt_pkg_shares.get('loose', 0.0):.2%} for MT). This breakdown of packaging unit selections is compared in Figure \\ref{{fig:q13-pkg-mix}}.",
        "",
        "![Q1.3 Packaging mix\\label{fig:q13-pkg-mix}](../charts/q13_packaging_mix.png)",
        "",
        f"4. **Geographic Spread**: Traditional Trade has a much wider geographic spread, covering **{tt_prof['province_count']} provinces** compared to MT's **{mt_prof['province_count']} provinces**, representing a highly fragmented, nation-wide distribution profile. The count of active provinces and regions for each segment is shown in Figure \\ref{{fig:q13-geo-spread}}.",
        "",
        "![Q1.3 Geographic spread\\label{fig:q13-geo-spread}](../charts/q13_geographic_spread.png)",
        "",
        f"To see the spatial distribution of these sales, Figure \\ref{{fig:q13-segment-geo-maps}} shows the choropleth maps of MT and TT customer demand across Vietnam.",
        "",
        "![Q1.3 Segment geography maps\\label{fig:q13-segment-geo-maps}](../charts/q13_segment_geographic_maps.png)",
    ]
    (NOTES_DIR / NOTE_FILENAME).write_text("\n".join(text) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    
    from src.logage2026.config import CLEANED_DIR, TABLES_DIR
    
    print("Loading static cleaned data from disk...")
    try:
        shipments = pd.read_csv(CLEANED_DIR / "shipments_cleaned.csv")
        abc_xyz = pd.read_csv(TABLES_DIR / "q11_sku_abc_xyz.csv")
        abc_xyz_matrix = pd.read_csv(TABLES_DIR / "q11_abc_xyz_matrix_summary.csv")
        fast_moving_summary = pd.read_csv(TABLES_DIR / "q11_fast_moving_summary.csv")
        classification_metadata = pd.read_csv(TABLES_DIR / "q11_classification_metadata.csv")
        missing_data_summary = pd.read_csv(TABLES_DIR / "shared_missing_data_summary.csv")
        geography_coverage_summary = pd.read_csv(TABLES_DIR / "q12_geography_coverage_summary.csv")
        warehouse_region_summary = pd.read_csv(TABLES_DIR / "q12_warehouse_region_summary.csv")
        customer_cluster_summary = pd.read_csv(TABLES_DIR / "q12_customer_cluster_summary.csv")
        warehouse_imbalance_summary = pd.read_csv(TABLES_DIR / "q12_warehouse_imbalance_summary.csv")
        q12_region_orders_quantity_summary = pd.read_csv(TABLES_DIR / "q12_region_quantity_orders_summary.csv")
        q12_province_cluster_summary = pd.read_csv(TABLES_DIR / "q12_top_demand_provinces_summary.csv")
        q12_province_demand_summary = pd.read_csv(TABLES_DIR / "q12_province_demand_summary.csv")
        q12_province_warehouse_dominance_summary = pd.read_csv(TABLES_DIR / "q12_province_warehouse_dominance_summary.csv")
        q12_urban_provincial_summary = pd.read_csv(TABLES_DIR / "q12_urban_provincial_summary.csv")
        q12_warehouse_imbalance_visual_summary = pd.read_csv(TABLES_DIR / "q12_warehouse_imbalance_visual_summary.csv")
        q13_segment_profile_summary = pd.read_csv(TABLES_DIR / "q13_segment_profile_summary.csv")
        q13_segment_packaging_summary = pd.read_csv(TABLES_DIR / "q13_segment_packaging_summary.csv")
        q13_segment_geographic_spread_summary = pd.read_csv(TABLES_DIR / "q13_segment_geographic_spread_summary.csv")
        
        # Convert dates
        shipments["created_date"] = pd.to_datetime(shipments["created_date"])
        
        print("Generating report text from static output...")
        write_notes(
            shipments, abc_xyz, abc_xyz_matrix, fast_moving_summary,
            classification_metadata, missing_data_summary, geography_coverage_summary,
            warehouse_region_summary, customer_cluster_summary, warehouse_imbalance_summary,
            q12_region_orders_quantity_summary, q12_province_cluster_summary,
            q12_province_demand_summary, q12_province_warehouse_dominance_summary,
            q12_urban_provincial_summary,
            q12_warehouse_imbalance_visual_summary,
            q13_segment_profile_summary, q13_segment_packaging_summary,
            q13_segment_geographic_spread_summary
        )
        print(f"Report written successfully to outputs/round2/notes/{NOTE_FILENAME}!")
    except Exception as e:
        print(f"Error loading static output: {e}")
        print("Please run run_analysis.py first to generate the outputs.")
