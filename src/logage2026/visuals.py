import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import os
import unicodedata
from pathlib import Path

mpl_config_dir = Path(__file__).resolve().parents[2] / "outputs" / ".matplotlib"
mpl_config_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(mpl_config_dir))

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
    abc_xyz_matrix_frequency: pd.DataFrame,
    abc_xyz_matrix_volatility: pd.DataFrame,
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
    safety_stock_class_a: pd.DataFrame,
    lead_time_sensitivity: pd.DataFrame,
    inventory_pooling_summary: pd.DataFrame,
    hcm_district_summary: pd.DataFrame,
    network_model_evaluation: pd.DataFrame,
    q21_channel_flow_summary: pd.DataFrame,
) -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    province_layer = _prepare_vietnam_province_layer()

    _abc_bar(abc_xyz)
    _abc_frequency_bar(abc_xyz)
    _abc_xyz_matrix_chart(abc_xyz_matrix_frequency, title_suffix="Frequency", save_suffix="frequency")
    _abc_xyz_matrix_chart(abc_xyz_matrix_volatility, title_suffix="Volatility", save_suffix="volatility")
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
    
    _q22_lead_time_sensitivity_chart(lead_time_sensitivity)
    _q22_inventory_pooling_chart(inventory_pooling_summary)
    _q21_hcm_district_chart(hcm_district_summary)
    _q21_network_coverage_chart(network_model_evaluation)
    _q21_channel_flow_chart(q21_channel_flow_summary)


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


def _abc_frequency_bar(abc_xyz: pd.DataFrame) -> None:
    chart = abc_xyz.groupby("abc_frequency")["order_frequency"].sum().reindex(["A", "B", "C"])
    fig, ax = plt.subplots(figsize=(8, 4))
    chart.plot(kind="bar", color="#fb8500", ax=ax, edgecolor="black")
    ax.set_title(f"Order Frequency Distribution by ABC Frequency Class\n{_window_label()}")
    ax.set_xlabel("ABC Frequency Class")
    ax.set_ylabel("Total Order Frequency")
    ax.set_xticklabels(chart.index, rotation=0)
    for p in ax.patches:
        ax.annotate(
            f"{int(p.get_height()):,}",
            (p.get_x() + p.get_width() / 2.0, p.get_height()),
            ha="center",
            va="bottom",
        )
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "q11_abc_frequency_distribution.png", dpi=160)
    plt.close(fig)


def _abc_xyz_matrix_chart(abc_xyz_matrix: pd.DataFrame, title_suffix="Frequency", save_suffix="frequency") -> None:
    if save_suffix == "frequency":
        cols = ["A", "B", "C"]
        title = "ABC-Frequency SKU Count Matrix"
        xlabel = "ABC frequency class"
    else:
        cols = ["X", "Y", "Z"]
        title = "ABC-Volatility SKU Count Matrix"
        xlabel = "XYZ volatility class"
        
    pivot = (
        abc_xyz_matrix.pivot(index="abc_quantity", columns=abc_xyz_matrix.columns[1], values="sku_count")
        .reindex(index=["A", "B", "C"], columns=cols)
        .fillna(0)
    )
    fig, ax = plt.subplots(figsize=(6, 4.5))
    image = ax.imshow(pivot.values, cmap="YlGnBu")
    ax.set_title(f"{title}\n{_window_label()}")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("ABC quantity class")
    ax.set_xticks(range(len(pivot.columns)), labels=pivot.columns)
    ax.set_yticks(range(len(pivot.index)), labels=pivot.index)
    for row_idx, row_label in enumerate(pivot.index):
        for col_idx, col_label in enumerate(pivot.columns):
            ax.text(col_idx, row_idx, f"{int(pivot.loc[row_label, col_label])}", ha="center", va="center", color="#102a43")
    fig.colorbar(image, ax=ax, shrink=0.85, label="SKU count")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / f"q11_abc_xyz_matrix_{save_suffix}.png", dpi=160)
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
        ("avg_order_cbm", "Avg order size (m³)", "#d29d3d"),
        ("normalized_frequency_7m", "7-Month Normalized Freq", "#6366f1"),
        ("active_month_frequency", "Active Month Avg Freq", "#8b5cf6"),
        ("avg_sku_breadth", "SKU breadth / order", "#b45f3c"),
        ("province_count", "Province count", "#4f7cac"),
        ("top_province_quantity_share", "Top-province quantity share", "#0f766e"),
        ("avg_distance_km", "Avg distance to warehouse (km proxy)", "#ec4899"),
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


