import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from src.logage2026.config import (
    ASSIGNMENT_DOCUMENT_TYPES,
    ASSIGNMENT_END_DATE,
    ASSIGNMENT_START_DATE,
    FAST_MOVING_XYZ_FREQUENCY,
    FAST_MOVING_ABC_QUANTITY,
    Q11_ABC_A_THRESHOLD,
    Q11_ABC_B_THRESHOLD,
    Q11_DOCUMENT_TYPES,
    Q11_END_DATE,
    Q11_KEEP_MISSING_SKU_MASTER,
    Q11_START_DATE,
    Q11_VARIABILITY_GRAIN,
    Q11_VARIABILITY_PERIOD_END,
    Q11_VARIABILITY_PERIOD_START,
    Q11_XYZ_CV_X_MAX,
    Q11_XYZ_CV_Y_MAX,
    Q11_XYZ_MIN_NONZERO_PERIODS,
    WINSORIZE_LIMITS,
)
from src.logage2026.geography import region_group


ASSIGNMENT_START = pd.Timestamp(ASSIGNMENT_START_DATE)
ASSIGNMENT_END = pd.Timestamp(ASSIGNMENT_END_DATE)
Q11_START = pd.Timestamp(Q11_START_DATE)
Q11_END = pd.Timestamp(Q11_END_DATE)
Q11_VARIABILITY_START = pd.Timestamp(Q11_VARIABILITY_PERIOD_START)
Q11_VARIABILITY_END = pd.Timestamp(Q11_VARIABILITY_PERIOD_END)
URBAN_MUNICIPALITIES = {
    "Hồ Chí Minh",
    "Hà Nội",
    "Đà Nẵng",
    "Cần Thơ",
    "Hải Phòng",
}
SEGMENT_ORDER = ["Modern Trade", "Traditional Trade / Distributor"]


def classify_cumulative_share(
    share: float, a_threshold: float = Q11_ABC_A_THRESHOLD, b_threshold: float = Q11_ABC_B_THRESHOLD,
    labels: tuple[str, str, str] = ("A", "B", "C")
) -> str:
    if share <= a_threshold:
        return labels[0]
    if share <= b_threshold:
        return labels[1]
    return labels[2]


def classify_xyz(
    cv: float, x_max: float = Q11_XYZ_CV_X_MAX, y_max: float = Q11_XYZ_CV_Y_MAX
) -> str:
    if pd.isna(cv) or np.isinf(cv):
        return "Z"
    if cv <= x_max:
        return "X"
    if cv <= y_max:
        return "Y"
    return "Z"


def filter_assignment_shipments(
    shipments: pd.DataFrame,
    start_date: pd.Timestamp = ASSIGNMENT_START,
    end_date: pd.Timestamp = ASSIGNMENT_END,
    allowed_document_types: tuple[str, ...] = ASSIGNMENT_DOCUMENT_TYPES,
) -> pd.DataFrame:
    mask = shipments["analysis_document_flag"] & shipments["created_date"].between(start_date, end_date, inclusive="both")
    mask = mask & shipments["document_type"].isin(allowed_document_types)
    if "data_error_flag" in shipments.columns:
        mask = mask & ~shipments["data_error_flag"]
    return shipments.loc[mask].copy()


def filter_q11_shipments(
    shipments: pd.DataFrame,
    start_date: pd.Timestamp = Q11_START,
    end_date: pd.Timestamp = Q11_END,
    allowed_document_types: tuple[str, ...] = Q11_DOCUMENT_TYPES,
) -> pd.DataFrame:
    mask = shipments["created_date"].between(start_date, end_date, inclusive="both")
    mask = mask & shipments["document_type"].isin(allowed_document_types)
    if "data_error_flag" in shipments.columns:
        mask = mask & ~shipments["data_error_flag"]
    return shipments.loc[mask].copy()


def _winsorize_weekly(weekly: pd.DataFrame, limits: tuple[float, float] | None) -> pd.DataFrame:
    if limits is None:
        return weekly
    lower, upper = limits
    if not 0 <= lower < upper <= 1:
        raise ValueError("Winsorize limits must be between 0 and 1 with lower < upper")
    lower_bounds = weekly.quantile(lower, axis=1)
    upper_bounds = weekly.quantile(upper, axis=1)
    return weekly.clip(lower=lower_bounds, upper=upper_bounds, axis=0)


def _build_period_quantity_table(
    shipments: pd.DataFrame,
    grain: str = Q11_VARIABILITY_GRAIN,
    period_start: pd.Timestamp = Q11_VARIABILITY_START,
    period_end: pd.Timestamp = Q11_VARIABILITY_END,
) -> pd.DataFrame:
    if grain == "monthly":
        freq = "M"
    elif grain == "weekly":
        freq = "W"
    else:
        raise ValueError(f"Unsupported variability grain: {grain}")
    periods = pd.period_range(start=period_start, end=period_end, freq=freq).astype(str)
    periodized = (
        shipments.assign(period=shipments["created_date"].dt.to_period(freq).astype(str))
        .groupby(["sku_code", "period"])["quantity"]
        .sum()
        .unstack(fill_value=0)
    )
    return periodized.reindex(columns=periods, fill_value=0)


