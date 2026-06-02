import pandas as pd

from .config import NOTES_DIR


def write_notes(
    shipments: pd.DataFrame,
    abc_xyz: pd.DataFrame,
    abc_xyz_matrix: pd.DataFrame,
    fast_moving_summary: pd.DataFrame,
    geography_coverage_summary: pd.DataFrame,
    warehouse_region_summary: pd.DataFrame,
    customer_cluster_summary: pd.DataFrame,
    warehouse_imbalance_summary: pd.DataFrame,
) -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    text = [
        "# Round 2 Question Summary",
        "",
        "## Data basis",
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
