from src.logage2026.analysis import (
    ASSIGNMENT_END,
    ASSIGNMENT_START,
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
)
from src.logage2026.cleaning import clean_distributors, clean_shipments, clean_sku_master
from src.logage2026.config import CHARTS_DIR, CLEANED_DIR, NOTES_DIR, OUTPUT_DIR, TABLES_DIR
from src.logage2026.loading import (
    load_distributors,
    load_segment_overrides,
    load_sku_master,
    load_transactions,
)
from src.logage2026.notes import write_notes
from src.logage2026.visuals import boundary_province_names, save_charts


EXPECTED_ASSIGNMENT_ROWS = 43_894
EXPECTED_ASSIGNMENT_QUANTITY = 355_364.80
EXPECTED_ASSIGNMENT_CBM = 19_653.78
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
    
    # Filter out unverified SKUs that are not present in the SKU Master
    valid_skus = set(sku_master["sap_code_2"].dropna())
    shipments = shipments[shipments["sku_code"].isin(valid_skus)].copy()

    assignment_shipments = filter_assignment_shipments(shipments)

    abc_xyz = build_abc_xyz(assignment_shipments, sku_master)
    abc_xyz_matrix = build_abc_xyz_matrix_summary(abc_xyz)
    abc_qty_freq_matrix = build_abc_quantity_frequency_matrix(abc_xyz)
    fast_moving_summary = build_fast_moving_summary(abc_xyz)
    classification_metadata = build_classification_metadata()
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
    verify_outputs(
        shipments,
        assignment_shipments,
        abc_xyz,
        abc_xyz_matrix,
        classification_metadata,
        missing_data_summary,
        geography_coverage_summary,
        geography_diagnostics_summary,
        unresolved_candidate_region_summary,
        warehouse_region_summary,
        customer_cluster_summary,
        warehouse_imbalance_summary,
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
        document_type_summary,
        customer_match_quality_summary,
        geography_source_summary,
        unresolved_customer_summary,
    )
    print(f"Round 2 analysis written to {OUTPUT_DIR}")
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