def build_abc_xyz(
    shipments: pd.DataFrame,
    sku_master: pd.DataFrame,
    variability_grain: str = Q11_VARIABILITY_GRAIN,
    variability_period_start: pd.Timestamp = Q11_VARIABILITY_START,
    variability_period_end: pd.Timestamp = Q11_VARIABILITY_END,
    min_nonzero_periods: int = Q11_XYZ_MIN_NONZERO_PERIODS,
    keep_missing_sku_master: bool = Q11_KEEP_MISSING_SKU_MASTER,
) -> pd.DataFrame:
    sku_master = sku_master.copy()
    required_sku_columns = [
        "product_name",
        "category",
        "pcs_per_carton",
        "pcs_per_pallet",
        "cbm_incl_flap_m3",
        "pcs_weight_kg",
        "carton_weight_kg",
    ]
    for column in required_sku_columns:
        if column not in sku_master.columns:
            sku_master[column] = pd.NA
    sku = shipments.groupby("sku_code").agg(
        quantity=("quantity", "sum"),
        order_frequency=("order_id", "nunique"),
        line_frequency=("sku_code", "size"),
        cbm_total=("cbm_total", "sum"),
    )
    period_quantities = _build_period_quantity_table(
        shipments,
        grain=variability_grain,
        period_start=variability_period_start,
        period_end=variability_period_end,
    )
    sku["variability_nonzero_periods"] = period_quantities.gt(0).sum(axis=1)
    winsorized = _winsorize_weekly(period_quantities, WINSORIZE_LIMITS)
    sku["variability_mean_quantity"] = winsorized.mean(axis=1)
    sku["variability_std_quantity"] = winsorized.std(axis=1)
    sku["demand_cv"] = sku["variability_std_quantity"] / sku["variability_mean_quantity"].replace(0, np.nan)
    sku["xyz_low_sample_flag"] = 0
    if min_nonzero_periods > 0:
        sku["xyz_low_sample_flag"] = sku["variability_nonzero_periods"].lt(min_nonzero_periods).astype(int)
    sku = sku.reset_index().sort_values("quantity", ascending=False)
    sku["quantity_share"] = sku["quantity"] / sku["quantity"].sum()
    sku["quantity_cumulative_share"] = sku["quantity_share"].cumsum()
    sku["abc_quantity"] = sku["quantity_cumulative_share"].map(classify_cumulative_share)

    sku = sku.sort_values("order_frequency", ascending=False)
    sku["frequency_share"] = sku["order_frequency"] / sku["order_frequency"].sum()
    sku["frequency_cumulative_share"] = sku["frequency_share"].cumsum()
    sku["xyz_frequency"] = sku["frequency_cumulative_share"].apply(
        lambda x: classify_cumulative_share(x, labels=("X", "Y", "Z"))
    )
    sku["abc_xyz_frequency"] = sku["abc_quantity"] + sku["xyz_frequency"]
    sku["xyz_volatility"] = sku["demand_cv"].map(classify_xyz)
    low_sample_mask = sku["xyz_low_sample_flag"].eq(1)
    sku.loc[low_sample_mask, "xyz_volatility"] = "Z"
    sku["abc_xyz_volatility"] = sku["abc_quantity"] + sku["xyz_volatility"]
    sku["fast_moving_flag"] = (
        sku["abc_quantity"].eq(FAST_MOVING_ABC_QUANTITY)
        & sku["xyz_frequency"].eq(FAST_MOVING_XYZ_FREQUENCY)
    ).astype(int)
    if not keep_missing_sku_master:
        sku = sku[sku["sku_code"].isin(set(sku_master["sku_code"].dropna()))].copy()
    sku = sku.merge(sku_master, on="sku_code", how="left")
    ordered_columns = [
        "sku_code",
        "product_name",
        "category",
        "quantity",
        "quantity_share",
        "quantity_cumulative_share",
        "abc_quantity",
        "order_frequency",
        "frequency_share",
        "frequency_cumulative_share",
        "variability_mean_quantity",
        "variability_std_quantity",
        "demand_cv",
        "variability_nonzero_periods",
        "xyz_low_sample_flag",
        "xyz_frequency",
        "abc_xyz_frequency",
        "xyz_volatility",
        "abc_xyz_volatility",
        "fast_moving_flag",
        "cbm_total",
        "pcs_per_carton",
        "pcs_per_pallet",
        "cbm_incl_flap_m3",
        "pcs_weight_kg",
        "carton_weight_kg",
    ]
    result = sku[ordered_columns].rename(
        columns={
            "variability_mean_quantity": f"{variability_grain}_mean_quantity",
            "variability_std_quantity": f"{variability_grain}_std_quantity",
            "variability_nonzero_periods": f"{variability_grain}_nonzero_periods",
        }
    )
    return result.sort_values(["abc_quantity", "xyz_frequency", "quantity"], ascending=[True, True, False])


def build_abc_xyz_matrix_summary(abc_xyz: pd.DataFrame, xyz_col: str = "xyz_frequency") -> pd.DataFrame:
    return (
        abc_xyz.groupby(["abc_quantity", xyz_col], dropna=False)
        .agg(
            sku_count=("sku_code", "nunique"),
            quantity=("quantity", "sum"),
            order_frequency=("order_frequency", "sum"),
            cbm_total=("cbm_total", "sum"),
        )
        .reset_index()
        .sort_values(["abc_quantity", xyz_col])
    )





def build_fast_moving_summary(abc_xyz: pd.DataFrame) -> pd.DataFrame:
    total_quantity = abc_xyz["quantity"].sum()
    total_frequency = abc_xyz["order_frequency"].sum()
    fast = abc_xyz[abc_xyz["fast_moving_flag"].eq(1)]
    summary = pd.DataFrame(
        [
            {
                "group": f"Fast Moving: ABC quantity {FAST_MOVING_ABC_QUANTITY} and XYZ frequency {FAST_MOVING_XYZ_FREQUENCY}",
                "sku_count": int(fast["sku_code"].nunique()),
                "quantity": fast["quantity"].sum(),
                "quantity_share": fast["quantity"].sum() / total_quantity if total_quantity else 0.0,
                "order_frequency": fast["order_frequency"].sum(),
                "frequency_share": fast["order_frequency"].sum() / total_frequency if total_frequency else 0.0,
                "top_skus": ", ".join(fast.sort_values("quantity", ascending=False)["sku_code"].head(10).astype(str)),
            }
        ]
    )
    return summary


