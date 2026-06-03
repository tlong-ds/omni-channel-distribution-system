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
    text = [
        "# Round 2 Question Summary",
        "",
        "## Data basis",
        "",
        f"- ABC thresholds: A≤{metadata['abc_a_threshold']:.2f}, B≤{metadata['abc_b_threshold']:.2f}"
        if metadata is not None
        else "- ABC thresholds: unavailable",
        f"- XYZ CV thresholds: X≤{metadata['xyz_cv_x_max']:.2f}, Y≤{metadata['xyz_cv_y_max']:.2f}"
        if metadata is not None
        else "- XYZ CV thresholds: unavailable",
        f"- Low-sample XYZ rule: min nonzero weeks = {int(metadata['xyz_min_nonzero_weeks'])}"
        if metadata is not None
        else "- Low-sample XYZ rule: unavailable",
        f"- Missing shipment rows excluded: {int(missing_row['rows_missing_either'])} "
        f"({missing_row['missing_row_share']:.2%} of rows)"
        if missing_row is not None
        else "- Missing shipment rows excluded: unavailable",
        "",
        "## Q1.1 Demand pattern classification",
        "![Q1.1 ABC quantity distribution](../charts/q11_abc_quantity_distribution.png)",
        "",
        "![Q1.1 ABC-XYZ matrix](../charts/q11_abc_xyz_matrix.png)",
        "",
        "## Q1.2 Demand geography with ambiguity-safe matching",
        "![Q1.2 Vietnam regioning map](../charts/q12_region_reference_map.png)",
        "",
        "![Q1.2 Regional quantity](../charts/q12_region_quantity_orders.png)",
        "",
        "![Q1.2 Warehouse-region split](../charts/q12_warehouse_region_quantity_split.png)",
        "",
        "![Q1.2 Top demand provinces map](../charts/q12_top_demand_provinces_map.png)",
        "",
        "![Q1.2 Province demand maps](../charts/q12_province_demand_choropleths.png)",
        "",
        "![Q1.2 Warehouse dominance map](../charts/q12_warehouse_dominance_map.png)",
        "",
        "![Q1.2 Geography coverage map](../charts/q12_geography_coverage_map.png)",
        "",
        "![Q1.2 Province distance correlation](../charts/q12_province_distance_correlation.png)",
        "",
        "![Q1.2 Urban and provincial split](../charts/q12_urban_provincial_split.png)",
        "",
        "![Q1.2 Warehouse imbalance](../charts/q12_warehouse_imbalance.png)",
        "",
        "## Q1.3 Order profile analysis",
        "![Q1.3 Order profile comparison](../charts/q13_order_profile_comparison.png)",
        "",
        "![Q1.3 Packaging mix](../charts/q13_packaging_mix.png)",
        "",
        "![Q1.3 Geographic spread](../charts/q13_geographic_spread.png)",
        "",
        "![Q1.3 Segment geography maps](../charts/q13_segment_geographic_maps.png)",
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
