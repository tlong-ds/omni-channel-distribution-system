import os

os.environ.setdefault("MPLCONFIGDIR", "outputs/round2/.matplotlib")

import matplotlib.pyplot as plt
import pandas as pd

from .analysis import ASSIGNMENT_END, ASSIGNMENT_START
from .config import CHARTS_DIR


def save_charts(
    shipments: pd.DataFrame,
    abc_xyz: pd.DataFrame,
    abc_xyz_matrix: pd.DataFrame,
    warehouse_region_summary: pd.DataFrame,
) -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    _abc_bar(abc_xyz)
    _abc_xyz_matrix_chart(abc_xyz_matrix)
    _region_bar(warehouse_region_summary)
    _warehouse_quantity_bar(shipments)
    _order_profile_chart(shipments)


def _window_label() -> str:
    return f"{ASSIGNMENT_START.date().isoformat()} to {ASSIGNMENT_END.date().isoformat()}"


def _abc_bar(abc_xyz: pd.DataFrame) -> None:
    chart = abc_xyz.groupby("abc_quantity")["quantity"].sum().reindex(["A", "B", "C"])
    fig, ax = plt.subplots(figsize=(7, 4))
    chart.plot(kind="bar", ax=ax, color=["#2f6f73", "#d29d3d", "#8b8f9b"])
    ax.set_title(f"Outbound quantity by ABC class\n{_window_label()}")
    ax.set_xlabel("ABC quantity class")
    ax.set_ylabel("Quantity")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "abc_quantity_distribution.png", dpi=160)
    plt.close(fig)


def _abc_xyz_matrix_chart(abc_xyz_matrix: pd.DataFrame) -> None:
    pivot = (
        abc_xyz_matrix.pivot(index="abc_quantity", columns="xyz", values="sku_count")
        .reindex(index=["A", "B", "C"], columns=["X", "Y", "Z"])
        .fillna(0)
    )
    fig, ax = plt.subplots(figsize=(6, 4.5))
    image = ax.imshow(pivot.values, cmap="YlGnBu")
    ax.set_title(f"ABC-XYZ SKU count matrix\n{_window_label()}")
    ax.set_xlabel("XYZ class")
    ax.set_ylabel("ABC quantity class")
    ax.set_xticks(range(len(pivot.columns)), labels=pivot.columns)
    ax.set_yticks(range(len(pivot.index)), labels=pivot.index)
    for row_idx, row_label in enumerate(pivot.index):
        for col_idx, col_label in enumerate(pivot.columns):
            ax.text(col_idx, row_idx, f"{int(pivot.loc[row_label, col_label])}", ha="center", va="center", color="#102a43")
    fig.colorbar(image, ax=ax, shrink=0.85, label="SKU count")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "abc_xyz_matrix.png", dpi=160)
    plt.close(fig)


def _region_bar(summary: pd.DataFrame) -> None:
    chart = summary.groupby("region")["quantity"].sum().sort_values(ascending=False).head(12)
    fig, ax = plt.subplots(figsize=(9, 5))
    chart.sort_values().plot(kind="barh", ax=ax, color="#4f7cac")
    ax.set_title(f"Known-customer outbound quantity by region\n{_window_label()}")
    ax.set_xlabel("Quantity")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "regional_quantity_density.png", dpi=160)
    plt.close(fig)


def _warehouse_quantity_bar(shipments: pd.DataFrame) -> None:
    known = shipments[shipments["known_geography_flag"]]
    chart = known.groupby(["region", "source_warehouse"])["quantity"].sum().unstack(fill_value=0)
    chart = chart.loc[chart.sum(axis=1).sort_values(ascending=False).head(8).index]
    fig, ax = plt.subplots(figsize=(9, 5))
    chart.plot(kind="bar", ax=ax, color=["#3d6b35", "#b45f3c"])
    ax.set_title(f"Warehouse split by known-customer region\n{_window_label()}")
    ax.set_xlabel("")
    ax.set_ylabel("Quantity")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "warehouse_region_split.png", dpi=160)
    plt.close(fig)


def _order_profile_chart(shipments: pd.DataFrame) -> None:
    known = shipments[shipments["analysis_document_flag"] & shipments["customer_segment"].ne("Unknown")].copy()
    order_level = (
        known.groupby(["customer_segment", "order_id"])
        .agg(quantity=("quantity", "sum"), cbm_total=("cbm_total", "sum"), sku_breadth=("sku_code", "nunique"))
        .reset_index()
    )
    summary = (
        order_level.groupby("customer_segment")
        .agg(
            orders=("order_id", "nunique"),
            avg_order_quantity=("quantity", "mean"),
            avg_order_cbm=("cbm_total", "mean"),
            avg_sku_breadth=("sku_breadth", "mean"),
        )
        .reindex(["Modern Trade", "Traditional Trade / Distributor"])
    )
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    metrics = [
        ("orders", "Order count", "#4f7cac"),
        ("avg_order_quantity", "Avg order quantity", "#2f6f73"),
        ("avg_order_cbm", "Avg order CBM", "#d29d3d"),
        ("avg_sku_breadth", "Avg SKU breadth", "#b45f3c"),
    ]
    for ax, (column, title, color) in zip(axes.flatten(), metrics):
        summary[column].plot(kind="bar", ax=ax, color=color)
        ax.set_title(title)
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(f"Order profile by customer segment\n{_window_label()}", y=0.98)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "order_profile_comparison.png", dpi=160)
    plt.close(fig)