def build_classification_metadata() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "q11_start_date": Q11_START.date().isoformat(),
                "q11_end_date": Q11_END.date().isoformat(),
                "q11_document_types": ",".join(Q11_DOCUMENT_TYPES),
                "q11_keep_missing_sku_master": int(Q11_KEEP_MISSING_SKU_MASTER),
                "q11_variability_grain": Q11_VARIABILITY_GRAIN,
                "q11_variability_period_start": Q11_VARIABILITY_START.date().isoformat(),
                "q11_variability_period_end": Q11_VARIABILITY_END.date().isoformat(),
                "abc_a_threshold": Q11_ABC_A_THRESHOLD,
                "abc_b_threshold": Q11_ABC_B_THRESHOLD,
                "fast_moving_xyz_frequency": FAST_MOVING_XYZ_FREQUENCY,
                "winsorize_limits": str(WINSORIZE_LIMITS),
            }
        ]
    )


def build_q11_monthly_demand_table(abc_xyz: pd.DataFrame, q11_shipments: pd.DataFrame) -> pd.DataFrame:
    monthly = _build_period_quantity_table(
        q11_shipments,
        grain="monthly",
        period_start=Q11_VARIABILITY_START,
        period_end=Q11_VARIABILITY_END,
    ).reset_index()
    monthly = monthly.rename(columns={column: pd.Period(column).strftime("%b-%y") for column in monthly.columns if column != "sku_code"})
    month_columns = [column for column in monthly.columns if column != "sku_code"]
    monthly["Total"] = monthly[month_columns].sum(axis=1)
    monthly["Mean/Mo"] = monthly[month_columns].mean(axis=1)
    monthly["Std Dev"] = monthly[month_columns].std(axis=1)
    monthly["CV"] = monthly["Std Dev"] / monthly["Mean/Mo"].replace(0, np.nan)
    merged = monthly.merge(
        abc_xyz[
            [
                "sku_code",
                "product_name",
                "category",
                "abc_quantity",
                "xyz_frequency",
                "abc_xyz_frequency",
                "xyz_volatility",
                "abc_xyz_volatility",
                "quantity",
                "order_frequency",
                "cbm_total",
                "quantity_share",
                "frequency_share",
            ]
        ],
        on="sku_code",
        how="left",
    )
    ordered_columns = [
        "sku_code",
        "product_name",
        "category",
        "abc_quantity",
        "xyz_frequency",
        "abc_xyz_frequency",
        "xyz_volatility",
        "abc_xyz_volatility",
        *month_columns,
        "Total",
        "Mean/Mo",
        "Std Dev",
        "CV",
        "quantity",
        "quantity_share",
        "order_frequency",
        "frequency_share",
        "cbm_total",
    ]
    return merged[ordered_columns].sort_values(["abc_quantity", "quantity"], ascending=[True, False])


def build_missing_data_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    summary = (
        shipments.groupby(["source_warehouse", "document_type"], dropna=False)
        .agg(
            shipment_rows=("sku_code", "size"),
            rows_missing_quantity=("quantity_missing_flag", "sum"),
            rows_missing_cbm=("cbm_missing_flag", "sum"),
            rows_missing_either=("data_error_flag", "sum"),
        )
        .reset_index()
    )
    summary["missing_row_share"] = summary["rows_missing_either"] / summary["shipment_rows"]
    total = pd.DataFrame(
        [
            {
                "source_warehouse": "All",
                "document_type": "All",
                "shipment_rows": int(summary["shipment_rows"].sum()),
                "rows_missing_quantity": int(summary["rows_missing_quantity"].sum()),
                "rows_missing_cbm": int(summary["rows_missing_cbm"].sum()),
                "rows_missing_either": int(summary["rows_missing_either"].sum()),
                "missing_row_share": summary["rows_missing_either"].sum()
                / summary["shipment_rows"].sum()
                if summary["shipment_rows"].sum()
                else 0.0,
            }
        ]
    )
    return pd.concat([summary, total], ignore_index=True, sort=False)


def build_geography_coverage_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    total_rows = len(shipments)
    total_quantity = shipments["quantity"].sum()
    known_rows = len(known)
    known_quantity = known["quantity"].sum()
    uniquely_matched_rows = int(shipments["geography_source"].eq("distributor_match").sum())
    parsed_rows = int(shipments["geography_source"].eq("transaction_text_parse").sum())
    unresolved_rows = int(shipments["geography_source"].eq("unresolved").sum())
    return pd.DataFrame(
        [
            {
                "assignment_start_date": ASSIGNMENT_START.date().isoformat(),
                "assignment_end_date": ASSIGNMENT_END.date().isoformat(),
                "shipment_rows_total": total_rows,
                "shipment_rows_known_geography": known_rows,
                "shipment_row_coverage": known_rows / total_rows if total_rows else 0.0,
                "shipment_rows_unknown_geography": total_rows - known_rows,
                "shipment_row_unknown_share": (total_rows - known_rows) / total_rows if total_rows else 0.0,
                "quantity_total": total_quantity,
                "quantity_known_geography": known_quantity,
                "quantity_coverage": known_quantity / total_quantity if total_quantity else 0.0,
                "quantity_unknown_geography": total_quantity - known_quantity,
                "quantity_unknown_share": (total_quantity - known_quantity) / total_quantity if total_quantity else 0.0,
                "orders_total": shipments["order_id"].nunique(),
                "orders_known_geography": known["order_id"].nunique(),
                "rows_distributor_match": uniquely_matched_rows,
                "rows_transaction_text_parse": parsed_rows,
                "rows_unresolved": unresolved_rows,
                "rows_ambiguous_customer": int(shipments["customer_match_status"].eq("ambiguous_multi_location_customer").sum()),
                "rows_unresolved_customer": int(
                    shipments["customer_match_status"].isin(["unmatched_customer_key", "missing_customer_name"]).sum()
                ),
            }
        ]
    )


