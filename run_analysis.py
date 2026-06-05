from src.logage2026.analysis import (
    ASSIGNMENT_END,
    ASSIGNMENT_START,
    Q11_END,
    Q11_START,
    build_abc_xyz,
    build_abc_xyz_matrix_summary,
    build_abc_quantity_frequency_matrix,
    build_classification_metadata,
    build_customer_match_quality_summary,
    build_customer_cluster_summary,
    build_document_type_summary,
    build_fast_moving_summary,
    build_geography_diagnostics_summary,
    build_geography_coverage_summary,
    build_geography_source_summary,
    build_missing_data_summary,
    build_order_profile_segments,
    build_q11_monthly_demand_table,
    build_q12_province_cluster_summary,
    build_q12_province_correlation_input_summary,
    build_q12_province_demand_summary,
    build_q12_province_warehouse_dominance_summary,
    build_q12_region_orders_quantity_summary,
    build_q12_urban_provincial_summary,
    build_q12_warehouse_imbalance_visual_summary,
    build_q13_segment_geographic_spread_summary,
    build_q13_segment_packaging_summary,
    build_q13_segment_province_spread_summary,
    build_q13_segment_profile_summary,
    build_unresolved_candidate_region_summary,
    build_unresolved_customer_summary,
    build_warehouse_imbalance_summary,
    build_warehouse_region_summary,
    filter_assignment_shipments,
    filter_q11_shipments,
)
from src.logage2026.cleaning import clean_distributors, clean_shipments, clean_sku_master
from src.logage2026.config import CHARTS_DIR, CLEANED_DIR, NOTES_DIR, OUTPUT_DIR, Q11_WORKBOOK_OUTPUT, TABLES_DIR
from src.logage2026.loading import (
    load_distributors,
    load_segment_overrides,
    load_sku_master,
    load_transactions,
)
from src.logage2026.notes import write_notes
from src.logage2026.q11_excel import write_q11_workbook
from src.logage2026.visuals import boundary_province_names, save_charts


EXPECTED_ASSIGNMENT_ROWS = 43_894
EXPECTED_ASSIGNMENT_QUANTITY = 355_364.80
EXPECTED_ASSIGNMENT_CBM = 19_653.78
EXPECTED_Q11_ROWS = 45_172
EXPECTED_Q11_SKUS = 612
EXPECTED_Q11_ABC_COUNTS = {"A": 41, "B": 74, "C": 497}
EXPECTED_Q11_XYZ_COUNTS = {"X": 52, "Y": 180, "Z": 380}
NOTE_FILENAME = "part1_question_summary.tex"

STALE_OUTPUTS = [
    TABLES_DIR / "safety_stock_class_a.csv",
    TABLES_DIR / "slotting_plan.csv",
    NOTES_DIR / "recommendations.md",
    NOTES_DIR / "pick_pack_flowchart.md",
    NOTES_DIR / "question_summary.md",
    TABLES_DIR / "abc_xyz.csv",
    TABLES_DIR / "abc_xyz_matrix_summary.csv",
    TABLES_DIR / "fast_moving_summary.csv",
    TABLES_DIR / "classification_metadata.csv",
    TABLES_DIR / "missing_data_summary.csv",
    TABLES_DIR / "geography_coverage_summary.csv",
    TABLES_DIR / "geography_diagnostics_summary.csv",
    TABLES_DIR / "unresolved_candidate_region_summary.csv",
    TABLES_DIR / "warehouse_region_summary.csv",
    TABLES_DIR / "customer_cluster_summary.csv",
    TABLES_DIR / "warehouse_imbalance_summary.csv",
    TABLES_DIR / "q12_region_orders_quantity_summary.csv",
    TABLES_DIR / "q12_province_cluster_summary.csv",
    TABLES_DIR / "order_profile_segments.csv",
    TABLES_DIR / "document_type_summary.csv",
    TABLES_DIR / "customer_match_quality_summary.csv",
    TABLES_DIR / "geography_source_summary.csv",
    TABLES_DIR / "unresolved_customer_summary.csv",
    CHARTS_DIR / "abc_quantity_distribution.png",
    CHARTS_DIR / "abc_xyz_matrix.png",
    CHARTS_DIR / "regional_quantity_density.png",
    CHARTS_DIR / "warehouse_region_split.png",
    CHARTS_DIR / "q12_province_demand_maps.png",
    CHARTS_DIR / "order_profile_comparison.png",
    CHARTS_DIR / "vietnam_regions_map.png",
]


