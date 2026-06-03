import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import os
import unicodedata

os.environ.setdefault("MPLCONFIGDIR", "outputs/round2/.matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.logage2026.analysis import ASSIGNMENT_END, ASSIGNMENT_START, SEGMENT_ORDER
from src.logage2026.config import CHARTS_DIR, ROOT_DIR
from src.logage2026.geography import region_group


PROVINCE_BOUNDARY_FILE = ROOT_DIR / "vietnam_provinces.json"
REGION_COLOR_MAP = {
    "Đông Nam Bộ": "#0f766e",
    "Đồng bằng sông Cửu Long": "#65a30d",
    "Bắc Trung Bộ và Duyên hải miền Trung": "#2563eb",
    "Tây Nguyên": "#d97706",
    "Đồng bằng sông Hồng": "#dc2626",
    "Trung du và miền núi phía Bắc": "#7c3aed",
}
WAREHOUSE_COLOR_MAP = {
    "My Phuoc": "#166534",
    "Vinh Loc": "#b45309",
    "Balanced": "#64748b",
}
SEGMENT_COLOR_MAP = {
    "Modern Trade": "#1d4ed8",
    "Traditional Trade / Distributor": "#b45309",
}


def save_charts(
    shipments: pd.DataFrame,
    abc_xyz: pd.DataFrame,
    abc_xyz_matrix: pd.DataFrame,
    warehouse_region_summary: pd.DataFrame,
    q12_region_orders_quantity_summary: pd.DataFrame,
    q12_province_cluster_summary: pd.DataFrame,
    q12_province_demand_summary: pd.DataFrame,
    q12_province_warehouse_dominance_summary: pd.DataFrame,
    q12_province_correlation_input_summary: pd.DataFrame,
    q12_urban_provincial_summary: pd.DataFrame,
    q12_warehouse_imbalance_visual_summary: pd.DataFrame,
    q13_segment_profile_summary: pd.DataFrame,
    q13_segment_packaging_summary: pd.DataFrame,
    q13_segment_geographic_spread_summary: pd.DataFrame,
    q13_segment_province_spread_summary: pd.DataFrame,
    sku_master: pd.DataFrame,
) -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    province_layer = _prepare_vietnam_province_layer()

    _abc_bar(abc_xyz)
    _abc_xyz_matrix_chart(abc_xyz_matrix)
    _region_bar(q12_region_orders_quantity_summary)
    _warehouse_quantity_bar(shipments)
    _q12_province_cluster_chart(q12_province_cluster_summary)
    _q12_province_demand_maps_chart(province_layer, q12_province_demand_summary)
    _q12_province_warehouse_dominance_map_chart(province_layer, q12_province_warehouse_dominance_summary)
    _q12_geography_coverage_map_chart(province_layer, q12_province_demand_summary, shipments)
    _q12_province_distance_correlation_chart(province_layer, q12_province_correlation_input_summary)
    _q12_urban_provincial_chart(q12_urban_provincial_summary)
    _q12_warehouse_imbalance_chart(q12_warehouse_imbalance_visual_summary)
    _order_profile_chart(q13_segment_profile_summary)
    _q13_packaging_mix_chart(q13_segment_packaging_summary)
    _q13_geographic_spread_chart(q13_segment_geographic_spread_summary)
    _q13_segment_geographic_maps_chart(province_layer, q13_segment_province_spread_summary)
    _vietnam_region_reference_map_chart(province_layer)


def _window_label() -> str:
    return f"{ASSIGNMENT_START.date().isoformat()} to {ASSIGNMENT_END.date().isoformat()}"


def _normalize_name_token(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    token = value.lower().replace(" ", "").replace("-", "")
    token = "".join(char for char in unicodedata.normalize("NFKD", token) if not unicodedata.combining(char))
    return token.replace("đ", "d")


def _province_name_mapping() -> dict[str, str]:
    return {
        "angiang": "An Giang",
        "bariavungtau": "Bà Rịa - Vũng Tàu",
        "bacgiang": "Bắc Giang",
        "backan": "Bắc Kạn",
        "baclieu": "Bạc Liêu",
        "bacninh": "Bắc Ninh",
        "bentre": "Bến Tre",
        "binhdinh": "Bình Định",
        "binhduong": "Bình Dương",
        "binhphuoc": "Bình Phước",
        "binhthuan": "Bình Thuận",
        "camau": "Cà Mau",
        "cantho": "Cần Thơ",
        "caobang": "Cao Bằng",
        "danang": "Đà Nẵng",
        "daklak": "Đắk Lắk",
        "daknong": "Đắk Nông",
        "dienbien": "Điện Biên",
        "dongnai": "Đồng Nai",
        "dongthap": "Đồng Tháp",
        "gialai": "Gia Lai",
        "hagiang": "Hà Giang",
        "hanam": "Hà Nam",
        "hanoi": "Hà Nội",
        "hatinh": "Hà Tĩnh",
        "haiduong": "Hải Dương",
        "haiphong": "Hải Phòng",
        "haugiang": "Hậu Giang",
        "hochiminh": "Hồ Chí Minh",
        "hoabinh": "Hòa Bình",
        "hungyen": "Hưng Yên",
        "khanhhoa": "Khánh Hòa",
        "kiengiang": "Kiên Giang",
        "kontum": "Kon Tum",
        "laichau": "Lai Châu",
        "lamdong": "Lâm Đồng",
        "langson": "Lạng Sơn",
        "laocai": "Lào Cai",
        "longan": "Long An",
        "namdinh": "Nam Định",
        "nghean": "Nghệ An",
        "ninhbinh": "Ninh Bình",
        "ninhthuan": "Ninh Thuận",
        "phutho": "Phú Thọ",
        "phuyen": "Phú Yên",
        "quangbinh": "Quảng Bình",
        "quangnam": "Quảng Nam",
        "quangngai": "Quảng Ngãi",
        "quangninh": "Quảng Ninh",
        "quangtri": "Quảng Trị",
        "soctrang": "Sóc Trăng",
        "sonla": "Sơn La",
        "tayninh": "Tây Ninh",
        "thaibinh": "Thái Bình",
        "thainguyen": "Thái Nguyên",
        "thanhhoa": "Thanh Hóa",
        "thuathienhue": "Huế",
        "tiengiang": "Tiền Giang",
        "travinh": "Trà Vinh",
        "tuyenquang": "Tuyên Quang",
        "vinhlong": "Vĩnh Long",
        "vinhphuc": "Vĩnh Phúc",
        "yenbai": "Yên Bái",
    }


def _normalize_boundary_province_name(name: object) -> str:
    mapping = _province_name_mapping()
    token = _normalize_name_token(name)
    return mapping.get(token, str(name).strip() if isinstance(name, str) else "Unknown")


def _prepare_vietnam_province_layer():
    import geopandas as gpd

    layer = gpd.read_file(PROVINCE_BOUNDARY_FILE)
    layer["province"] = layer["NAME_1"].map(_normalize_boundary_province_name)
    layer["region"] = layer["province"].map(region_group)
    return layer


def _province_layer_with_data(province_layer, summary: pd.DataFrame, value_columns: list[str]):
    merge_columns = ["province"] + [column for column in value_columns if column in summary.columns]
    if "region" in summary.columns and "region" not in merge_columns:
        merge_columns.append("region")
    merged = province_layer.merge(summary[merge_columns], on="province", how="left", suffixes=("", "_summary"))
    if "region_summary" in merged.columns:
        merged["region"] = merged["region_summary"].fillna(merged["region"])
        merged = merged.drop(columns=["region_summary"])
    return merged


def _style_map_axis(ax, title: str) -> None:
    ax.set_title(title, fontsize=12, weight="bold")
    ax.set_axis_off()


def _add_top_labels(ax, merged, label_column: str, value_column: str, top_n: int = 5) -> None:
    available = merged.dropna(subset=[value_column]).sort_values(value_column, ascending=False).head(top_n)
    if available.empty:
        return
    centroids = available.geometry.representative_point()
    for (_, row), point in zip(available.iterrows(), centroids, strict=False):
        ax.text(point.x, point.y, str(row[label_column]), fontsize=7.5, color="#0f172a", ha="center", va="center")


def _add_callout_labels(ax, merged, label_column: str, value_column: str, top_n: int = 10) -> None:
    available = merged.dropna(subset=[value_column]).sort_values(value_column, ascending=False).head(top_n).copy()
    if available.empty:
        return
    points = available.geometry.representative_point()
    x_mid = float(points.x.median())
    overrides = {
        "Đồng Nai": {"dx": 1.0, "dy": -0.45, "ha": "left"},
        "Đà Nẵng": {"dx": -1.55, "dy": 0.15, "ha": "right"},
        "Quảng Nam": {"dx": -1.75, "dy": -0.05, "ha": "right"},
        "Khánh Hòa": {"dx": -1.45, "dy": 0.2, "ha": "right"},
        "Bình Thuận": {"dx": 1.15, "dy": -0.35, "ha": "left"},
        "Hà Nội": {"dx": -1.55, "dy": 0.0, "ha": "right"},
        "Hải Phòng": {"dx": 1.2, "dy": 0.35, "ha": "left"},
        "Nghệ An": {"dx": -1.3, "dy": -0.1, "ha": "right"},
        "Hòa Bình": {"dx": -1.2, "dy": -0.45, "ha": "right"},
        "Đắk Lắk": {"dx": -1.2, "dy": 0.15, "ha": "right"},
        "Cần Thơ": {"dx": -1.35, "dy": -0.35, "ha": "right"},
        "Tiền Giang": {"dx": -1.1, "dy": 0.02, "ha": "right"},
        "Bình Dương": {"dx": -1.15, "dy": 0.15, "ha": "right"},
        "Hồ Chí Minh": {"dx": -1.1, "dy": -0.3, "ha": "right"},
    }
    for idx, ((_, row), point) in enumerate(zip(available.iterrows(), points, strict=False)):
        side = 1 if point.x >= x_mid else -1
        default = {"dx": 1.6 * side, "dy": 0.0, "ha": "left" if side > 0 else "right"}
        custom = overrides.get(str(row[label_column]), {})
        dx = custom.get("dx", default["dx"])
        dy = custom.get("dy", default["dy"])
        ha = custom.get("ha", default["ha"])
        ax.annotate(
            str(row[label_column]),
            xy=(point.x, point.y),
            xytext=(point.x + dx, point.y + dy),
            textcoords="data",
            fontsize=8,
            color="#0f172a",
            ha=ha,
            va="center",
            arrowprops={"arrowstyle": "-", "color": "#334155", "linewidth": 1.1, "shrinkA": 0, "shrinkB": 0},
            bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
        )


def boundary_province_names() -> set[str]:
    return set(_prepare_vietnam_province_layer()["province"].dropna().astype(str))


def _abc_bar(abc_xyz: pd.DataFrame) -> None:
    chart = abc_xyz.groupby("abc_quantity")["quantity"].sum().reindex(["A", "B", "C"])
    fig, ax = plt.subplots(figsize=(7, 4))
    chart.plot(kind="bar", ax=ax, color=["#2f6f73", "#d29d3d", "#8b8f9b"])
    ax.set_title(f"Outbound quantity by ABC class\n{_window_label()}")
    ax.set_xlabel("ABC quantity class")
    ax.set_ylabel("Quantity")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q11_abc_quantity_distribution.png", dpi=160)
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
    fig.savefig(CHARTS_DIR / "q11_abc_xyz_matrix.png", dpi=160)
    plt.close(fig)


def _region_bar(summary: pd.DataFrame) -> None:
    ordered = summary.sort_values("quantity", ascending=False).copy()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    y = np.arange(len(ordered))
    ax.barh(y, ordered["quantity"], color="#4f7cac", alpha=0.85, label="Quantity")
    ax.set_yticks(y, labels=ordered["region"])
    ax.invert_yaxis()
    ax.set_xlabel("Quantity")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    ax.set_title(f"Known-customer demand by region: quantity and orders\n{_window_label()}")
    ax2 = ax.twiny()
    ax2.plot(ordered["orders"], y, color="#b45f3c", marker="o", linewidth=2, label="Orders")
    ax2.set_xlabel("Orders")
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc="lower right")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q12_region_quantity_orders.png", dpi=160)
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
    fig.savefig(CHARTS_DIR / "q12_warehouse_region_quantity_split.png", dpi=160)
    plt.close(fig)


def _q12_province_cluster_chart(summary: pd.DataFrame) -> None:
    province_layer = _prepare_vietnam_province_layer()
    ordered = summary.sort_values(["rank_by_quantity", "rank_by_orders", "quantity"], ascending=[True, True, False]).copy()
    merged = _province_layer_with_data(province_layer, ordered, ["quantity", "orders", "region"])
    fig, ax = plt.subplots(figsize=(8.5, 12))
    province_layer.plot(ax=ax, color="#f3f4f6", edgecolor="#cbd5e1", linewidth=0.45)
    hotspots = merged.dropna(subset=["quantity"]).sort_values("quantity", ascending=False).copy()
    if not hotspots.empty:
        hotspots.plot(
            ax=ax,
            column="quantity",
            cmap="YlOrRd",
            edgecolor="#0f172a",
            linewidth=0.9,
            alpha=0.92,
            legend=True,
            legend_kwds={"shrink": 0.75, "label": "Quantity"},
        )
        hotspots.boundary.plot(ax=ax, color="#0f172a", linewidth=1.1)
    _add_callout_labels(ax, hotspots, "province", "quantity", top_n=min(14, len(hotspots)))
    _style_map_axis(ax, f"Top demand provinces map\n{_window_label()}")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q12_top_demand_provinces_map.png", dpi=160)
    plt.close(fig)


def _q12_province_demand_maps_chart(province_layer, summary: pd.DataFrame) -> None:
    merged = _province_layer_with_data(province_layer, summary, ["quantity", "orders", "customers"])
    fig, axes = plt.subplots(1, 3, figsize=(16, 8))
    specs = [
        ("quantity", "Province quantity"),
        ("orders", "Province orders"),
        ("customers", "Province customers"),
    ]
    for ax, (column, title) in zip(axes, specs, strict=False):
        merged.plot(
            column=column,
            ax=ax,
            cmap="YlGnBu",
            linewidth=0.35,
            edgecolor="#1f2937",
            missing_kwds={"color": "#e5e7eb", "edgecolor": "#9ca3af", "hatch": "///", "label": "No mapped demand"},
            legend=True,
            legend_kwds={"shrink": 0.7},
        )
        _style_map_axis(ax, title)
        if column == "quantity":
            _add_top_labels(ax, merged, "province", "quantity")
    fig.suptitle(f"Q1.2 Province demand choropleths\n{_window_label()}", y=0.98, fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q12_province_demand_choropleths.png", dpi=160)
    plt.close(fig)


def _q12_province_warehouse_dominance_map_chart(province_layer, summary: pd.DataFrame) -> None:
    merged = _province_layer_with_data(province_layer, summary, ["dominant_warehouse", "dominance_intensity"])
    fig, ax = plt.subplots(figsize=(8.5, 12))
    for warehouse, color in WAREHOUSE_COLOR_MAP.items():
        subset = merged[merged["dominant_warehouse"].eq(warehouse)]
        if subset.empty:
            continue
        alpha = 0.45 + subset["dominance_intensity"].fillna(0).clip(0, 1) * 0.5
        subset.plot(ax=ax, color=color, linewidth=0.4, edgecolor="#0f172a", alpha=alpha)
    merged[merged["dominant_warehouse"].isna()].plot(
        ax=ax,
        color="#e5e7eb",
        linewidth=0.35,
        edgecolor="#9ca3af",
        hatch="///",
    )
    _style_map_axis(ax, f"Province warehouse dominance map\n{_window_label()}")
    from matplotlib.patches import Patch

    legend_items = [
        Patch(facecolor=color, edgecolor="#0f172a", label=label)
        for label, color in WAREHOUSE_COLOR_MAP.items()
    ] + [Patch(facecolor="#e5e7eb", edgecolor="#9ca3af", hatch="///", label="No mapped demand")]
    ax.legend(handles=legend_items, loc="lower left", frameon=True, fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q12_warehouse_dominance_map.png", dpi=160)
    plt.close(fig)


def _q12_geography_coverage_map_chart(province_layer, summary: pd.DataFrame, shipments: pd.DataFrame) -> None:
    merged = _province_layer_with_data(province_layer, summary, ["quantity"])
    total_quantity = shipments.loc[shipments["analysis_document_flag"], "quantity"].sum()
    mapped_quantity = shipments.loc[shipments["analysis_document_flag"] & shipments["known_geography_flag"], "quantity"].sum()
    unresolved_quantity = total_quantity - mapped_quantity
    unresolved_share = (unresolved_quantity / total_quantity) if total_quantity else 0.0

    fig, ax = plt.subplots(figsize=(8.5, 12))
    merged.plot(
        column="quantity",
        ax=ax,
        cmap="Blues",
        linewidth=0.35,
        edgecolor="#1f2937",
        missing_kwds={"color": "#ffffff", "edgecolor": "#9ca3af", "hatch": "///", "label": "Unresolved / excluded"},
        legend=True,
        legend_kwds={"shrink": 0.7, "label": "Mapped quantity"},
    )
    _style_map_axis(ax, f"Mapped province demand coverage\nUnresolved quantity: {unresolved_share:.1%} of demand")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q12_geography_coverage_map.png", dpi=160)
    plt.close(fig)


def _q12_province_distance_correlation_chart(province_layer, summary: pd.DataFrame) -> None:
    merged = _province_layer_with_data(province_layer, summary, ["quantity"])
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))

    merged.plot(
        column="quantity",
        ax=axes[0],
        cmap="YlOrRd",
        linewidth=0.35,
        edgecolor="#1f2937",
        missing_kwds={"color": "#e5e7eb", "edgecolor": "#9ca3af", "hatch": "///"},
        legend=True,
        legend_kwds={"shrink": 0.75, "label": "Quantity"},
    )
    _style_map_axis(axes[0], "Province demand intensity")
    _add_top_labels(axes[0], merged, "province", "quantity")

    scatter = summary.dropna(subset=["avg_distance_km", "quantity"]).copy()
    colors = scatter["region"].map(REGION_COLOR_MAP).fillna("#64748b")
    sizes = 40 + (scatter["orders"] / scatter["orders"].max()).fillna(0) * 260 if not scatter.empty else []
    axes[1].scatter(scatter["avg_distance_km"], scatter["quantity"], s=sizes, c=colors, alpha=0.85, edgecolors="white", linewidth=0.8)
    for _, row in scatter.sort_values("quantity", ascending=False).head(6).iterrows():
        axes[1].annotate(row["province"], (row["avg_distance_km"], row["quantity"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
    axes[1].set_title("Quantity vs serving-warehouse distance proxy", fontsize=12, weight="bold")
    axes[1].set_xlabel("Average distance to serving warehouse (km)")
    axes[1].set_ylabel("Quantity")
    axes[1].grid(alpha=0.25)

    fig.suptitle(f"Q1.2 Province demand and distance pair\n{_window_label()}", y=0.98, fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q12_province_distance_correlation.png", dpi=160)
    plt.close(fig)


def _q12_urban_provincial_chart(summary: pd.DataFrame) -> None:
    pivot = summary.pivot(index="geography_tier", columns="source_warehouse", values="quantity").fillna(0)
    pivot = pivot.reindex(["urban", "provincial"]).fillna(0)
    fig, ax = plt.subplots(figsize=(8, 5))
    pivot.plot(kind="bar", stacked=True, ax=ax, color=["#3d6b35", "#b45f3c"])
    ax.set_title(f"Urban vs provincial quantity by serving warehouse\n{_window_label()}")
    ax.set_xlabel("")
    ax.set_ylabel("Quantity")
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q12_urban_provincial_split.png", dpi=160)
    plt.close(fig)


def _q12_warehouse_imbalance_chart(summary: pd.DataFrame) -> None:
    ordered = summary.sort_values("quantity_share_gap").copy()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    colors = ordered["dominant_warehouse"].map(WAREHOUSE_COLOR_MAP)
    ax.barh(ordered["region"], ordered["quantity_share_gap"], color=colors)
    ax.axvline(0, color="#334155", linewidth=1)
    ax.set_title(f"Warehouse dominance gap by region\n{_window_label()}")
    ax.set_xlabel("Quantity share gap (My Phuoc minus Vinh Loc)")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q12_warehouse_imbalance.png", dpi=160)
    plt.close(fig)


def _order_profile_chart(summary: pd.DataFrame) -> None:
    summary = summary.set_index("customer_segment").reindex(SEGMENT_ORDER)
    fig, axes = plt.subplots(4, 2, figsize=(12, 12))
    metrics = [
        ("avg_order_quantity", "Avg order size (pcs)", "#2f6f73"),
        ("avg_order_cbm", "Avg order size (CBM)", "#d29d3d"),
        ("avg_orders_per_customer_month", "Order frequency", "#6366f1"),
        ("avg_sku_breadth", "SKU breadth / order", "#b45f3c"),
        ("province_count", "Province count", "#4f7cac"),
        ("top_province_quantity_share", "Top-province quantity share", "#0f766e"),
        ("avg_distance_km", "Avg distance to warehouse (km proxy)", "#ec4899"),
        ("orders", "Order count", "#64748b"),
    ]
    for ax, (column, title, color) in zip(axes.flatten(), metrics, strict=False):
        summary[column].plot(kind="bar", ax=ax, color=color)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=10)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(f"Segment order profile dashboard\n{_window_label()}", y=0.99, fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q13_order_profile_comparison.png", dpi=160)
    plt.close(fig)


def _q13_packaging_mix_chart(summary: pd.DataFrame) -> None:
    pivot = summary.pivot(index="customer_segment", columns="packaging_unit", values="quantity_share").fillna(0)
    pivot = pivot.reindex(SEGMENT_ORDER).fillna(0)
    pivot = pivot[["pallet", "carton", "loose"]]
    fig, ax = plt.subplots(figsize=(8.5, 5))
    pivot.plot(kind="bar", stacked=True, ax=ax, color=["#3d6b35", "#d29d3d", "#b45f3c"])
    ax.set_title(f"Packaging unit mix by customer segment\n{_window_label()}")
    ax.set_xlabel("")
    ax.set_ylabel("Quantity share")
    ax.tick_params(axis="x", rotation=10)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q13_packaging_mix.png", dpi=160)
    plt.close(fig)


def _q13_geographic_spread_chart(summary: pd.DataFrame) -> None:
    ordered = summary.set_index("customer_segment").reindex(SEGMENT_ORDER)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8))
    ordered["province_count"].plot(kind="bar", ax=axes[0], color="#4f7cac")
    axes[0].set_title("Province coverage")
    axes[0].set_xlabel("")
    axes[0].tick_params(axis="x", rotation=10)
    axes[0].grid(axis="y", alpha=0.25)
    ordered["top_province_quantity_share"].plot(kind="bar", ax=axes[1], color="#0f766e")
    axes[1].set_title("Top-province quantity share")
    axes[1].set_xlabel("")
    axes[1].tick_params(axis="x", rotation=10)
    axes[1].grid(axis="y", alpha=0.25)
    fig.suptitle(f"Geographic spread by customer segment\n{_window_label()}", y=0.98, fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q13_geographic_spread.png", dpi=160)
    plt.close(fig)


def _q13_segment_geographic_maps_chart(province_layer, summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.5))
    for ax, segment in zip(axes, SEGMENT_ORDER, strict=False):
        segment_summary = summary[summary["customer_segment"].eq(segment)].copy()
        merged = _province_layer_with_data(province_layer, segment_summary, ["quantity"])
        merged.plot(
            column="quantity",
            ax=ax,
            cmap="PuBuGn" if segment == "Modern Trade" else "YlOrBr",
            linewidth=0.35,
            edgecolor="#1f2937",
            missing_kwds={"color": "#e5e7eb", "edgecolor": "#9ca3af", "hatch": "///"},
            legend=True,
            legend_kwds={"shrink": 0.7},
        )
        _style_map_axis(ax, segment)
        _add_top_labels(ax, merged, "province", "quantity", top_n=4)
    fig.suptitle(f"Q1.3 Province demand by customer segment\n{_window_label()}", y=0.98, fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q13_segment_geographic_maps.png", dpi=160)
    plt.close(fig)


def _vietnam_region_reference_map_chart(province_layer) -> None:
    fig, ax = plt.subplots(figsize=(8, 12))
    for region, color in REGION_COLOR_MAP.items():
        subset = province_layer[province_layer["region"].eq(region)]
        if subset.empty:
            continue
        subset.plot(ax=ax, color=color, edgecolor="#1e293b", linewidth=0.5)
    _style_map_axis(ax, "Vietnam macro-region reference map")
    from matplotlib.patches import Patch

    legend_items = [Patch(facecolor=color, edgecolor="#1e293b", label=region) for region, color in REGION_COLOR_MAP.items()]
    ax.legend(handles=legend_items, loc="lower left", frameon=True, fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q12_region_reference_map.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    from src.logage2026.config import CLEANED_DIR, TABLES_DIR

    print("Loading static cleaned data from disk...")
    try:
        shipments = pd.read_csv(CLEANED_DIR / "shipments_cleaned.csv")
        abc_xyz = pd.read_csv(TABLES_DIR / "q11_sku_abc_xyz.csv")
        abc_xyz_matrix = pd.read_csv(TABLES_DIR / "q11_abc_xyz_matrix_summary.csv")
        warehouse_region_summary = pd.read_csv(TABLES_DIR / "q12_warehouse_region_summary.csv")
        q12_region_orders_quantity_summary = pd.read_csv(TABLES_DIR / "q12_region_quantity_orders_summary.csv")
        q12_province_cluster_summary = pd.read_csv(TABLES_DIR / "q12_top_demand_provinces_summary.csv")
        q12_province_demand_summary = pd.read_csv(TABLES_DIR / "q12_province_demand_summary.csv")
        q12_province_warehouse_dominance_summary = pd.read_csv(TABLES_DIR / "q12_province_warehouse_dominance_summary.csv")
        q12_province_correlation_input_summary = pd.read_csv(TABLES_DIR / "q12_province_correlation_input_summary.csv")
        q12_urban_provincial_summary = pd.read_csv(TABLES_DIR / "q12_urban_provincial_summary.csv")
        q12_warehouse_imbalance_visual_summary = pd.read_csv(TABLES_DIR / "q12_warehouse_imbalance_visual_summary.csv")
        q13_segment_profile_summary = pd.read_csv(TABLES_DIR / "q13_segment_profile_summary.csv")
        q13_segment_packaging_summary = pd.read_csv(TABLES_DIR / "q13_segment_packaging_summary.csv")
        q13_segment_geographic_spread_summary = pd.read_csv(TABLES_DIR / "q13_segment_geographic_spread_summary.csv")
        q13_segment_province_spread_summary = pd.read_csv(TABLES_DIR / "q13_segment_province_spread_summary.csv")
        sku_master = pd.read_csv(CLEANED_DIR / "sku_master_cleaned.csv")

        shipments["created_date"] = pd.to_datetime(shipments["created_date"])

        print("Generating charts from static output...")
        save_charts(
            shipments,
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
        )
        print("Charts generated successfully!")
    except Exception as error:
        print(f"Error loading static output: {error}")
        print("Please run run_analysis.py first to generate the outputs.")