def build_geography_diagnostics_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    unresolved = shipments[~shipments["known_geography_flag"]].copy()
    transaction_mask = shipments["geography_source"].eq("transaction_text_parse")
    return pd.DataFrame(
        [
            {
                "shipment_rows_total": len(shipments),
                "shipment_rows_known_geography": len(known),
                "shipment_rows_unknown_geography": len(unresolved),
                "rows_transaction_text_parse": int(transaction_mask.sum()),
                "rows_transaction_text_parse_alias_matched": int(
                    shipments.loc[transaction_mask, "province_alias_match_flag"].sum()
                ),
                "rows_with_distance_my_phuoc": int(
                    shipments["distance_from_my_phuoc_km"].notna().sum()
                ),
                "rows_with_distance_vinh_loc": int(
                    shipments["distance_from_vinh_loc_km"].notna().sum()
                ),
            }
        ]
    )


def build_unresolved_candidate_region_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    unresolved = shipments[~shipments["known_geography_flag"]].copy()
    if unresolved.empty:
        return pd.DataFrame(columns=["candidate_region", "shipment_rows"])
    unresolved["candidate_region"] = unresolved["parsed_province"].map(region_group)
    return (
        unresolved.groupby("candidate_region", dropna=False)
        .agg(shipment_rows=("sku_code", "size"))
        .reset_index()
        .sort_values("shipment_rows", ascending=False)
    )


