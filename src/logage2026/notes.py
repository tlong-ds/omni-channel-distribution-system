import pandas as pd

from .config import NOTES_DIR


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
        "![Q1.1 ABC quantity distribution](../charts/abc_quantity_distribution.png)",
        "",
        "![Q1.1 ABC-XYZ matrix](../charts/abc_xyz_matrix.png)",
        "",
        "## Q1.2 Demand geography with ambiguity-safe matching",
        "![Q1.2 Regional quantity](../charts/regional_quantity_density.png)",
        "",
        "![Q1.2 Warehouse-region split](../charts/warehouse_region_split.png)",
        "",
        "## Q1.3 Order profile analysis",
        "![Q1.3 Order profile comparison](../charts/order_profile_comparison.png)",
    ]
    (NOTES_DIR / "question_summary.md").write_text("\n".join(text) + "\n", encoding="utf-8")