def verify_outputs(
    shipments,
    assignment_shipments,
    abc_xyz,
    abc_xyz_matrix,
    classification_metadata,
    missing_data_summary,
    geography_coverage_summary,
    geography_diagnostics_summary,
    unresolved_candidate_region_summary,
    warehouse_region_summary,
    customer_cluster_summary,
    warehouse_imbalance_summary,
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
    document_type_summary,
    customer_match_quality_summary,
    geography_source_summary,
    unresolved_customer_summary,
) -> None:
    if len(assignment_shipments) != EXPECTED_ASSIGNMENT_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_ASSIGNMENT_ROWS:,} assignment shipment rows, found {len(assignment_shipments):,}"
        )
    if abs(assignment_shipments["quantity"].sum() - EXPECTED_ASSIGNMENT_QUANTITY) > 0.05:
        raise ValueError("Assignment-window shipment quantity total was not preserved")
    if abs(assignment_shipments["cbm_total"].sum() - EXPECTED_ASSIGNMENT_CBM) > 0.05:
        raise ValueError("Assignment-window shipment CBM total was not preserved")
    if assignment_shipments["created_date"].min() < ASSIGNMENT_START or assignment_shipments["created_date"].max() > ASSIGNMENT_END:
        raise ValueError("Assignment-window filter leaked rows outside 2025-07-01 to 2025-12-31")
    if not assignment_shipments["analysis_document_flag"].all():
        raise ValueError("Excluded document types leaked into assignment demand shipments")
    if "data_error_flag" in assignment_shipments.columns and assignment_shipments["data_error_flag"].any():
        raise ValueError("Assignment-window shipments contain rows flagged as data errors")

    observed_skus = set(assignment_shipments["sku_code"].dropna().astype(str))
    classified_skus = set(abc_xyz["sku_code"].dropna().astype(str))
    missing = observed_skus - classified_skus
    if missing:
        raise ValueError(f"{len(missing):,} observed SKUs missing ABC/XYZ classes")
    if abc_xyz_matrix["sku_count"].sum() != abc_xyz["sku_code"].nunique():
        raise ValueError("ABC-XYZ matrix summary does not reconcile to classified SKU count")

    known = assignment_shipments[assignment_shipments["known_geography_flag"]].copy()
    coverage = geography_coverage_summary.iloc[0]
    if int(coverage["shipment_rows_known_geography"]) != len(known):
        raise ValueError("Geography row coverage does not reconcile to known-geography shipments")
    if abs(float(coverage["quantity_known_geography"]) - known["quantity"].sum()) > 0.05:
        raise ValueError("Geography quantity coverage does not reconcile to known-geography shipments")
    if abs(warehouse_region_summary["quantity"].sum() - known["quantity"].sum()) > 0.05:
        raise ValueError("Warehouse region summary does not reconcile to known-geography quantity")
    if abs(q12_region_orders_quantity_summary["quantity"].sum() - known["quantity"].sum()) > 0.05:
        raise ValueError("Q1.2 region summary does not reconcile to known-geography quantity")
    if abs(q12_province_demand_summary["quantity"].sum() - known["quantity"].sum()) > 0.05:
        raise ValueError("Q1.2 province demand summary does not reconcile to known-geography quantity")
    if abs(q12_province_warehouse_dominance_summary["quantity"].sum() - known["quantity"].sum()) > 0.05:
        raise ValueError("Q1.2 province warehouse dominance summary does not reconcile to known-geography quantity")
    boundary_names = boundary_province_names()
    if not q12_province_demand_summary["province"].isin(boundary_names).all():
        raise ValueError("Q1.2 province demand summary contains province names missing from the boundary layer")
    if not q12_province_warehouse_dominance_summary["province"].isin(boundary_names).all():
        raise ValueError("Q1.2 warehouse dominance summary contains province names missing from the boundary layer")
    if not q12_province_correlation_input_summary["province"].isin(boundary_names).all():
        raise ValueError("Q1.2 province correlation input summary contains province names missing from the boundary layer")
    if not q12_province_cluster_summary["my_phuoc_quantity_share"].between(0, 1).all():
        raise ValueError("Q1.2 province cluster summary has invalid My Phuoc quantity shares")
    if not q12_province_cluster_summary["vinh_loc_quantity_share"].between(0, 1).all():
        raise ValueError("Q1.2 province cluster summary has invalid Vinh Loc quantity shares")
    if abs(q12_urban_provincial_summary["quantity"].sum() - known["quantity"].sum()) > 0.05:
        raise ValueError("Q1.2 urban/provincial summary does not reconcile to known-geography quantity")
    if abs(q12_warehouse_imbalance_visual_summary["region_quantity"].sum() - known["quantity"].sum()) > 0.05:
        raise ValueError("Q1.2 warehouse imbalance visual summary does not reconcile to known-geography quantity")
    if warehouse_imbalance_summary["orders"].sum() < known["order_id"].nunique():
        raise ValueError("Warehouse imbalance summary unexpectedly undercounts known-geography orders")
    segment_known = assignment_shipments[
        assignment_shipments["customer_segment"].isin(["Modern Trade", "Traditional Trade / Distributor"])
    ].copy()
    if int(q13_segment_profile_summary["orders"].sum()) != segment_known.groupby(["customer_segment", "order_id"]).ngroups:
        raise ValueError("Q1.3 segment profile summary does not reconcile to assignment-window segment orders")
    packaging_share = q13_segment_packaging_summary.groupby("customer_segment")["quantity_share"].sum()
    if not packaging_share.round(6).eq(1.0).all():
        raise ValueError("Q1.3 packaging mix shares do not sum to 1 by segment")
    if int(q13_segment_geographic_spread_summary["province_count"].min()) <= 0:
        raise ValueError("Q1.3 geographic spread summary should contain positive province coverage")
    if q13_segment_province_spread_summary["customer_segment"].isin(["Unknown"]).any():
        raise ValueError("Q1.3 province spread summary should exclude Unknown customer segment")
    if abs(q13_segment_province_spread_summary["quantity"].sum() - segment_known.loc[segment_known["known_geography_flag"], "quantity"].sum()) > 0.05:
        raise ValueError("Q1.3 province spread summary does not reconcile to known-geography segment quantity")
    if not q13_segment_province_spread_summary["province"].isin(boundary_names).all():
        raise ValueError("Q1.3 province spread summary contains province names missing from the boundary layer")
    if assignment_shipments.loc[
        assignment_shipments["customer_match_status"].eq("ambiguous_multi_location_customer"), "geography_source"
    ].eq("distributor_match").any():
        raise ValueError("Ambiguous distributor keys were assigned geography via distributor matching")
    if int(document_type_summary["shipment_rows"].sum()) != len(shipments):
        raise ValueError("Document type diagnostics do not reconcile to full cleaned shipment rows")
    if int(customer_match_quality_summary["shipment_rows"].sum()) != len(assignment_shipments):
        raise ValueError("Customer match quality diagnostics do not reconcile to assignment demand rows")
    if int(geography_source_summary["shipment_rows"].sum()) != len(assignment_shipments):
        raise ValueError("Geography source diagnostics do not reconcile to assignment demand rows")
    if not unresolved_customer_summary.empty:
        unresolved_statuses = {
            "ambiguous_multi_location_customer",
            "unmatched_customer_key",
            "missing_customer_name",
        }
        if not set(unresolved_customer_summary["customer_match_status"]).issubset(unresolved_statuses):
            raise ValueError("Unresolved customer diagnostics contain resolved customer statuses")

    required_outputs = [
        CLEANED_DIR / "sku_master_cleaned.csv",
        CLEANED_DIR / "distributors_cleaned.csv",
        CLEANED_DIR / "shipments_cleaned.csv",
        TABLES_DIR / "q11_sku_abc_xyz.csv",
        TABLES_DIR / "q11_abc_xyz_matrix_summary.csv",
        TABLES_DIR / "q11_abc_quantity_frequency_matrix.csv",
        TABLES_DIR / "q11_fast_moving_summary.csv",
        TABLES_DIR / "q11_classification_metadata.csv",
        TABLES_DIR / "shared_missing_data_summary.csv",
        TABLES_DIR / "q12_geography_coverage_summary.csv",
        TABLES_DIR / "q12_geography_diagnostics_summary.csv",
        TABLES_DIR / "q12_unresolved_candidate_region_summary.csv",
        TABLES_DIR / "q12_warehouse_region_summary.csv",
        TABLES_DIR / "q12_customer_cluster_summary.csv",
        TABLES_DIR / "q12_warehouse_imbalance_summary.csv",
        TABLES_DIR / "q12_region_quantity_orders_summary.csv",
        TABLES_DIR / "q12_top_demand_provinces_summary.csv",
        TABLES_DIR / "q12_province_demand_summary.csv",
        TABLES_DIR / "q12_province_warehouse_dominance_summary.csv",
        TABLES_DIR / "q12_province_correlation_input_summary.csv",
        TABLES_DIR / "q12_urban_provincial_summary.csv",
        TABLES_DIR / "q12_warehouse_imbalance_visual_summary.csv",
        TABLES_DIR / "q13_segment_profile_summary.csv",
        TABLES_DIR / "q13_segment_packaging_summary.csv",
        TABLES_DIR / "q13_segment_geographic_spread_summary.csv",
        TABLES_DIR / "q13_segment_province_spread_summary.csv",
        TABLES_DIR / "q13_order_profile_segments.csv",
        TABLES_DIR / "shared_document_type_summary.csv",
        TABLES_DIR / "q12_customer_match_quality_summary.csv",
        TABLES_DIR / "q12_geography_source_summary.csv",
        TABLES_DIR / "q12_unresolved_customer_summary.csv",
        NOTES_DIR / NOTE_FILENAME,
        CHARTS_DIR / "q11_abc_quantity_distribution.png",
        CHARTS_DIR / "q11_abc_frequency_distribution.png",
        CHARTS_DIR / "q11_abc_xyz_matrix.png",
        CHARTS_DIR / "q11_abc_quantity_frequency_matrix.png",
        CHARTS_DIR / "q12_region_quantity_orders.png",
        CHARTS_DIR / "q12_warehouse_region_quantity_split.png",
        CHARTS_DIR / "q13_order_profile_comparison.png",
        CHARTS_DIR / "q12_top_demand_provinces_map.png",
        CHARTS_DIR / "q12_province_demand_choropleths.png",
        CHARTS_DIR / "q12_warehouse_dominance_map.png",
        CHARTS_DIR / "q12_geography_coverage_map.png",
        CHARTS_DIR / "q12_province_distance_correlation.png",
        CHARTS_DIR / "q12_urban_provincial_split.png",
        CHARTS_DIR / "q12_warehouse_imbalance.png",
        CHARTS_DIR / "q13_packaging_mix.png",
        CHARTS_DIR / "q13_geographic_spread.png",
        CHARTS_DIR / "q13_segment_geographic_maps.png",
        CHARTS_DIR / "q12_region_reference_map.png",
    ]
    missing_files = [path for path in required_outputs if not path.exists()]
    if missing_files:
        raise ValueError(f"Missing required output files: {missing_files}")
    stale_files = [path for path in STALE_OUTPUTS if path.exists()]
    if stale_files:
        raise ValueError(f"Speculative output files should not exist: {stale_files}")
    if customer_cluster_summary.empty:
        raise ValueError("Customer cluster summary should not be empty for the assignment window")


if __name__ == "__main__":
    main()