def build_warehouse_region_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    return (
        known.groupby(["source_warehouse", "region", "province", "geography_source"], dropna=False)
        .agg(
            shipment_lines=("sku_code", "size"),
            orders=("order_id", "nunique"),
            customers=("customer_key", "nunique"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
        )
        .reset_index()
        .sort_values(["quantity", "orders"], ascending=False)
    )


def build_q12_region_orders_quantity_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    if known.empty:
        return pd.DataFrame(columns=["region", "shipment_lines", "orders", "customers", "quantity", "cbm_total"])
    return (
        known.groupby("region", dropna=False)
        .agg(
            shipment_lines=("sku_code", "size"),
            orders=("order_id", "nunique"),
            customers=("customer_key", "nunique"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
        )
        .reset_index()
        .sort_values(["quantity", "orders"], ascending=False)
    )


def build_q12_province_cluster_summary(shipments: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    if known.empty:
        return pd.DataFrame(
            columns=[
                "province",
                "shipment_lines",
                "orders",
                "customers",
                "quantity",
                "cbm_total",
                "my_phuoc_orders",
                "vinh_loc_orders",
                "my_phuoc_quantity",
                "vinh_loc_quantity",
                "my_phuoc_quantity_share",
                "vinh_loc_quantity_share",
                "dominant_warehouse",
                "rank_by_orders",
                "rank_by_quantity",
            ]
        )

    summary = (
        known.groupby("province", dropna=False)
        .agg(
            shipment_lines=("sku_code", "size"),
            orders=("order_id", "nunique"),
            customers=("customer_key", "nunique"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
        )
        .reset_index()
    )
    warehouse_orders = (
        known.groupby(["province", "source_warehouse"])["order_id"]
        .nunique()
        .unstack(fill_value=0)
        .rename(columns={"My Phuoc": "my_phuoc_orders", "Vinh Loc": "vinh_loc_orders"})
        .reset_index()
    )
    warehouse_quantity = (
        known.groupby(["province", "source_warehouse"])["quantity"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={"My Phuoc": "my_phuoc_quantity", "Vinh Loc": "vinh_loc_quantity"})
        .reset_index()
    )
    summary = summary.merge(warehouse_orders, on="province", how="left")
    summary = summary.merge(warehouse_quantity, on="province", how="left")
    for column in ["my_phuoc_orders", "vinh_loc_orders", "my_phuoc_quantity", "vinh_loc_quantity"]:
        if column not in summary.columns:
            summary[column] = 0.0
    summary["my_phuoc_quantity_share"] = np.where(
        summary["quantity"].gt(0), summary["my_phuoc_quantity"] / summary["quantity"], 0.0
    )
    summary["vinh_loc_quantity_share"] = np.where(
        summary["quantity"].gt(0), summary["vinh_loc_quantity"] / summary["quantity"], 0.0
    )
    summary["dominant_warehouse"] = np.where(
        summary["my_phuoc_quantity"].gt(summary["vinh_loc_quantity"]),
        "My Phuoc",
        np.where(summary["vinh_loc_quantity"].gt(summary["my_phuoc_quantity"]), "Vinh Loc", "Balanced"),
    )
    summary["rank_by_orders"] = summary["orders"].rank(method="first", ascending=False).astype(int)
    summary["rank_by_quantity"] = summary["quantity"].rank(method="first", ascending=False).astype(int)
    summary = summary[summary["rank_by_orders"].le(top_n) | summary["rank_by_quantity"].le(top_n)].copy()
    return summary.sort_values(["rank_by_orders", "rank_by_quantity", "province"])


def build_q12_province_demand_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    if known.empty:
        return pd.DataFrame(
            columns=[
                "province",
                "region",
                "shipment_lines",
                "orders",
                "customers",
                "quantity",
                "cbm_total",
                "quantity_rank",
                "orders_rank",
                "customers_rank",
            ]
        )
    summary = (
        known.groupby(["province", "region"], dropna=False)
        .agg(
            shipment_lines=("sku_code", "size"),
            orders=("order_id", "nunique"),
            customers=("customer_key", "nunique"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
        )
        .reset_index()
    )
    summary["quantity_rank"] = summary["quantity"].rank(method="first", ascending=False).astype(int)
    summary["orders_rank"] = summary["orders"].rank(method="first", ascending=False).astype(int)
    summary["customers_rank"] = summary["customers"].rank(method="first", ascending=False).astype(int)
    return summary.sort_values(["quantity_rank", "orders_rank", "province"])


def build_q12_province_warehouse_dominance_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    summary = build_q12_province_demand_summary(shipments)
    if summary.empty:
        return pd.DataFrame(
            columns=[
                "province",
                "region",
                "orders",
                "customers",
                "quantity",
                "my_phuoc_orders",
                "vinh_loc_orders",
                "my_phuoc_quantity",
                "vinh_loc_quantity",
                "my_phuoc_quantity_share",
                "vinh_loc_quantity_share",
                "quantity_share_gap",
                "dominance_intensity",
                "dominant_warehouse",
            ]
        )
    known = shipments[shipments["known_geography_flag"]].copy()
    warehouse_orders = (
        known.groupby(["province", "source_warehouse"])["order_id"]
        .nunique()
        .unstack(fill_value=0)
        .rename(columns={"My Phuoc": "my_phuoc_orders", "Vinh Loc": "vinh_loc_orders"})
        .reset_index()
    )
    warehouse_quantity = (
        known.groupby(["province", "source_warehouse"])["quantity"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={"My Phuoc": "my_phuoc_quantity", "Vinh Loc": "vinh_loc_quantity"})
        .reset_index()
    )
    summary = summary.merge(warehouse_orders, on="province", how="left")
    summary = summary.merge(warehouse_quantity, on="province", how="left")
    for column in ["my_phuoc_orders", "vinh_loc_orders", "my_phuoc_quantity", "vinh_loc_quantity"]:
        if column not in summary.columns:
            summary[column] = 0.0
    summary["my_phuoc_quantity_share"] = np.where(
        summary["quantity"].gt(0), summary["my_phuoc_quantity"] / summary["quantity"], 0.0
    )
    summary["vinh_loc_quantity_share"] = np.where(
        summary["quantity"].gt(0), summary["vinh_loc_quantity"] / summary["quantity"], 0.0
    )
    summary["quantity_share_gap"] = summary["my_phuoc_quantity_share"] - summary["vinh_loc_quantity_share"]
    summary["dominance_intensity"] = summary["quantity_share_gap"].abs()
    summary["dominant_warehouse"] = np.where(
        summary["quantity_share_gap"].gt(0),
        "My Phuoc",
        np.where(summary["quantity_share_gap"].lt(0), "Vinh Loc", "Balanced"),
    )
    return summary.sort_values(["dominance_intensity", "quantity", "province"], ascending=[False, False, True])


def build_q12_urban_provincial_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    if known.empty:
        return pd.DataFrame(
            columns=["geography_tier", "source_warehouse", "shipment_lines", "orders", "customers", "quantity", "cbm_total"]
        )
    known["geography_tier"] = np.where(known["province"].isin(URBAN_MUNICIPALITIES), "urban", "provincial")
    return (
        known.groupby(["geography_tier", "source_warehouse"], dropna=False)
        .agg(
            shipment_lines=("sku_code", "size"),
            orders=("order_id", "nunique"),
            customers=("customer_key", "nunique"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
        )
        .reset_index()
        .sort_values(["geography_tier", "quantity"], ascending=[True, False])
    )


def build_customer_cluster_summary(shipments: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    province_summary = (
        known.groupby("province", dropna=False)
        .agg(orders=("order_id", "nunique"), quantity=("quantity", "sum"))
        .reset_index()
        .rename(columns={"province": "geography_name"})
    )
    province_summary["geography_level"] = "province"

    combined = province_summary
    if combined.empty:
        return pd.DataFrame(
            columns=["geography_level", "geography_name", "orders", "quantity", "rank_by_orders", "rank_by_quantity"]
        )

    combined["rank_by_orders"] = combined.groupby("geography_level")["orders"].rank(method="first", ascending=False).astype(int)
    combined["rank_by_quantity"] = combined.groupby("geography_level")["quantity"].rank(method="first", ascending=False).astype(int)
    filtered = combined[combined["rank_by_orders"].le(top_n) | combined["rank_by_quantity"].le(top_n)].copy()
    keep = ["geography_level", "geography_name", "orders", "quantity", "rank_by_orders", "rank_by_quantity"]
    return filtered[keep].sort_values(["geography_level", "rank_by_orders", "rank_by_quantity", "geography_name"])


def build_warehouse_imbalance_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    summary = (
        known.groupby(["source_warehouse", "region"], dropna=False)
        .agg(
            orders=("order_id", "nunique"),
            shipment_lines=("sku_code", "size"),
            customers=("customer_key", "nunique"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
        )
        .reset_index()
    )
    if summary.empty:
        return summary

    # Calculate true unique orders per region directly from transactions to prevent double counting of split orders
    true_region_orders = known.groupby("region")["order_id"].nunique().rename("region_orders")
    summary = summary.merge(true_region_orders, on="region", how="left")

    region_quantity = summary.groupby("region")["quantity"].transform("sum")
    warehouse_orders = summary.groupby("source_warehouse")["orders"].transform("sum")
    warehouse_quantity = summary.groupby("source_warehouse")["quantity"].transform("sum")
    
    summary["region_order_share"] = summary["orders"] / summary["region_orders"]
    summary["region_quantity_share"] = summary["quantity"] / region_quantity
    summary["warehouse_order_share"] = summary["orders"] / warehouse_orders
    summary["warehouse_quantity_share"] = summary["quantity"] / warehouse_quantity
    
    summary = summary.drop(columns=["region_orders"])
    return summary.sort_values(["region", "quantity", "orders"], ascending=[True, False, False])


def build_q12_warehouse_imbalance_visual_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    summary = build_warehouse_imbalance_summary(shipments)
    if summary.empty:
        return pd.DataFrame(
            columns=[
                "region",
                "region_orders",
                "region_quantity",
                "my_phuoc_orders",
                "vinh_loc_orders",
                "my_phuoc_quantity",
                "vinh_loc_quantity",
                "my_phuoc_order_share",
                "vinh_loc_order_share",
                "my_phuoc_quantity_share",
                "vinh_loc_quantity_share",
                "quantity_share_gap",
                "dominant_warehouse",
                "dominant_warehouse_flag",
            ]
        )
    pivot = summary.pivot(index="region", columns="source_warehouse", values="orders").fillna(0)
    qty_pivot = summary.pivot(index="region", columns="source_warehouse", values="quantity").fillna(0)
    combined = pd.DataFrame({"region": sorted(summary["region"].unique())})
    combined["my_phuoc_orders"] = combined["region"].map(pivot.get("My Phuoc", pd.Series(dtype=float))).fillna(0)
    combined["vinh_loc_orders"] = combined["region"].map(pivot.get("Vinh Loc", pd.Series(dtype=float))).fillna(0)
    combined["my_phuoc_quantity"] = combined["region"].map(qty_pivot.get("My Phuoc", pd.Series(dtype=float))).fillna(0)
    combined["vinh_loc_quantity"] = combined["region"].map(qty_pivot.get("Vinh Loc", pd.Series(dtype=float))).fillna(0)
    combined["region_orders"] = combined["my_phuoc_orders"] + combined["vinh_loc_orders"]
    combined["region_quantity"] = combined["my_phuoc_quantity"] + combined["vinh_loc_quantity"]
    combined["my_phuoc_order_share"] = np.where(
        combined["region_orders"].gt(0), combined["my_phuoc_orders"] / combined["region_orders"], 0.0
    )
    combined["vinh_loc_order_share"] = np.where(
        combined["region_orders"].gt(0), combined["vinh_loc_orders"] / combined["region_orders"], 0.0
    )
    combined["my_phuoc_quantity_share"] = np.where(
        combined["region_quantity"].gt(0), combined["my_phuoc_quantity"] / combined["region_quantity"], 0.0
    )
    combined["vinh_loc_quantity_share"] = np.where(
        combined["region_quantity"].gt(0), combined["vinh_loc_quantity"] / combined["region_quantity"], 0.0
    )
    combined["quantity_share_gap"] = combined["my_phuoc_quantity_share"] - combined["vinh_loc_quantity_share"]
    combined["dominant_warehouse"] = np.where(
        combined["quantity_share_gap"].gt(0),
        "My Phuoc",
        np.where(combined["quantity_share_gap"].lt(0), "Vinh Loc", "Balanced"),
    )
    combined["dominant_warehouse_flag"] = combined["dominant_warehouse"].ne("Balanced").astype(int)
    return combined.sort_values(["region_quantity", "region_orders"], ascending=False)


def _calculate_packaging_components(known: pd.DataFrame, sku_master: pd.DataFrame) -> pd.DataFrame:
    missing_cols = [c for c in ["pcs_per_pallet", "pcs_per_carton"] if c not in known.columns]
    if missing_cols:
        sku_pkg = sku_master[["sku_code"] + missing_cols].copy()
        known = known.merge(sku_pkg, on="sku_code", how="left")

    qty = known["quantity"].fillna(0).astype(float)
    ppp = known["pcs_per_pallet"].astype(float).fillna(qty + 1.0)
    ppc = known["pcs_per_carton"].astype(float).fillna(qty + 1.0)

    has_pallet = known["pcs_per_pallet"].notna()
    pallet_qty = np.where(has_pallet & (qty >= ppp), (qty // ppp) * ppp, 0.0)
    rem_qty = np.where(has_pallet & (qty >= ppp), qty % ppp, qty)

    has_carton = known["pcs_per_carton"].notna()
    carton_qty = np.where(has_carton & (rem_qty >= ppc), (rem_qty // ppc) * ppc, 0.0)
    loose_qty = np.where(has_carton & (rem_qty >= ppc), rem_qty % ppc, rem_qty)

    known["pallet_qty"] = pallet_qty
    known["carton_qty"] = carton_qty
    known["loose_qty"] = loose_qty
    return known


def _prepare_segment_order_lines(shipments: pd.DataFrame, sku_master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    known = shipments[
        shipments["analysis_document_flag"] 
        & shipments["customer_segment"].isin(SEGMENT_ORDER)
        & shipments["known_geography_flag"]
    ].copy()
    known["distance_km"] = np.where(
        known["source_warehouse"] == "My Phuoc",
        known["distance_from_my_phuoc_km"],
        known["distance_from_vinh_loc_km"],
    )
    known = _calculate_packaging_components(known, sku_master)
    order_level = (
        known.groupby(["customer_segment", "order_id"], dropna=False)
        .agg(
            customer_key=("customer_key", "first"),
            source_warehouse=("source_warehouse", "first"),
            province=("province", "first"),
            region=("region", "first"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
            sku_breadth=("sku_code", "nunique"),
            line_count=("sku_code", "size"),
            distance_km=("distance_km", "mean"),
        )
        .reset_index()
    )
    return known, order_level


def build_q13_segment_profile_summary(shipments: pd.DataFrame, sku_master: pd.DataFrame) -> pd.DataFrame:
    known, order_level = _prepare_segment_order_lines(shipments, sku_master)
    if order_level.empty:
        return pd.DataFrame(
            columns=[
                "customer_segment",
                "orders",
                "customers",
                "avg_order_quantity",
                "avg_order_cbm",
                "avg_orders_per_customer_month",
                "avg_sku_breadth",
                "avg_lines_per_order",
                "province_count",
                "region_count",
                "top_province_quantity_share",
                "avg_distance_km",
            ]
        )
    summary = (
        order_level.groupby("customer_segment", dropna=False)
        .agg(
            orders=("order_id", "nunique"),
            customers=("customer_key", "nunique"),
            avg_order_quantity=("quantity", "mean"),
            median_order_quantity=("quantity", "median"),
            avg_order_cbm=("cbm_total", "mean"),
            median_order_cbm=("cbm_total", "median"),
            avg_sku_breadth=("sku_breadth", "mean"),
            avg_lines_per_order=("line_count", "mean"),
            avg_distance_km=("distance_km", "mean"),
        )
        .reset_index()
    )
    customer_orders = order_level.groupby(["customer_segment", "customer_key"], dropna=False)["order_id"].nunique().reset_index()
    customer_orders["orders_per_month"] = customer_orders["order_id"] / 6.0
    avg_freq = customer_orders.groupby("customer_segment", dropna=False)["orders_per_month"].mean().rename(
        "avg_orders_per_customer_month"
    )
    geography = build_q13_segment_geographic_spread_summary(shipments)
    summary = summary.merge(avg_freq.reset_index(), on="customer_segment", how="left")
    summary = summary.merge(
        geography[["customer_segment", "province_count", "region_count", "top_province_quantity_share"]],
        on="customer_segment",
        how="left",
    )
    return summary.sort_values("customer_segment")


def build_q13_segment_packaging_summary(shipments: pd.DataFrame, sku_master: pd.DataFrame) -> pd.DataFrame:
    known, _ = _prepare_segment_order_lines(shipments, sku_master)
    if known.empty:
        return pd.DataFrame(columns=["customer_segment", "packaging_unit", "quantity", "quantity_share"])
    pkg = (
        known.groupby("customer_segment", dropna=False)[["pallet_qty", "carton_qty", "loose_qty", "quantity"]]
        .sum()
        .reset_index()
    )
    rows: list[dict[str, object]] = []
    for _, row in pkg.iterrows():
        total_quantity = float(row["quantity"])
        for packaging_unit, column in [
            ("pallet", "pallet_qty"),
            ("carton", "carton_qty"),
            ("loose", "loose_qty"),
        ]:
            quantity = float(row[column])
            rows.append(
                {
                    "customer_segment": row["customer_segment"],
                    "packaging_unit": packaging_unit,
                    "quantity": quantity,
                    "quantity_share": quantity / total_quantity if total_quantity else 0.0,
                }
            )
    return pd.DataFrame(rows).sort_values(["customer_segment", "packaging_unit"])


def build_q13_segment_geographic_spread_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[
        shipments["analysis_document_flag"]
        & shipments["customer_segment"].isin(SEGMENT_ORDER)
        & shipments["known_geography_flag"]
    ].copy()
    if known.empty:
        return pd.DataFrame(
            columns=["customer_segment", "province_count", "region_count", "top_province", "top_province_quantity_share"]
        )
    province_summary = (
        known.groupby(["customer_segment", "province"], dropna=False)
        .agg(quantity=("quantity", "sum"))
        .reset_index()
    )
    province_summary["province_rank"] = province_summary.groupby("customer_segment")["quantity"].rank(
        method="first", ascending=False
    )
    top_province = province_summary[province_summary["province_rank"].eq(1)].rename(columns={"province": "top_province"})
    total_quantity = known.groupby("customer_segment", dropna=False)["quantity"].sum().rename("segment_quantity")
    top_province = top_province.merge(total_quantity.reset_index(), on="customer_segment", how="left")
    top_province["top_province_quantity_share"] = np.where(
        top_province["segment_quantity"].gt(0), top_province["quantity"] / top_province["segment_quantity"], 0.0
    )
    spread = (
        known.groupby("customer_segment", dropna=False)
        .agg(province_count=("province", "nunique"), region_count=("region", "nunique"))
        .reset_index()
    )
    spread = spread.merge(
        top_province[["customer_segment", "top_province", "top_province_quantity_share"]],
        on="customer_segment",
        how="left",
    )
    return spread.sort_values("customer_segment")


def build_q13_segment_province_spread_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[
        shipments["analysis_document_flag"]
        & shipments["customer_segment"].isin(SEGMENT_ORDER)
        & shipments["known_geography_flag"]
    ].copy()
    if known.empty:
        return pd.DataFrame(
            columns=["customer_segment", "province", "region", "orders", "customers", "quantity", "cbm_total"]
        )
    return (
        known.groupby(["customer_segment", "province", "region"], dropna=False)
        .agg(
            orders=("order_id", "nunique"),
            customers=("customer_key", "nunique"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
        )
        .reset_index()
        .sort_values(["customer_segment", "quantity", "orders", "province"], ascending=[True, False, False, True])
    )


def build_q12_province_correlation_input_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[shipments["analysis_document_flag"] & shipments["known_geography_flag"]].copy()
    if known.empty:
        return pd.DataFrame(
            columns=[
                "province",
                "region",
                "orders",
                "customers",
                "quantity",
                "cbm_total",
                "avg_distance_km",
                "avg_order_quantity",
                "avg_order_cbm",
                "avg_sku_breadth",
            ]
        )
    known["distance_km"] = np.where(
        known["source_warehouse"] == "My Phuoc",
        known["distance_from_my_phuoc_km"],
        known["distance_from_vinh_loc_km"],
    )
    order_level = (
        known.groupby(["province", "region", "order_id"], dropna=False)
        .agg(
            customer_key=("customer_key", "first"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
            sku_breadth=("sku_code", "nunique"),
            distance_km=("distance_km", "mean"),
        )
        .reset_index()
    )
    summary = (
        order_level.groupby(["province", "region"], dropna=False)
        .agg(
            orders=("order_id", "nunique"),
            customers=("customer_key", "nunique"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
            avg_distance_km=("distance_km", "mean"),
            avg_order_quantity=("quantity", "mean"),
            avg_order_cbm=("cbm_total", "mean"),
            avg_sku_breadth=("sku_breadth", "mean"),
        )
        .reset_index()
    )
    return summary.sort_values(["quantity", "orders", "province"], ascending=[False, False, True])


def build_order_profile_segments(shipments: pd.DataFrame, sku_master: pd.DataFrame) -> pd.DataFrame:
    summary = build_q13_segment_profile_summary(shipments, sku_master)
    packaging = build_q13_segment_packaging_summary(shipments, sku_master)
    if summary.empty:
        return pd.DataFrame(
            columns=[
                "customer_segment",
                "orders",
                "customers",
                "provinces",
                "avg_order_quantity",
                "median_order_quantity",
                "avg_order_cbm",
                "median_order_cbm",
                "avg_sku_breadth",
                "avg_lines_per_order",
                "avg_distance_km",
                "segment_sku_breadth",
                "pallet_qty_share",
                "carton_qty_share",
                "loose_qty_share",
                "avg_orders_per_customer_month",
                "province_count",
                "region_count",
                "top_province_quantity_share",
            ]
        )
    pkg_pivot = packaging.pivot(index="customer_segment", columns="packaging_unit", values="quantity_share").fillna(0)
    pkg_pivot = pkg_pivot.rename(
        columns={
            "pallet": "pallet_qty_share",
            "carton": "carton_qty_share",
            "loose": "loose_qty_share",
        }
    )
    segment_sku = (
        shipments[shipments["analysis_document_flag"] & shipments["customer_segment"].isin(SEGMENT_ORDER)]
        .groupby("customer_segment", dropna=False)["sku_code"]
        .nunique()
        .rename("segment_sku_breadth")
    )
    result = summary.copy()
    result = result.merge(segment_sku.reset_index(), on="customer_segment", how="left")
    result = result.merge(pkg_pivot.reset_index(), on="customer_segment", how="left")
    result["provinces"] = result["province_count"]
    return result.sort_values("customer_segment")


def build_document_type_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    return (
        shipments.groupby(["document_type", "analysis_document_flag", "exclusion_reason"], dropna=False)
        .agg(
            shipment_rows=("sku_code", "size"),
            orders=("order_id", "nunique"),
            quantity=("quantity", "sum"),
            cbm_total=("cbm_total", "sum"),
        )
        .reset_index()
        .sort_values(["analysis_document_flag", "shipment_rows", "document_type"], ascending=[False, False, True])
    )


def build_customer_match_quality_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    return (
        shipments.groupby("customer_match_status", dropna=False)
        .agg(
            shipment_rows=("sku_code", "size"),
            orders=("order_id", "nunique"),
            customers=("customer_key", "nunique"),
            quantity=("quantity", "sum"),
        )
        .reset_index()
        .sort_values(["shipment_rows", "quantity"], ascending=False)
    )


def build_geography_source_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    total_rows = len(shipments)
    total_quantity = shipments["quantity"].sum()
    summary = (
        shipments.groupby("geography_source", dropna=False)
        .agg(
            shipment_rows=("sku_code", "size"),
            orders=("order_id", "nunique"),
            quantity=("quantity", "sum"),
        )
        .reset_index()
    )
    summary["row_share"] = summary["shipment_rows"] / total_rows if total_rows else 0.0
    summary["quantity_share"] = summary["quantity"] / total_quantity if total_quantity else 0.0
    return summary.sort_values(["shipment_rows", "quantity"], ascending=False)


def build_unresolved_customer_summary(shipments: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    unresolved = shipments[
        shipments["customer_match_status"].isin(["ambiguous_multi_location_customer", "unmatched_customer_key", "missing_customer_name"])
    ].copy()
    if unresolved.empty:
        return pd.DataFrame(columns=["ship_to_customer", "customer_key", "customer_match_status", "shipment_rows", "orders", "quantity"])
    return (
        unresolved.groupby(["ship_to_customer", "customer_key", "customer_match_status"], dropna=False)
        .agg(
            shipment_rows=("sku_code", "size"),
            orders=("order_id", "nunique"),
            quantity=("quantity", "sum"),
        )
        .reset_index()
        .sort_values(["shipment_rows", "quantity"], ascending=False)
        .head(top_n)
    )


def build_safety_stock_class_a(shipments: pd.DataFrame, abc_xyz: pd.DataFrame) -> pd.DataFrame:
    class_a = set(abc_xyz.loc[abc_xyz["abc_quantity"].eq("A"), "sku_code"])
    weekly = (
        shipments[shipments["sku_code"].isin(class_a)]
        .assign(week=shipments["created_date"].dt.to_period("W").astype(str))
        .groupby(["sku_code", "week"])["quantity"]
        .sum()
        .unstack(fill_value=0)
    )
    weeks = pd.period_range(start=ASSIGNMENT_START, end=ASSIGNMENT_END, freq="W").astype(str)
    weekly = weekly.reindex(columns=weeks, fill_value=0)
    table = pd.DataFrame(
        {
            "sku_code": weekly.index,
            "weekly_mean_demand": weekly.mean(axis=1).values,
            "weekly_std_demand": weekly.std(axis=1).values,
        }
    )
    table["service_level_z"] = 1.65
    table["assumed_lead_time_weeks"] = 1.0
    table["safety_stock_units"] = (
        table["service_level_z"] * table["weekly_std_demand"] * np.sqrt(table["assumed_lead_time_weeks"])
    )
    table = table.merge(
        abc_xyz[["sku_code", "product_name", "category", "abc_quantity", "xyz_frequency", "quantity"]],
        on="sku_code",
        how="left",
    )
    return table.sort_values("safety_stock_units", ascending=False)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    
    try:
        from src.logage2026.loading import load_sku_master, load_transactions, load_distributors, load_segment_overrides
        from src.logage2026.cleaning import clean_sku_master, clean_distributors, clean_shipments
    except ImportError:
        from loading import load_sku_master, load_transactions, load_distributors, load_segment_overrides
        from cleaning import clean_sku_master, clean_distributors, clean_shipments
        
    print("Loading raw datasets...")
    sku_raw = load_sku_master()
    tx_raw = load_transactions()
    dist_raw = load_distributors()
    overrides = load_segment_overrides()
    
    print("Cleaning datasets...")
    sku_master = clean_sku_master(sku_raw)
    distributors = clean_distributors(dist_raw)
    shipments = clean_shipments(tx_raw, distributors, segment_overrides=overrides)
    
    print("Running classification...")
    q11_shipments = filter_q11_shipments(shipments)
    abc_xyz = build_abc_xyz(q11_shipments, sku_master)
    print(f"Classification completed. Total unique SKUs classified: {abc_xyz['sku_code'].nunique()}")
    print("\nABC Quantity Class counts:")
    print(abc_xyz["abc_quantity"].value_counts())
    print("\nXYZ Demand Variability Class counts:")
    print(abc_xyz["xyz"].value_counts())