def main() -> None:
    for directory in [CLEANED_DIR, TABLES_DIR, NOTES_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    sku_master = clean_sku_master(load_sku_master())
    distributors = clean_distributors(load_distributors())
    segment_overrides = load_segment_overrides()
    shipments = clean_shipments(load_transactions(), distributors, segment_overrides=segment_overrides)
    valid_skus = set(sku_master["sap_code_2"].dropna())
    assignment_base_shipments = shipments[shipments["sku_code"].isin(valid_skus)].copy()
    q11_shipments = filter_q11_shipments(shipments)
    assignment_shipments = filter_assignment_shipments(assignment_base_shipments)

    abc_xyz = build_abc_xyz(q11_shipments, sku_master)
    abc_xyz_matrix = build_abc_xyz_matrix_summary(abc_xyz)
    abc_qty_freq_matrix = build_abc_quantity_frequency_matrix(abc_xyz)
    fast_moving_summary = build_fast_moving_summary(abc_xyz)
    classification_metadata = build_classification_metadata()
    q11_monthly_demand = build_q11_monthly_demand_table(abc_xyz, q11_shipments)
    missing_data_summary = build_missing_data_summary(shipments)
    geography_coverage_summary = build_geography_coverage_summary(assignment_shipments)
    geography_diagnostics_summary = build_geography_diagnostics_summary(assignment_shipments)
    unresolved_candidate_region_summary = build_unresolved_candidate_region_summary(assignment_shipments)
    warehouse_region_summary = build_warehouse_region_summary(assignment_shipments)
    customer_cluster_summary = build_customer_cluster_summary(assignment_shipments)
    warehouse_imbalance_summary = build_warehouse_imbalance_summary(assignment_shipments)
    q12_region_orders_quantity_summary = build_q12_region_orders_quantity_summary(assignment_shipments)
    q12_province_cluster_summary = build_q12_province_cluster_summary(assignment_shipments)
    q12_province_demand_summary = build_q12_province_demand_summary(assignment_shipments)
    q12_province_warehouse_dominance_summary = build_q12_province_warehouse_dominance_summary(assignment_shipments)
    q12_province_correlation_input_summary = build_q12_province_correlation_input_summary(assignment_shipments)
    q12_urban_provincial_summary = build_q12_urban_provincial_summary(assignment_shipments)
    q12_warehouse_imbalance_visual_summary = build_q12_warehouse_imbalance_visual_summary(assignment_shipments)
    q13_segment_profile_summary = build_q13_segment_profile_summary(assignment_shipments, sku_master)
    q13_segment_packaging_summary = build_q13_segment_packaging_summary(assignment_shipments, sku_master)
    q13_segment_geographic_spread_summary = build_q13_segment_geographic_spread_summary(assignment_shipments)
    q13_segment_province_spread_summary = build_q13_segment_province_spread_summary(assignment_shipments)
    order_profile_segments = build_order_profile_segments(assignment_shipments, sku_master)
    document_type_summary = build_document_type_summary(shipments)
    customer_match_quality_summary = build_customer_match_quality_summary(assignment_shipments)
    geography_source_summary = build_geography_source_summary(assignment_shipments)
    unresolved_customer_summary = build_unresolved_customer_summary(assignment_shipments)

    sku_master.to_csv(CLEANED_DIR / "sku_master_cleaned.csv", index=False)
    distributors.to_csv(CLEANED_DIR / "distributors_cleaned.csv", index=False)
    shipments.to_csv(CLEANED_DIR / "shipments_cleaned.csv", index=False)

    abc_xyz.to_csv(TABLES_DIR / "q11_sku_abc_xyz.csv", index=False)
    abc_xyz_matrix.to_csv(TABLES_DIR / "q11_abc_xyz_matrix_summary.csv", index=False)
    abc_qty_freq_matrix.to_csv(TABLES_DIR / "q11_abc_quantity_frequency_matrix.csv", index=False)
    fast_moving_summary.to_csv(TABLES_DIR / "q11_fast_moving_summary.csv", index=False)
    classification_metadata.to_csv(TABLES_DIR / "q11_classification_metadata.csv", index=False)
    q11_monthly_demand.to_csv(TABLES_DIR / "q11_monthly_demand_summary.csv", index=False)
    missing_data_summary.to_csv(TABLES_DIR / "shared_missing_data_summary.csv", index=False)
    geography_coverage_summary.to_csv(TABLES_DIR / "q12_geography_coverage_summary.csv", index=False)
    geography_diagnostics_summary.to_csv(TABLES_DIR / "q12_geography_diagnostics_summary.csv", index=False)
    unresolved_candidate_region_summary.to_csv(TABLES_DIR / "q12_unresolved_candidate_region_summary.csv", index=False)
    warehouse_region_summary.to_csv(TABLES_DIR / "q12_warehouse_region_summary.csv", index=False)
    customer_cluster_summary.to_csv(TABLES_DIR / "q12_customer_cluster_summary.csv", index=False)
    warehouse_imbalance_summary.to_csv(TABLES_DIR / "q12_warehouse_imbalance_summary.csv", index=False)
    q12_region_orders_quantity_summary.to_csv(TABLES_DIR / "q12_region_quantity_orders_summary.csv", index=False)
    q12_province_cluster_summary.to_csv(TABLES_DIR / "q12_top_demand_provinces_summary.csv", index=False)
    q12_province_demand_summary.to_csv(TABLES_DIR / "q12_province_demand_summary.csv", index=False)
    q12_province_warehouse_dominance_summary.to_csv(
        TABLES_DIR / "q12_province_warehouse_dominance_summary.csv", index=False
    )
    q12_province_correlation_input_summary.to_csv(
        TABLES_DIR / "q12_province_correlation_input_summary.csv", index=False
    )
    q12_urban_provincial_summary.to_csv(TABLES_DIR / "q12_urban_provincial_summary.csv", index=False)
    q12_warehouse_imbalance_visual_summary.to_csv(TABLES_DIR / "q12_warehouse_imbalance_visual_summary.csv", index=False)
    q13_segment_profile_summary.to_csv(TABLES_DIR / "q13_segment_profile_summary.csv", index=False)
    q13_segment_packaging_summary.to_csv(TABLES_DIR / "q13_segment_packaging_summary.csv", index=False)
    q13_segment_geographic_spread_summary.to_csv(TABLES_DIR / "q13_segment_geographic_spread_summary.csv", index=False)
    q13_segment_province_spread_summary.to_csv(TABLES_DIR / "q13_segment_province_spread_summary.csv", index=False)
    order_profile_segments.to_csv(TABLES_DIR / "q13_order_profile_segments.csv", index=False)
    document_type_summary.to_csv(TABLES_DIR / "shared_document_type_summary.csv", index=False)
    customer_match_quality_summary.to_csv(TABLES_DIR / "q12_customer_match_quality_summary.csv", index=False)
    geography_source_summary.to_csv(TABLES_DIR / "q12_geography_source_summary.csv", index=False)
    unresolved_customer_summary.to_csv(TABLES_DIR / "q12_unresolved_customer_summary.csv", index=False)
    write_q11_workbook(abc_xyz, abc_xyz_matrix, q11_monthly_demand, q11_shipments)

    _remove_stale_outputs()
    save_charts(
        assignment_shipments,
        abc_xyz,
        abc_xyz_matrix,
        warehouse_region_summary,
        q12_region_orders_quantity_summary,
        q12_province_cluster_summary,
        q12_province_demand_summary,
        q12_province_warehouse_dominance_summary,
        q12_province_correlation_input_summary,
        q12_urban_provincial_summary,
        q12_warehouse_imbalance_visual_summary,
        q13_segment_profile_summary,
        q13_segment_packaging_summary,
        q13_segment_geographic_spread_summary,
        q13_segment_province_spread_summary,
        sku_master,
        abc_qty_freq_matrix,
    )
    write_notes(
        assignment_shipments,
        abc_xyz,
        abc_xyz_matrix,
        fast_moving_summary,
        classification_metadata,
        missing_data_summary,
        geography_coverage_summary,
        warehouse_region_summary,
        customer_cluster_summary,
        warehouse_imbalance_summary,
        q12_region_orders_quantity_summary,
        q12_province_cluster_summary,
        q12_province_demand_summary,
        q12_province_warehouse_dominance_summary,
        q12_urban_provincial_summary,
        q12_warehouse_imbalance_visual_summary,
        q13_segment_profile_summary,
        q13_segment_packaging_summary,
        q13_segment_geographic_spread_summary,
        abc_qty_freq_matrix,
    )
    print(f"Round 2 analysis written to {OUTPUT_DIR}")
    print(
        "Q1.1 workbook window: "
        f"{Q11_START.date().isoformat()} to {Q11_END.date().isoformat()} "
        f"| rows: {len(q11_shipments):,} "
        f"| classified SKUs: {abc_xyz['sku_code'].nunique():,}"
    )
    print(
        "Assignment window: "
        f"{ASSIGNMENT_START.date().isoformat()} to {ASSIGNMENT_END.date().isoformat()} "
        f"| rows: {len(assignment_shipments):,} "
        f"| quantity: {assignment_shipments['quantity'].sum():,.2f} "
        f"| CBM: {assignment_shipments['cbm_total'].sum():,.2f}"
    )
    print(f"Classified SKUs: {abc_xyz['sku_code'].nunique():,}")


def _remove_stale_outputs() -> None:
    for path in STALE_OUTPUTS:
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    main()
