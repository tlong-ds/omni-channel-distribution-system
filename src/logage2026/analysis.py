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
    sku["abc_frequency"] = sku["frequency_cumulative_share"].apply(
        lambda x: classify_cumulative_share(x, labels=("A", "B", "C"))
    )
    sku["abc_frequency_matrix"] = sku["abc_quantity"] + sku["abc_frequency"]
    sku["xyz_volatility"] = sku["demand_cv"].map(classify_xyz)
    low_sample_mask = sku["xyz_low_sample_flag"].eq(1)
    sku.loc[low_sample_mask, "xyz_volatility"] = "Z"
    sku["abc_xyz_volatility"] = sku["abc_quantity"] + sku["xyz_volatility"]
    sku["fast_moving_flag"] = (
        sku["abc_quantity"].eq("A")
        & sku["abc_frequency"].eq("A")
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
        "abc_frequency",
        "abc_frequency_matrix",
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
    return result.sort_values(["abc_quantity", "abc_frequency", "quantity"], ascending=[True, True, False])


def build_abc_xyz_matrix_summary(abc_xyz: pd.DataFrame, xyz_col: str = "abc_frequency") -> pd.DataFrame:
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
                "group": "Fast Moving Class AA: ABC quantity A and ABC frequency A",
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
                "abc_frequency",
                "abc_frequency_matrix",
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
        "abc_frequency",
        "abc_frequency_matrix",
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
                "normalized_frequency_7m",
                "active_month_frequency",
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
    true_customers = known.groupby("customer_segment", dropna=False)["customer_key"].nunique().rename("customers")
    summary = summary.merge(true_customers.reset_index(), on="customer_segment", how="left")
    summary = summary[[
        "customer_segment",
        "orders",
        "customers",
        "avg_order_quantity",
        "median_order_quantity",
        "avg_order_cbm",
        "median_order_cbm",
        "avg_sku_breadth",
        "avg_lines_per_order",
        "avg_distance_km"
    ]]

    # New frequency calculations
    known_freq = known.copy()
    known_freq["year_month"] = known_freq["created_date"].dt.strftime("%Y-%m")
    customer_stats = known_freq.groupby(["customer_segment", "customer_key"], dropna=False).agg(
        active_months=("year_month", "nunique"),
        order_count=("order_id", "nunique")
    ).reset_index()
    customer_stats["orders_per_month"] = customer_stats["order_count"] / 7.0
    customer_stats["normalized_frequency_7m"] = customer_stats["order_count"] / 7.0
    customer_stats["active_month_frequency"] = customer_stats["order_count"] / customer_stats["active_months"]

    segment_averages = customer_stats.groupby("customer_segment", dropna=False).agg(
        avg_orders_per_customer_month=("orders_per_month", "mean"),
        normalized_frequency_7m=("normalized_frequency_7m", "mean"),
        active_month_frequency=("active_month_frequency", "mean")
    ).reset_index()

    geography = build_q13_segment_geographic_spread_summary(shipments)
    summary = summary.merge(segment_averages, on="customer_segment", how="left")
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


# Mile-weighted average lead time constants (RDC in Đông Nam Bộ → 6 regions).
# Source: GHN / VTP / GHTK standard transit benchmarks; weights = order counts
# from the transaction log (Jun–Dec 2025, A/R INVOICE, both warehouses).
_REGIONAL_LT_DATA: list[tuple[str, float, int]] = [
    # (region_name, lead_time_days, order_count)
    ("Đông Nam Bộ",                                    1.0, 2614),
    ("Bắc Trung Bộ và Duyên hải miền Trung",           3.0, 1027),
    ("Đồng bằng sông Cửu Long",                        2.0,  800),
    ("Đồng bằng sông Hồng",                            4.0,  503),
    ("Tây Nguyên",                                      2.0,  247),
    ("Trung du và miền núi phía Bắc",                  4.0,  143),
]


def _compute_mile_weighted_lt() -> float:
    """Return the order-count–weighted average lead time (days) across all regions."""
    total_orders = sum(orders for _, _, orders in _REGIONAL_LT_DATA)
    return sum(lt * orders for _, lt, orders in _REGIONAL_LT_DATA) / total_orders


def build_safety_stock_class_a(shipments: pd.DataFrame, abc_xyz: pd.DataFrame) -> pd.DataFrame:
    """Compute safety stock for all Class A SKUs using a mile-weighted average lead time.

    Formula (mirrors LOGage2026_Part2_SafetyStock_MileAvg.xlsx, sheet 'Q2.2 Safety Stock'):
        SS  = Z × σ_daily × √(LT_avg)
        ROP = μ_daily × LT_avg + SS
    where:
        Z        = 1.645  (95 % service level, one-tailed)
        LT_avg   = mile-weighted average replenishment lead time (days)
        σ_daily  = σ_monthly / √30
        μ_daily  = μ_monthly / 30
        σ_monthly computed with ddof=1 over 7 months (Jun–Dec 2025)
    """
    lt_avg = _compute_mile_weighted_lt()  # ≈ 1.94 days
    sqrt_lt = np.sqrt(lt_avg)

    class_a = set(abc_xyz.loc[abc_xyz["abc_quantity"].eq("A"), "sku_code"])
    class_a_shipments = shipments[
        shipments["sku_code"].isin(class_a)
        & shipments["created_date"].between("2025-06-01", "2025-12-31")
    ].copy()

    monthly = (
        class_a_shipments
        .assign(month=class_a_shipments["created_date"].dt.to_period("M"))
        .groupby(["sku_code", "month"])["quantity"]
        .sum()
        .unstack(fill_value=0)
    )
    months = pd.period_range(start="2025-06", end="2025-12", freq="M")
    monthly = monthly.reindex(columns=months, fill_value=0)

    table = pd.DataFrame(
        {
            "sku_code": monthly.index,
            "mu_monthly": monthly.mean(axis=1).values,
            "sigma_monthly": monthly.std(axis=1, ddof=1).values,
        }
    )

    table["mu_daily"]    = table["mu_monthly"] / 30
    table["sigma_daily"] = table["sigma_monthly"] / np.sqrt(30)
    table["Z"]           = 1.645
    table["lt_avg"]      = lt_avg
    table["sqrt_lt"]     = sqrt_lt

    table["ss"]  = table["Z"] * table["sigma_daily"] * sqrt_lt
    table["rop"] = table["mu_daily"] * lt_avg + table["ss"]

    table = table.merge(
        abc_xyz[["sku_code", "product_name", "category", "abc_quantity", "abc_frequency"]],
        on="sku_code",
        how="left",
    ).fillna("")

    return table.sort_values("ss", ascending=False)


def build_lead_time_sensitivity(safety_stock_table: pd.DataFrame) -> pd.DataFrame:
    """Show how total Class A safety stock changes as LT_avg is varied from 1 to 7 days.

    Uses the same simplified formula as build_safety_stock_class_a:
        total_SS(LT) = Z × Σσ_daily × √LT
    The actual LT_avg ≈ 1.94 is the reference point (first row).
    """
    rows = []
    total_class_a_sigma_d = safety_stock_table["sigma_daily"].sum()
    z = 1.645
    lt_actual = _compute_mile_weighted_lt()
    ss_at_actual = z * total_class_a_sigma_d * np.sqrt(lt_actual)
    for lt in range(1, 8):
        total_ss = z * total_class_a_sigma_d * np.sqrt(lt)
        rows.append({
            "lead_time_days": lt,
            "total_safety_stock": total_ss,
            "delta_from_actual": total_ss - ss_at_actual,
        })
    return pd.DataFrame(rows)


def build_inventory_pooling_summary(safety_stock_table: pd.DataFrame) -> pd.DataFrame:
    """Compare separated-channel SS vs virtual-pooling SS for reference.

    The 'Pooled (Mile-Weighted)' row reflects the actual model used in
    build_safety_stock_class_a (SS = Z × σ × √LT_avg, LT_avg ≈ 1.94 days).

    The 'Separated B2B + B2C' reference scenario (B2B=5d, B2C=2d) is kept for
    comparison, following the Excel Q2.2 Pooling sheet quantification:
        Separated: SS = Z × σ × (√5 + √2) = Z × σ × 3.650
        Pooled:    SS = Z × σ × √3.5      = Z × σ × 1.871
        Reduction factor = √3.5 / (√5 + √2) ≈ 0.5125  → −48.7%
    """
    z = 1.645
    total_class_a_sigma_d = safety_stock_table["sigma_daily"].sum()

    # Reference: separated B2B (5d) + B2C (2d)
    lt_b2b, lt_b2c = 5.0, 2.0
    separated_ss = z * total_class_a_sigma_d * (np.sqrt(lt_b2b) + np.sqrt(lt_b2c))

    # Reference: classic pooled (avg of the two channels)
    classic_pooled_ss = z * total_class_a_sigma_d * np.sqrt((lt_b2b + lt_b2c) / 2.0)
    classic_savings_pct = (separated_ss - classic_pooled_ss) / separated_ss if separated_ss else 0

    # Actual model: mile-weighted average LT
    lt_avg = _compute_mile_weighted_lt()
    mw_pooled_ss = z * total_class_a_sigma_d * np.sqrt(lt_avg)
    mw_savings_pct = (separated_ss - mw_pooled_ss) / separated_ss if separated_ss else 0

    return pd.DataFrame([
        {
            "scenario": "Separated B2B + B2C",
            "formula": "Z * sigma * (sqrt(5) + sqrt(2))",
            "total_ss": separated_ss,
            "savings_pct": 0.0,
        },
        {
            "scenario": "Pooled (Shared)",
            "formula": "Z * sigma * sqrt(3.5)",
            "total_ss": classic_pooled_ss,
            "savings_pct": classic_savings_pct,
        },
        {
            "scenario": "Pooled (Mile-Weighted)",
            "formula": f"Z * sigma * sqrt({lt_avg:.4f})",
            "total_ss": mw_pooled_ss,
            "savings_pct": mw_savings_pct,
        },
    ])


def build_hcm_district_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    hcm_ship = shipments[
        shipments["province"].eq("Hồ Chí Minh") 
        & shipments["created_date"].between("2025-06-01", "2025-12-31") 
        & shipments["document_type"].eq("A/R INVOICE")
    ]
    districts_summary = hcm_ship.groupby("district").agg(
        orders=("order_id", "nunique"),
        quantity=("quantity", "sum"),
        cbm=("cbm_total", "sum"),
        avg_dist_my_phuoc=("distance_from_my_phuoc_km", "mean"),
        avg_dist_vinh_loc=("distance_from_vinh_loc_km", "mean"),
        avg_lat=("latitude", "mean"),
        avg_lon=("longitude", "mean")
    ).sort_values("orders", ascending=False).reset_index()
    return districts_summary


def build_network_model_evaluation(hcm_district_summary: pd.DataFrame) -> pd.DataFrame:
    """Q2.1: Evaluate each HCM district's RDC distance and suitability for 2-4h B2C SLA.
    
    Implements travel time verification formula, traffic zones, and compares Vinh Loc Baseline vs. Vinh Loc + DS1 + DS2.
    """
    df = hcm_district_summary.copy()
    
    # Model 2 Dark Stores coordinates
    ds1_coord = (10.7848, 106.6267)
    ds2_coord = (10.7735, 106.6982)
    
    from src.logage2026.geography import haversine_km
    
    # Calculate distance from each district's center to DS1 and DS2
    df["dist_ds1"] = df.apply(lambda r: haversine_km((r["avg_lat"], r["avg_lon"]), ds1_coord), axis=1)
    df["dist_ds2"] = df.apply(lambda r: haversine_km((r["avg_lat"], r["avg_lon"]), ds2_coord), axis=1)
    
    def get_traffic_factor(district):
        d = district.strip()
        inner = {
            "Quận 1", "Quận 3", "Quận 4", "Quận 5", "Quận 6", "Quận 10", "Quận 11",
            "Gò Vấp", "Bình Thạnh", "Phú Nhuận", "Tân Bình", "Tân Phú"
        }
        suburban = {
            "Thủ Đức", "Bình Tân", "Bình Chánh", "Quận 7", "Quận 8", "Quận 12",
            "Hóc Môn", "Nhà Bè"
        }
        outer = {"Củ Chi"}
        if d in inner:
            return 1.8
        if d in suburban:
            return 1.4
        if d in outer:
            return 1.2
        return 1.4
        
    df["traffic_factor"] = df["district"].apply(get_traffic_factor)
    
    # Baseline: served by Vinh Loc RDC with 90 min overhead
    df["baseline_dist"] = df["avg_dist_vinh_loc"]
    df["baseline_time"] = (df["baseline_dist"] / 30.0) * 60.0 * df["traffic_factor"] + 90.0
    df["baseline_2h"] = np.where(df["baseline_time"] <= 120.0, "Met", "Not Met")
    df["baseline_4h"] = np.where(df["baseline_time"] <= 240.0, "Met", "Not Met")
    
    # 2 Dark Stores: Vinh Loc RDC, DS1, DS2
    df["ds_dist"] = df[["avg_dist_vinh_loc", "dist_ds1", "dist_ds2"]].min(axis=1)
    df["nearest_facility"] = np.where(
        df["ds_dist"] == df["avg_dist_vinh_loc"], 
        "Vinh Loc RDC", 
        np.where(df["ds_dist"] == df["dist_ds1"], "DS1 (Tân Phú)", "DS2 (Quận 1)")
    )
    df["ds_overhead"] = np.where(df["nearest_facility"] == "Vinh Loc RDC", 90.0, 35.0)
    df["ds_time"] = (df["ds_dist"] / 30.0) * 60.0 * df["traffic_factor"] + df["ds_overhead"]
    df["ds_2h"] = np.where(df["ds_time"] <= 120.0, "Met", "Not Met")
    df["ds_4h"] = np.where(df["ds_time"] <= 240.0, "Met", "Not Met")
    
    total_qty = df["quantity"].sum()
    df["qty_share"] = df["quantity"] / total_qty if total_qty else 0.0
    # Derive sla_status for downstream consumers (notes.py / visuals.py)
    df["sla_status"] = np.where(df["baseline_4h"] == "Met", "Adequate", "Needs Dark Store")
    # Backward-compatible alias used by visuals.py _q21_network_coverage_chart
    df["best_rdc_km"] = df["baseline_dist"]
    return df.sort_values("quantity", ascending=False).reset_index(drop=True)


def build_q21_channel_flow_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    """Q2.1: Compute warehouse x channel operational KPIs with timeline context.

    The two RDCs operated in non-overlapping periods:
      - My Phuoc: Jun-Nov 2025  (primary warehouse, 6 months)
      - Vinh Loc: Dec 2025 only (new/secondary warehouse, 1 month)

    All rate metrics (avg_orders_per_active_day, etc.) are normalized to each
    warehouse's actual operating window so that the volatility index and order
    intensity are comparable on a like-for-like basis.
    """
    df = shipments[
        shipments["created_date"].between("2025-06-01", "2025-12-31")
        & shipments["document_type"].eq("A/R INVOICE")
    ].copy()

    df["date"] = pd.to_datetime(df["created_date"]).dt.date

    # Determine each warehouse's operating window from actual data
    wh_windows: dict = {}
    for wh, grp in df.groupby("source_warehouse"):
        wh_windows[wh] = (grp["date"].min(), grp["date"].max(), grp["date"].nunique())

    # Daily order counts per (warehouse, channel, date)
    daily = (
        df.groupby(["source_warehouse", "channel", "date"])
        .agg(daily_orders=("order_id", "nunique"))
        .reset_index()
    )

    rows = []
    for (wh, ch), grp in df.groupby(["source_warehouse", "channel"]):
        orders = grp["order_id"].nunique()
        quantity = grp["quantity"].sum()
        cbm = grp["cbm_total"].sum()
        avg_cbm_per_order = cbm / orders if orders else 0.0

        daily_grp = daily[(daily["source_warehouse"] == wh) & (daily["channel"] == ch)]
        active_days_ch = len(daily_grp)
        avg_orders_per_day = daily_grp["daily_orders"].mean() if active_days_ch else 0.0
        peak_orders = daily_grp["daily_orders"].max() if active_days_ch else 0
        p95_orders = float(daily_grp["daily_orders"].quantile(0.95)) if active_days_ch else 0.0
        volatility_index = peak_orders / p95_orders if p95_orders else 0.0

        # Operating window for this warehouse (across all channels)
        wh_start, wh_end, wh_active_days = wh_windows.get(wh, (None, None, 0))
        # Calendar months span: treat active_days / 30 as approximate operating months
        operating_months = round(wh_active_days / 30, 1)

        # Order share within warehouse
        wh_df = df[df["source_warehouse"] == wh]
        wh_orders = wh_df["order_id"].nunique()
        wh_cbm = wh_df["cbm_total"].sum()
        order_share = orders / wh_orders if wh_orders else 0.0
        cbm_share = cbm / wh_cbm if wh_cbm else 0.0

        # Qualitative flow-type classification
        if order_share >= 0.9 and cbm_share >= 0.9:
            flow_type = "Large-volume flow"
        elif order_share < 0.1 or cbm_share < 0.05:
            flow_type = "Small fragmented flow"
        else:
            flow_type = "Mixed flow"

        # Human-readable period note
        if wh == "My Phuoc":
            period_note = "Primary RDC: Jun to Nov 2025 (6 months)"
        elif wh == "Vinh Loc":
            period_note = "New RDC: Dec 2025 only (1 month)"
        else:
            period_note = f"{wh_start} to {wh_end}"

        rows.append({
            "warehouse": wh,
            "channel": ch,
            "operating_start": str(wh_start),
            "operating_end": str(wh_end),
            "operating_months": operating_months,
            "period_note": period_note,
            "orders": orders,
            "quantity": quantity,
            "total_cbm": cbm,
            "avg_cbm_per_order": avg_cbm_per_order,
            "active_days": active_days_ch,
            "avg_orders_per_day": avg_orders_per_day,
            "peak_daily_orders": int(peak_orders),
            "p95_daily_orders": p95_orders,
            "volatility_index": volatility_index,
            "order_share_in_warehouse": order_share,
            "cbm_share_in_warehouse": cbm_share,
            "flow_type": flow_type,
        })

    result = pd.DataFrame(rows).sort_values(
        ["warehouse", "channel"], ascending=[True, True]
    ).reset_index(drop=True)
    return result


# ---------------------------------------------------------------------------
# Part 3 — Slotting & Pick-Time Constants
# ---------------------------------------------------------------------------
# Physical zone distances to packing station (U-shaped warehouse model)
# Source: LOGage2026 Excel model assumptions (Q3.1 Slotting Design sheet)
#   Zone A (golden pick-face, nearest dock):       8.0 m
#   Zone B (mid-bay forward reserve):             25.0 m
#   Zone C (back / upper rack reserve/bulk):      47.5 m
DIST_A_M = 8.0
DIST_B_M = 25.0
DIST_C_M = 47.5

# Per-zone pick rates (pcs/min) from Excel model assumptions
#   Zone A: 4 pcs/min   — fast pick-face (loose + carton break-bulk)
#   Zone B: 2.5 pcs/min — carton-centric intermediate
#   Zone C: 2.0 pcs/min — slow reserve / pallet store
PICK_RATE_A_PCS_MIN = 4.0
PICK_RATE_B_PCS_MIN = 2.5
PICK_RATE_C_PCS_MIN = 2.0

# Walk speed and round-trip factor for travel-time proof
# Source: Excel model assumption: walk speed 1.2 m/s = 72 m/min; round-trip = pick + return
WALK_SPEED_M_MIN   = 72.0   # m/min (1.2 m/s, standard warehouse)
ROUND_TRIP_FACTOR  = 2      # one-way distance × 2 for round-trip

# Minimum travel-time reduction target (≥30% vs random baseline)
# Source: Excel Q3.1 Travel Proof, cell labelled "Target"
REDUCTION_TARGET = 0.30

# Pick-time benchmarks (seconds per pick event, Vietnam warehouse standard)
# Sources:
#   - PICK_TIME_LOOSE_SEC: Standard each-pick time (MOST/MTM-1 time study: 3.0-4.5s pick + 1.5-2.0s scan)
#   - PICK_TIME_CARTON_SEC: Standard carton manual hand-carry & stack (Frazelle, 2002)
#   - PICK_TIME_PALLET_SEC: Forklift retrieval cycle (Vietnam benchmark: 1-3 mins; Mecalux standard)
PICK_TIME_LOOSE_SEC   = 6.0    # per pcs, manual pick from shelf
PICK_TIME_CARTON_SEC  = 12.0   # per carton, hand-carried
PICK_TIME_PALLET_SEC  = 120.0  # per pallet, forklift / reach truck

# Ergonomic weight thresholds (kg per piece)
# Sources:
#   - ERGO_LIGHT_KG: ISO 11228-1 lower-bound threshold for manual lifting risk assessment
#   - ERGO_HEAVY_KG: NIOSH Lifting Equation / UK HSE MAC charts high-risk limit for repetitive lifting
ERGO_LIGHT_KG  = 3.0
ERGO_HEAVY_KG  = 8.0

# Composite intra-zone score weights (lower composite = closer to dock)
# Source: Multi-Criteria Decision Analysis (MCDA) in Warehouse Slotting (Tompkins et al., 2010)
W_VELOCITY  = 0.50
W_ERGONOMIC = 0.30
W_SIZE      = 0.20

# A-door rule: top-N velocity SKUs must occupy the nearest N slots to dock
# Source: Golden Zone & Dock-Adjacent Slotting (Frazelle, 2002)
A_DOOR_TOP_N = 10

# Zone distance and pick-rate lookup maps (used by slotting plan & travel proof)
_ZONE_DIST_M     = {"A": DIST_A_M, "B": DIST_B_M, "C": DIST_C_M}
_ZONE_PICK_RATE  = {"A": PICK_RATE_A_PCS_MIN, "B": PICK_RATE_B_PCS_MIN, "C": PICK_RATE_C_PCS_MIN}


def build_sku_pick_profile(
    shipments: pd.DataFrame,
    sku_master: pd.DataFrame,
    abc_xyz: pd.DataFrame,
) -> pd.DataFrame:
    """Compute per-SKU pick-unit mix and ergonomic / size scores.

    For each SKU the function estimates:
      - avg_qty_per_order   : mean order-line quantity (Jun–Dec 2025)
      - pallet_share        : fraction of order lines that are full-pallet picks
      - carton_share        : fraction of order lines that are full-carton picks
      - loose_share         : fraction of order lines that are loose-piece picks
      - baseline_pick_time_sec: weighted pick time per order event
      - ergonomic_penalty   : 0 (light) / 1 (moderate) / 2 (heavy, needs MHE)
      - cbm_incl_flap_m3    : carton CBM from SKU master (size proxy)
      - size_score_norm     : size relative to the median CBM in its ABC class

    Pick-unit classification:
      order qty >= pcs_per_pallet  → pallet pick
      order qty >= pcs_per_carton  → carton pick
      else                         → loose / piece pick
    """
    ship = shipments[
        shipments["created_date"].between("2025-06-01", "2025-12-31")
    ].copy()

    # Per-order-line quantities
    order_lines = (
        ship.groupby(["sku_code", "order_id"])["quantity"]
        .sum()
        .reset_index()
        .rename(columns={"quantity": "order_qty"})
    )

    # Join physical attributes
    phys = sku_master[[
        "sku_code", "pcs_per_carton", "pcs_per_pallet",
        "cbm_incl_flap_m3", "pcs_weight_kg", "carton_weight_kg",
    ]].copy()
    order_lines = order_lines.merge(phys, on="sku_code", how="left")

    # Classify each order line into a pick unit
    def _classify(row: pd.Series) -> str:
        qty  = row["order_qty"]
        ppp  = row["pcs_per_pallet"]
        ppc  = row["pcs_per_carton"]
        if pd.notna(ppp) and qty >= ppp:
            return "pallet"
        if pd.notna(ppc) and qty >= ppc:
            return "carton"
        return "loose"

    order_lines["pick_unit"] = order_lines.apply(_classify, axis=1)

    # Aggregate per-SKU mix
    mix = (
        order_lines.groupby(["sku_code", "pick_unit"])
        .size()
        .unstack(fill_value=0)
    )
    for col in ["pallet", "carton", "loose"]:
        if col not in mix.columns:
            mix[col] = 0
    mix["total_orders"] = mix[["pallet", "carton", "loose"]].sum(axis=1)
    mix["pallet_share"] = mix["pallet"] / mix["total_orders"]
    mix["carton_share"] = mix["carton"] / mix["total_orders"]
    mix["loose_share"]  = mix["loose"]  / mix["total_orders"]

    # Average qty per order
    avg_qty = order_lines.groupby("sku_code")["order_qty"].mean().rename("avg_qty_per_order")
    mix = mix.join(avg_qty)

    # Baseline pick time (weighted by share of order events × qty proxy)
    mix["baseline_pick_time_sec"] = (
        mix["pallet_share"] * PICK_TIME_PALLET_SEC
        + mix["carton_share"] * PICK_TIME_CARTON_SEC
        + mix["loose_share"]  * PICK_TIME_LOOSE_SEC
    )

    mix = mix.reset_index()

    # Join physical attributes for ergonomic / size scoring
    mix = mix.merge(phys, on="sku_code", how="left")

    # Ergonomic penalty from piece weight
    def _ergo(w):
        if pd.isna(w):
            return 1  # assume moderate if unknown
        if w <= ERGO_LIGHT_KG:
            return 0
        if w <= ERGO_HEAVY_KG:
            return 1
        return 2

    mix["ergonomic_penalty"] = mix["pcs_weight_kg"].apply(_ergo)

    # Join ABC class for class-relative size scoring
    mix = mix.merge(
        abc_xyz[["sku_code", "abc_quantity", "abc_frequency", "order_frequency", "quantity"]],
        on="sku_code",
        how="left",
    )

    # Size score: CBM relative to the median within each ABC class.
    # Use transform so abc_quantity column is never consumed by groupby.
    median_cbm = mix.groupby("abc_quantity")["cbm_incl_flap_m3"].transform("median")
    mix["size_score_norm"] = (mix["cbm_incl_flap_m3"] / median_cbm.clip(lower=1e-9)).fillna(1.0)

    return mix.reset_index(drop=True)


def build_slotting_plan(
    shipments: pd.DataFrame,
    sku_master: pd.DataFrame,
    abc_xyz: pd.DataFrame,
) -> pd.DataFrame:
    """Assign every SKU to a warehouse slotting zone with ergonomic sub-tiers.

    Two-model approach
    ------------------
    Model 1 — ABC-only (baseline)
        Zone: A → Pick-Face, B → Forward Reserve, C → Reserve/Bulk.
        Intra-zone rank: order_frequency descending.

    Model 2 — ABC + Ergonomics + Pick-Mix (new)
        Same top-level zones, but each is split into sub-tiers based on the
        pick-unit mix and physical dimensions:

        A1 (Pallet Lane):  pallet_share >= 40% AND cbm >= 0.07 m³
                           → ground-level pallet slots nearest dock (forklift lane)
        A2 (Big-Face):     pallet_share <  40% AND carton_share >= 80%
                           → waist-height shelving, full-carton pick face
        A3 (Mixed-Pick):   remaining Class A

        B1 (Bulk-Replen):  pallet_share >= 30% OR cbm >= 0.07 m³
                           → mid-aisle ground storage with dedicated replen lane
        B2 (Two-Bin):      remaining Class B → standard two-bin forward pick-face

        C1 (Upper Rack):   cbm < 0.05 m³ → upper rack (small/light slow-movers)
        C2 (Pallet Block): cbm >= 0.05 m³ → floor block-stack behind Zone B

    Composite intra-zone score (lower = closer to dock):
        score = W_VELOCITY × velocity_rank_norm
              + W_ERGONOMIC × ergonomic_penalty_norm
              + W_SIZE × size_score_norm

    A-door rule: top-A_DOOR_TOP_N velocity SKUs are pinned to rank 1..N
    regardless of sub-tier, as they must stay within the first rack bays.
    """
    profile = build_sku_pick_profile(shipments, sku_master, abc_xyz)

    df = profile.copy()

    # ── Top-level zone ───────────────────────────────────────────────────────
    zone_map = {
        "A": "Pick-Face Zone (Ground Level)",
        "B": "Forward Reserve Zone",
        "C": "Reserve / Bulk Zone",
    }
    df["zone_assignment"] = df["abc_quantity"].map(zone_map)
    df["zone_order"]      = df["abc_quantity"].map({"A": 1, "B": 2, "C": 3})

    # ── Sub-tier assignment ──────────────────────────────────────────────────
    def _sub_tier(row):
        cls  = row["abc_quantity"]
        ps   = row["pallet_share"]
        cs   = row["carton_share"]
        cbm  = row["cbm_incl_flap_m3"] if pd.notna(row["cbm_incl_flap_m3"]) else 0.04
        if cls == "A":
            if ps >= 0.40 and cbm >= 0.07:
                return "A1"
            if ps < 0.40 and cs >= 0.80:
                return "A2"
            return "A3"
        if cls == "B":
            if ps >= 0.30 or cbm >= 0.07:
                return "B1"
            return "B2"
        # cls == "C"
        if cbm < 0.05:
            return "C1"
        return "C2"

    df["sub_tier"] = df.apply(_sub_tier, axis=1)

    # Sub-tier sort priority (A1 pallet-lane nearest dock inside Zone A)
    sub_tier_order = {"A1": 1, "A2": 2, "A3": 3, "B1": 1, "B2": 2, "C1": 1, "C2": 2}
    df["sub_tier_order"] = df["sub_tier"].map(sub_tier_order)

    # ── Composite intra-zone score ───────────────────────────────────────────
    # Velocity rank (normalised 0–1 within zone; lower rank = higher velocity)
    df["velocity_rank"] = (
        df.groupby("abc_quantity")["order_frequency"]
        .rank(method="first", ascending=False)
    )
    zone_sizes = df.groupby("abc_quantity")["order_frequency"].transform("count")
    df["velocity_rank_norm"] = (df["velocity_rank"] - 1) / (zone_sizes - 1).clip(lower=1)

    # Ergonomic penalty normalised 0–1 (0=light, 0.5=moderate, 1=heavy)
    df["ergonomic_penalty_norm"] = df["ergonomic_penalty"] / 2.0

    df["composite_score"] = (
        W_VELOCITY  * df["velocity_rank_norm"]
        + W_ERGONOMIC * df["ergonomic_penalty_norm"]
        + W_SIZE      * df["size_score_norm"].clip(upper=3.0) / 3.0
    )

    # ── Sort within zone: sub-tier first, then composite score ──────────────
    df = df.sort_values(
        ["zone_order", "sub_tier_order", "composite_score"],
        ascending=[True, True, True],
    ).reset_index(drop=True)

    # ── Global rank within zone ──────────────────────────────────────────────
    df["rank_in_zone"] = (
        df.groupby("zone_assignment").cumcount() + 1
    )

    # ── A-door override: pin top-N velocity SKUs to rank 1..N ───────────────
    top_n_skus = (
        abc_xyz.sort_values("order_frequency", ascending=False)
        .head(A_DOOR_TOP_N)["sku_code"]
        .tolist()
    )
    df["a_door_pinned"] = df["sku_code"].isin(top_n_skus)

    # ── Physical zone distances, pick rates, and velocity ────────────────────
    df["slot_distance_m"]  = df["abc_quantity"].map(_ZONE_DIST_M)
    df["pick_rate_pcs_min"] = df["abc_quantity"].map(_ZONE_PICK_RATE)
    # velocity = order_frequency / pick_rate_pcs_min  (picks per pcs/min = pick-load index)
    df["velocity"] = df["order_frequency"] / df["pick_rate_pcs_min"]

    # ── Output columns ───────────────────────────────────────────────────────
    cols = [
        "sku_code",
        "abc_quantity",
        "abc_frequency",
        "zone_assignment",
        "sub_tier",
        "rank_in_zone",
        "order_frequency",
        "velocity",
        "slot_distance_m",
        "pick_rate_pcs_min",
        "composite_score",
        "pallet_share",
        "carton_share",
        "loose_share",
        "ergonomic_penalty",
        "baseline_pick_time_sec",
        "cbm_incl_flap_m3",
        "pcs_weight_kg",
        "avg_qty_per_order",
        "a_door_pinned",
    ]
    return df[cols].rename(
        columns={
            "abc_quantity": "abc_class",
            "abc_frequency": "abc_class_freq",
            "order_frequency": "travel_contribution",
        }
    )


def compute_travel_time_metrics(abc_xyz: pd.DataFrame) -> dict:
    """Compute physical travel-time metrics for the slotting design.

    Implements the physical-distance model from the Q3.1 Slotting Design Excel:

        Total round-trip distance = Σ_zone ( picks_zone × dist_zone × ROUND_TRIP_FACTOR )
        Avg one-way distance / pick = Total_round_trip / (2 × total_picks)
        Travel time (min)           = Total_round_trip / WALK_SPEED_M_MIN

    Baseline (random placement):
        Every pick travels the SKU-count-weighted average zone distance
        (i.e. all SKUs equally probable, not weighted by frequency).
        avg_dist_random = (Na × DIST_A + Nb × DIST_B + Nc × DIST_C) / N

    Optimized (ABC velocity-zoned):
        High-frequency SKUs (Class A) sit at DIST_A_M, B at DIST_B_M, C at DIST_C_M.
        Total_opt = Σ picks_zone × dist_zone × ROUND_TRIP_FACTOR

    Also computes slot-index reductions for warehouse-slotting benchmarking:
        2. ABC zoned (qty)  — A in slots 1..Na, B in Na+1..Na+Nb, C in rest
        3. ABC freq-zoned   — same structure on frequency dimension
        4. Velocity-ranked  — continuous sort by order_frequency (theoretical optimum)
        5. Model 2 (ABC+Ergon) — composite score sort, with ergonomic gain factor

    Returns a dict with physical distance/time metrics and slot-index reductions.
    """
    # ── Physical distance model (matches Excel Q3.1 Travel Proof) ───────────
    df = abc_xyz.copy()
    N = len(df)
    total_picks = df["order_frequency"].sum()

    zone_picks = df.groupby("abc_quantity")["order_frequency"].sum().to_dict()
    zone_counts = df.groupby("abc_quantity").size().to_dict()
    Na = zone_counts.get("A", 0)
    Nb = zone_counts.get("B", 0)
    Nc = zone_counts.get("C", 0)
    picks_a = zone_picks.get("A", 0)
    picks_b = zone_picks.get("B", 0)
    picks_c = zone_picks.get("C", 0)

    # Optimized: Class A at DIST_A_M, B at DIST_B_M, C at DIST_C_M
    opt_total_rt = (
        picks_a * DIST_A_M * ROUND_TRIP_FACTOR
        + picks_b * DIST_B_M * ROUND_TRIP_FACTOR
        + picks_c * DIST_C_M * ROUND_TRIP_FACTOR
    )
    opt_avg_oneway = opt_total_rt / (ROUND_TRIP_FACTOR * total_picks) if total_picks else 0.0
    opt_travel_time_min = opt_total_rt / WALK_SPEED_M_MIN if WALK_SPEED_M_MIN else 0.0

    # Baseline: random — every pick travels SKU-count-weighted avg distance
    # (each SKU equally likely to be visited, not weighted by frequency)
    avg_dist_random = (Na * DIST_A_M + Nb * DIST_B_M + Nc * DIST_C_M) / N if N else 0.0
    baseline_total_rt = total_picks * avg_dist_random * ROUND_TRIP_FACTOR
    baseline_travel_time_min = baseline_total_rt / WALK_SPEED_M_MIN if WALK_SPEED_M_MIN else 0.0

    travel_reduction = (
        (baseline_total_rt - opt_total_rt) / baseline_total_rt
        if baseline_total_rt else 0.0
    )
    meets_target = travel_reduction >= REDUCTION_TARGET

    # ── Zone-level breakdown rows (mirrors Excel Q3.1 Travel Proof table) ───
    zone_detail = [
        {"zone": "A", "picks": picks_a, "dist_m": DIST_A_M,
         "round_trip_dist_m": picks_a * DIST_A_M * ROUND_TRIP_FACTOR},
        {"zone": "B", "picks": picks_b, "dist_m": DIST_B_M,
         "round_trip_dist_m": picks_b * DIST_B_M * ROUND_TRIP_FACTOR},
        {"zone": "C", "picks": picks_c, "dist_m": DIST_C_M,
         "round_trip_dist_m": picks_c * DIST_C_M * ROUND_TRIP_FACTOR},
    ]

    return {
        # Physical distance model (primary, matches Excel)
        "N": N,
        "total_picks": int(total_picks),
        "zone_counts": {"A": Na, "B": Nb, "C": Nc},
        "zone_picks":  {"A": int(picks_a), "B": int(picks_b), "C": int(picks_c)},
        "zone_detail": zone_detail,
        # Optimized (ABC-zoned)
        "opt_total_round_trip_m":   round(opt_total_rt, 2),
        "opt_avg_oneway_m_per_pick": round(opt_avg_oneway, 4),
        "opt_travel_time_min":       round(opt_travel_time_min, 2),
        # Baseline (random placement)
        "baseline_avg_dist_m":       round(avg_dist_random, 4),
        "baseline_total_round_trip_m": round(baseline_total_rt, 2),
        "baseline_travel_time_min":    round(baseline_travel_time_min, 2),
        # Reduction
        "travel_reduction":          round(travel_reduction, 6),
        "reduction_target":          REDUCTION_TARGET,
        "meets_target":              meets_target,
        # Model parameters (for report transparency)
        "walk_speed_m_min":   WALK_SPEED_M_MIN,
        "round_trip_factor":  ROUND_TRIP_FACTOR,
        "dist_a_m": DIST_A_M,
        "dist_b_m": DIST_B_M,
        "dist_c_m": DIST_C_M,
    }


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