def _q22_lead_time_sensitivity_chart(df: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))
    plt.plot(df['lead_time_days'], df['total_safety_stock'], marker='o', color='#1d4ed8', linewidth=2)
    plt.title("Q2.2 Lead Time Sensitivity on Class A Safety Stock")
    plt.xlabel("Assumed Lead Time (Days)")
    plt.ylabel("Total Safety Stock (Units)")
    plt.grid(axis='y', alpha=0.3)
    for idx, row in df.iterrows():
        plt.text(row['lead_time_days'], row['total_safety_stock'] + df['total_safety_stock'].max()*0.02, 
                 f"{row['total_safety_stock']:,.0f}", ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "q22_lead_time_sensitivity.png", dpi=150)
    plt.close()


def _q22_inventory_pooling_chart(df: pd.DataFrame) -> None:
    plt.figure(figsize=(7, 5))
    bars = plt.bar(df['scenario'], df['total_ss'], color=['#b45309', '#1d4ed8'])
    plt.title("Q2.2 Inventory Pooling Impact on Safety Stock")
    plt.ylabel("Total Safety Stock (Units)")
    plt.ylim(0, df['total_ss'].max() * 1.2)
    
    for i, bar in enumerate(bars):
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + df['total_ss'].max()*0.02, 
                 f"{yval:,.0f}", ha='center', va='bottom', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "q22_inventory_pooling.png", dpi=150)
    plt.close()


def _q21_hcm_district_chart(df: pd.DataFrame) -> None:
    if df.empty:
        return
    plt.figure(figsize=(10, 6))
    top_districts = df.sort_values('quantity', ascending=False).head(10)
    
    bars = plt.barh(top_districts['district'][::-1], top_districts['quantity'][::-1], color='#0f766e')
    plt.title("Top HCM Districts by B2B Quantity (Q2.1)")
    plt.xlabel("Total Quantity (Units)")
    
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2, f" {width:,.0f}", ha='left', va='center', fontsize=9)
        
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "q21_hcm_district_volume.png", dpi=150)
    plt.close()


def _q21_network_coverage_chart(df: pd.DataFrame) -> None:
    """Two-panel Q2.1 chart: district distance bar + volume vs distance scatter."""
    if df.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    colors = ["#16a34a" if s == "Adequate" else "#dc2626" for s in df["sla_status"]]

    # Left: horizontal bar — distance to nearest warehouse
    ax = axes[0]
    bars = ax.barh(df["district"][::-1], df["best_rdc_km"][::-1], color=colors[::-1])
    ax.axvline(25, color="#1d4ed8", linestyle="--", linewidth=1.5, label="25 km SLA threshold")
    ax.set_xlabel("Distance to Nearest Warehouse (km)")
    ax.set_title("Q2.1 District Distance to Nearest Warehouse")
    ax.legend(fontsize=9)
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.3, bar.get_y() + bar.get_height() / 2, f"{w:.1f} km", va="center", fontsize=8)

    # Right: scatter — B2B volume vs distance, sized by order count
    ax2 = axes[1]
    adequate = df[df["sla_status"] == "Adequate"]
    needs_ds = df[df["sla_status"] == "Needs Dark Store"]
    ax2.scatter(adequate["best_rdc_km"], adequate["quantity"],
                s=adequate["orders"] * 2, color="#16a34a", alpha=0.75, label="Adequate")
    ax2.scatter(needs_ds["best_rdc_km"], needs_ds["quantity"],
                s=needs_ds["orders"] * 2, color="#dc2626", alpha=0.75, label="Needs Dark Store")
    for _, row in df.iterrows():
        ax2.annotate(row["district"], (row["best_rdc_km"], row["quantity"]),
                     textcoords="offset points", xytext=(4, 3), fontsize=7)
    ax2.axvline(25, color="#1d4ed8", linestyle="--", linewidth=1.5, label="25 km threshold")
    ax2.set_xlabel("Distance to Nearest Warehouse (km)")
    ax2.set_ylabel("B2B Quantity (Units)")
    ax2.set_title("Q2.1 B2B Volume vs Warehouse Distance")
    ax2.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "q21_network_coverage.png", dpi=150)
    plt.close()


