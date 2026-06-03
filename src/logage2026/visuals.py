import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import os
os.environ.setdefault("MPLCONFIGDIR", "outputs/round2/.matplotlib")

import matplotlib.pyplot as plt
import pandas as pd

from src.logage2026.analysis import ASSIGNMENT_END, ASSIGNMENT_START
from src.logage2026.config import CHARTS_DIR


def save_charts(
    shipments: pd.DataFrame,
    abc_xyz: pd.DataFrame,
    abc_xyz_matrix: pd.DataFrame,
    warehouse_region_summary: pd.DataFrame,
    sku_master: pd.DataFrame,
) -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    _abc_bar(abc_xyz)
    _abc_xyz_matrix_chart(abc_xyz_matrix)
    _region_bar(warehouse_region_summary)
    _warehouse_quantity_bar(shipments)
    _order_profile_chart(shipments, sku_master)
    _vietnam_map_chart()


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


def _order_profile_chart(shipments: pd.DataFrame, sku_master: pd.DataFrame) -> None:
    from .analysis import build_order_profile_segments
    summary = build_order_profile_segments(shipments, sku_master)
    summary = summary.set_index("customer_segment").reindex(["Modern Trade", "Traditional Trade / Distributor"])
    
    fig, axes = plt.subplots(3, 2, figsize=(11, 10))
    metrics = [
        ("orders", "Order count", "#4f7cac"),
        ("avg_order_quantity", "Avg order quantity (pcs)", "#2f6f73"),
        ("avg_order_cbm", "Avg order CBM", "#d29d3d"),
        ("avg_sku_breadth", "Avg SKU breadth per order", "#b45f3c"),
        ("avg_orders_per_customer_month", "Avg orders / customer / month", "#6366f1"),
        ("avg_distance_km", "Avg distance to warehouse (km)", "#ec4899"),
    ]
    for ax, (column, title, color) in zip(axes.flatten(), metrics):
        summary[column].plot(kind="bar", ax=ax, color=color)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=10)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(f"Order profile comparison by customer segment\n{_window_label()}", y=0.99, fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "order_profile_comparison.png", dpi=160)
    plt.close(fig)


def _vietnam_map_chart() -> None:
    try:
        import geopandas as gpd
        import unicodedata
        from .geography import to_new_province, region_group
        
        gdf = gpd.read_file("vietnam_provinces.json")
        gdf["province_std"] = gdf["NAME_1"].apply(to_new_province)
        gdf["region"] = gdf["province_std"].apply(region_group)
        
        colors = {
            "Đông Nam Bộ": "#2f6f73",
            "Đồng bằng sông Cửu Long": "#3d6b35",
            "Bắc Trung Bộ và Duyên hải miền Trung": "#4f7cac",
            "Tây Nguyên": "#d29d3d",
            "Đồng bằng sông Hồng": "#b45f3c",
            "Trung du và miền núi phía Bắc": "#8b8f9b",
        }
        
        fig, ax = plt.subplots(figsize=(8, 12))
        ax.axis("off")
        fig.patch.set_facecolor("#0f172a")
        ax.set_facecolor("#0f172a")
        
        for region, color in colors.items():
            region_gdf = gdf[gdf["region"] == region]
            if not region_gdf.empty:
                region_gdf.plot(ax=ax, color=color, edgecolor="#1e293b", linewidth=0.6)
                
        ax.set_title("Vietnam Regional Segmentation Map", color="white", fontsize=16, pad=20, weight="bold")
        
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=color, edgecolor="#1e293b", label=region) for region, color in colors.items()]
        ax.legend(handles=legend_elements, loc="lower right", facecolor="#1e293b", edgecolor="#334155", labelcolor="white", framealpha=0.9, fontsize=10)
        
        fig.tight_layout()
        fig.savefig(CHARTS_DIR / "vietnam_regions_map.png", dpi=160, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
    except Exception as e:
        print(f"Skipping Vietnam map generation: {e}")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    
    from src.logage2026.config import CLEANED_DIR, TABLES_DIR
    
    print("Loading static cleaned data from disk...")
    try:
        shipments = pd.read_csv(CLEANED_DIR / "shipments_cleaned.csv")
        abc_xyz = pd.read_csv(TABLES_DIR / "abc_xyz.csv")
        abc_xyz_matrix = pd.read_csv(TABLES_DIR / "abc_xyz_matrix_summary.csv")
        warehouse_region_summary = pd.read_csv(TABLES_DIR / "warehouse_region_summary.csv")
        sku_master = pd.read_csv(CLEANED_DIR / "sku_master_cleaned.csv")
        
        # Convert dates
        shipments["created_date"] = pd.to_datetime(shipments["created_date"])
        
        print("Generating charts from static output...")
        save_charts(shipments, abc_xyz, abc_xyz_matrix, warehouse_region_summary, sku_master)
        print("Charts generated successfully!")
    except Exception as e:
        print(f"Error loading static output: {e}")
        print("Please run run_analysis.py first to generate the outputs.")
