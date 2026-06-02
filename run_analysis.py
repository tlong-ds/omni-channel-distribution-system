from src.logage2026.analysis import (
    ASSIGNMENT_END,
    ASSIGNMENT_START,
    build_abc_xyz,
    build_abc_xyz_matrix_summary,
    build_customer_match_quality_summary,
    build_customer_cluster_summary,
    build_document_type_summary,
    build_fast_moving_summary,
    build_geography_coverage_summary,
    build_geography_source_summary,
    build_order_profile_segments,
    build_unresolved_customer_summary,
    build_warehouse_imbalance_summary,
    build_warehouse_region_summary,
    filter_assignment_shipments,
)
from src.logage2026.cleaning import clean_distributors, clean_shipments, clean_sku_master
from src.logage2026.config import CHARTS_DIR, CLEANED_DIR, NOTES_DIR, OUTPUT_DIR, TABLES_DIR
from src.logage2026.loading import load_distributors, load_sku_master, load_transactions
from src.logage2026.notes import write_notes
from src.logage2026.visuals import save_charts


EXPECTED_ASSIGNMENT_ROWS = 43_955
EXPECTED_ASSIGNMENT_QUANTITY = 372_333.80
EXPECTED_ASSIGNMENT_CBM = 20_565.06

STALE_OUTPUTS = [
    TABLES_DIR / "safety_stock_class_a.csv",
    TABLES_DIR / "slotting_plan.csv",
    NOTES_DIR / "recommendations.md",
    NOTES_DIR / "pick_pack_flowchart.md",
]


def main() -> None:
    for directory in [CLEANED_DIR, TABLES_DIR, NOTES_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    sku_master = clean_sku_master(load_sku_master())
    distributors = clean_distributors(load_distributors())
    shipments = clean_shipments(load_transactions(), distributors)
    assignment_shipments = filter_assignment_shipments(shipments)

    abc_xyz = build_abc_xyz(assignment_shipments, sku_master)
    abc_xyz_matrix = build_abc_xyz_matrix_summary(abc_xyz)
    fast_moving_summary = build_fast_moving_summary(abc_xyz)
    geography_coverage_summary = build_geography_coverage_summary(assignment_shipments)
    warehouse_region_summary = build_warehouse_region_summary(assignment_shipments)
    customer_cluster_summary = build_customer_cluster_summary(assignment_shipments)
    warehouse_imbalance_summary = build_warehouse_imbalance_summary(assignment_shipments)
    order_profile_segments = build_order_profile_segments(assignment_shipments)
    document_type_summary = build_document_type_summary(shipments)
    customer_match_quality_summary = build_customer_match_quality_summary(assignment_shipments)
    geography_source_summary = build_geography_source_summary(assignment_shipments)
    unresolved_customer_summary = build_unresolved_customer_summary(assignment_shipments)

    sku_master.to_csv(CLEANED_DIR / "sku_master_cleaned.csv", index=False)
    distributors.to_csv(CLEANED_DIR / "distributors_cleaned.csv", index=False)
    shipments.to_csv(CLEANED_DIR / "shipments_cleaned.csv", index=False)

    abc_xyz.to_csv(TABLES_DIR / "abc_xyz.csv", index=False)
    abc_xyz_matrix.to_csv(TABLES_DIR / "abc_xyz_matrix_summary.csv", index=False)
    fast_moving_summary.to_csv(TABLES_DIR / "fast_moving_summary.csv", index=False)
    geography_coverage_summary.to_csv(TABLES_DIR / "geography_coverage_summary.csv", index=False)
    warehouse_region_summary.to_csv(TABLES_DIR / "warehouse_region_summary.csv", index=False)
    customer_cluster_summary.to_csv(TABLES_DIR / "customer_cluster_summary.csv", index=False)
    warehouse_imbalance_summary.to_csv(TABLES_DIR / "warehouse_imbalance_summary.csv", index=False)
    order_profile_segments.to_csv(TABLES_DIR / "order_profile_segments.csv", index=False)
    document_type_summary.to_csv(TABLES_DIR / "document_type_summary.csv", index=False)
    customer_match_quality_summary.to_csv(TABLES_DIR / "customer_match_quality_summary.csv", index=False)
    geography_source_summary.to_csv(TABLES_DIR / "geography_source_summary.csv", index=False)
    unresolved_customer_summary.to_csv(TABLES_DIR / "unresolved_customer_summary.csv", index=False)

    _remove_stale_outputs()
    save_charts(assignment_shipments, abc_xyz, abc_xyz_matrix, warehouse_region_summary)
    write_notes(
        assignment_shipments,
        abc_xyz,
        abc_xyz_matrix,
        fast_moving_summary,
        geography_coverage_summary,
        warehouse_region_summary,
        customer_cluster_summary,
        warehouse_imbalance_summary,
    )
    verify_outputs(
        shipments,
        assignment_shipments,
        abc_xyz,
        abc_xyz_matrix,
        geography_coverage_summary,
        warehouse_region_summary,
        customer_cluster_summary,
        warehouse_imbalance_summary,
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
    geography_coverage_summary,
    warehouse_region_summary,
    customer_cluster_summary,
    warehouse_imbalance_summary,
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
    if warehouse_imbalance_summary["orders"].sum() < known["order_id"].nunique():
        raise ValueError("Warehouse imbalance summary unexpectedly undercounts known-geography orders")
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
        TABLES_DIR / "abc_xyz.csv",
        TABLES_DIR / "abc_xyz_matrix_summary.csv",
        TABLES_DIR / "fast_moving_summary.csv",
        TABLES_DIR / "geography_coverage_summary.csv",
        TABLES_DIR / "warehouse_region_summary.csv",
        TABLES_DIR / "customer_cluster_summary.csv",
        TABLES_DIR / "warehouse_imbalance_summary.csv",
        TABLES_DIR / "order_profile_segments.csv",
        TABLES_DIR / "document_type_summary.csv",
        TABLES_DIR / "customer_match_quality_summary.csv",
        TABLES_DIR / "geography_source_summary.csv",
        TABLES_DIR / "unresolved_customer_summary.csv",
        NOTES_DIR / "question_summary.md",
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