def _q21_channel_flow_chart(df: pd.DataFrame) -> None:
    """Q2.1 warehouse x channel flow KPI chart — per-day rates, timeline-normalized.

    My Phuoc ran Jun-Nov 2025 (6 months); Vinh Loc ran Dec 2025 only (1 month).
    Raw order counts are not directly comparable, so panel 1 uses avg_orders_per_day.
    """
    if df.empty:
        return

    fig, axes = plt.subplots(1, 3, figsize=(16, 7))
    fig.suptitle(
        "Q2.1 Warehouse × Channel Flow Profile\n"
        "Note: My Phuoc = Jun–Nov 2025 (6 months) | Vinh Loc = Dec 2025 only (1 month)",
        fontsize=13, fontweight="bold", y=1.02
    )

    PALETTE = {"B2B": "#0f766e", "B2C": "#d97706"}
    WH_ORDER = ["My Phuoc", "Vinh Loc"]

    # Period labels for x-axis annotation
    PERIOD_LABELS = {
        "My Phuoc": "Jun–Nov 2025\n(6 months)",
        "Vinh Loc": "Dec 2025\n(1 month)",
    }

    def _bar_group(ax, metric, ylabel, title, fmt="{:.1f}"):
        b2b = df[df["channel"] == "B2B"].set_index("warehouse")[metric].reindex(WH_ORDER)
        b2c = df[df["channel"] == "B2C"].set_index("warehouse")[metric].reindex(WH_ORDER)
        x = np.arange(len(WH_ORDER))
        w = 0.35
        bars_b2b = ax.bar(x - w / 2, b2b, w, label="B2B", color=PALETTE["B2B"])
        bars_b2c = ax.bar(x + w / 2, b2c, w, label="B2C", color=PALETTE["B2C"])
        ax.set_xticks(x)
        ax.set_xticklabels(
            [f"{wh}\n{PERIOD_LABELS.get(wh, '')}" for wh in WH_ORDER],
            fontsize=8.5
        )
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.legend(fontsize=8)
        for bar in list(bars_b2b) + list(bars_b2c):
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h, fmt.format(h),
                        ha="center", va="bottom", fontsize=8)

    # Panel 1: avg orders per active day (fair cross-warehouse comparison)
    avg_col = "avg_orders_per_day" if "avg_orders_per_day" in df.columns else "orders"
    _bar_group(axes[0], avg_col, "Orders / Active Day", "Avg Daily Orders\n(normalized per warehouse period)", "{:.1f}")

    # Panel 2: avg CBM per order
    _bar_group(axes[1], "avg_cbm_per_order", "Avg CBM / Order", "Avg CBM per Order\n(order size proxy)", "{:.3f}")

    # Panel 3: volatility index
    _bar_group(axes[2], "volatility_index", "Volatility Index\n(Peak ÷ P95)", "Demand Volatility Index\n(higher = more erratic)", "{:.2f}")

    # Annotate flow-type labels inside bars area
    for ax in axes:
        for wh_idx, wh in enumerate(WH_ORDER):
            for ch_idx, ch in enumerate(["B2B", "B2C"]):
                sub = df[(df["warehouse"] == wh) & (df["channel"] == ch)]
                if sub.empty:
                    continue
                flow = sub.iloc[0]["flow_type"]
                x_pos = wh_idx + (ch_idx - 0.5) * 0.35
                ax.text(x_pos, -0.14, flow.replace(" flow", ""),
                        transform=ax.get_xaxis_transform(), ha="center",
                        va="top", fontsize=6.5, color="#475569", style="italic")

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "q21_channel_flow_profile.png", dpi=150, bbox_inches="tight")
    plt.close()


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




def save_q31_u_shape_heatmap() -> None:
    """Extract the U-shaped warehouse heatmap from the reference Excel file."""
    import openpyxl
    from pathlib import Path
    ref_path = Path(__file__).resolve().parents[2] / "references" / "LOGage2026_Part3_Complete.xlsx"
    wb = openpyxl.load_workbook(ref_path)
    ws = wb["Q3.1 Heatmap (U-shape)"]
    img_data = ws._images[0]._data()
    out_path = CHARTS_DIR / "q31_u_shape_heatmap.png"
    out_path.write_bytes(img_data)
    print(f"Extracted reference heatmap to {out_path.name}")


def save_q32_flowchart_image() -> None:
    """Extract the pick-and-pack decision flowchart from the reference Excel file."""
    import openpyxl
    from pathlib import Path
    ref_path = Path(__file__).resolve().parents[2] / "references" / "LOGage2026_Part3_Complete.xlsx"
    wb = openpyxl.load_workbook(ref_path)
    ws = wb["Q3.2 Pick & Pack"]
    img_data = ws._images[0]._data()
    out_path = CHARTS_DIR / "q32_pick_pack_flowchart.png"
    out_path.write_bytes(img_data)
    print(f"Extracted reference flowchart to {out_path.name}")


if __name__ == "__main__":

    from src.logage2026.config import CLEANED_DIR, TABLES_DIR

    print("Loading static cleaned data from disk...")
    try:
        shipments = pd.read_csv(CLEANED_DIR / "shipments_cleaned.csv")
        abc_xyz = pd.read_csv(TABLES_DIR / "q11_sku_abc_xyz.csv")
        abc_xyz_matrix_frequency = pd.read_csv(TABLES_DIR / "q11_abc_xyz_matrix_frequency_summary.csv")
        abc_xyz_matrix_volatility = pd.read_csv(TABLES_DIR / "q11_abc_xyz_matrix_volatility_summary.csv")
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
            abc_xyz_matrix_frequency,
            abc_xyz_matrix_volatility,
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
