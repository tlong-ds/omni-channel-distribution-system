import numpy as np
import pandas as pd


ASSIGNMENT_START = pd.Timestamp("2025-07-01")
ASSIGNMENT_END = pd.Timestamp("2025-12-31")


def classify_cumulative_share(share: float) -> str:
    if share <= 0.80:
        return "A"
    if share <= 0.95:
        return "B"
    return "C"


def classify_xyz(cv: float) -> str:
    if pd.isna(cv) or np.isinf(cv):
        return "Z"
    if cv <= 0.50:
        return "X"
    if cv <= 1.00:
        return "Y"
    return "Z"


def filter_assignment_shipments(
    shipments: pd.DataFrame,
    start_date: pd.Timestamp = ASSIGNMENT_START,
    end_date: pd.Timestamp = ASSIGNMENT_END,
) -> pd.DataFrame:
    mask = shipments["analysis_document_flag"] & shipments["created_date"].between(start_date, end_date, inclusive="both")
    return shipments.loc[mask].copy()


def build_abc_xyz(shipments: pd.DataFrame, sku_master: pd.DataFrame) -> pd.DataFrame:
    sku = shipments.groupby("sku_code").agg(
        quantity=("quantity", "sum"),
        order_frequency=("order_id", "nunique"),
        line_frequency=("sku_code", "size"),
        cbm_total=("cbm_total", "sum"),
    )
    weekly = (
        shipments.assign(week=shipments["created_date"].dt.to_period("W").astype(str))
        .groupby(["sku_code", "week"])["quantity"]
        .sum()
        .unstack(fill_value=0)
    )
    sku["weekly_mean_quantity"] = weekly.mean(axis=1)
    sku["weekly_std_quantity"] = weekly.std(axis=1)
    sku["demand_cv"] = sku["weekly_std_quantity"] / sku["weekly_mean_quantity"].replace(0, np.nan)
    sku = sku.reset_index().sort_values("quantity", ascending=False)
    sku["quantity_share"] = sku["quantity"] / sku["quantity"].sum()
    sku["quantity_cumulative_share"] = sku["quantity_share"].cumsum()
    sku["abc_quantity"] = sku["quantity_cumulative_share"].map(classify_cumulative_share)

    sku = sku.sort_values("order_frequency", ascending=False)
    sku["frequency_share"] = sku["order_frequency"] / sku["order_frequency"].sum()
    sku["frequency_cumulative_share"] = sku["frequency_share"].cumsum()
    sku["abc_frequency"] = sku["frequency_cumulative_share"].map(classify_cumulative_share)
    sku["xyz"] = sku["demand_cv"].map(classify_xyz)
    sku["abc_xyz"] = sku["abc_quantity"] + sku["xyz"]
    sku["fast_moving_flag"] = (sku["abc_quantity"].eq("A") & sku["abc_frequency"].eq("A")).astype(int)
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
        "abc_frequency",
        "weekly_mean_quantity",
        "weekly_std_quantity",
        "demand_cv",
        "xyz",
        "abc_xyz",
        "fast_moving_flag",
        "cbm_total",
        "pcs_per_carton",
        "pcs_per_pallet",
        "cbm_incl_flap_m3",
        "pcs_weight_kg",
        "carton_weight_kg",
    ]
    return sku[ordered_columns].sort_values(["abc_quantity", "xyz", "quantity"], ascending=[True, True, False])


def build_abc_xyz_matrix_summary(abc_xyz: pd.DataFrame) -> pd.DataFrame:
    return (
        abc_xyz.groupby(["abc_quantity", "xyz"], dropna=False)
        .agg(
            sku_count=("sku_code", "nunique"),
            quantity=("quantity", "sum"),
            order_frequency=("order_frequency", "sum"),
            cbm_total=("cbm_total", "sum"),
        )
        .reset_index()
        .sort_values(["abc_quantity", "xyz"])
    )


def build_fast_moving_summary(abc_xyz: pd.DataFrame) -> pd.DataFrame:
    total_quantity = abc_xyz["quantity"].sum()
    total_frequency = abc_xyz["order_frequency"].sum()
    fast = abc_xyz[abc_xyz["fast_moving_flag"].eq(1)]
    summary = pd.DataFrame(
        [
            {
                "group": "Fast Moving: ABC quantity A and ABC frequency A",
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


def build_warehouse_region_summary(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    return (
        known.groupby(["source_warehouse", "region", "province", "hcmc_district", "geography_source"], dropna=False)
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


def build_customer_cluster_summary(shipments: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    known = shipments[shipments["known_geography_flag"]].copy()
    province_summary = (
        known.groupby("province", dropna=False)
        .agg(orders=("order_id", "nunique"), quantity=("quantity", "sum"))
        .reset_index()
        .rename(columns={"province": "geography_name"})
    )
    province_summary["geography_level"] = "province"

    hcmc = known[known["province"].eq("Ho Chi Minh City") & known["hcmc_district"].ne("")].copy()
    district_summary = (
        hcmc.groupby("hcmc_district", dropna=False)
        .agg(orders=("order_id", "nunique"), quantity=("quantity", "sum"))
        .reset_index()
        .rename(columns={"hcmc_district": "geography_name"})
    )
    district_summary["geography_level"] = "hcmc_district"

    combined = pd.concat([province_summary, district_summary], ignore_index=True, sort=False)
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

    region_orders = summary.groupby("region")["orders"].transform("sum")
    region_quantity = summary.groupby("region")["quantity"].transform("sum")
    warehouse_orders = summary.groupby("source_warehouse")["orders"].transform("sum")
    warehouse_quantity = summary.groupby("source_warehouse")["quantity"].transform("sum")
    summary["region_order_share"] = summary["orders"] / region_orders
    summary["region_quantity_share"] = summary["quantity"] / region_quantity
    summary["warehouse_order_share"] = summary["orders"] / warehouse_orders
    summary["warehouse_quantity_share"] = summary["quantity"] / warehouse_quantity
    return summary.sort_values(["region", "quantity", "orders"], ascending=[True, False, False])


def build_order_profile_segments(shipments: pd.DataFrame) -> pd.DataFrame:
    known = shipments[shipments["analysis_document_flag"] & shipments["customer_segment"].ne("Unknown")].copy()
    order_level = known.groupby(["customer_segment", "order_id"]).agg(
        source_warehouse=("source_warehouse", "first"),
        province=("province", "first"),
        quantity=("quantity", "sum"),
        cbm_total=("cbm_total", "sum"),
        sku_breadth=("sku_code", "nunique"),
        line_count=("sku_code", "size"),
    )
    order_level = order_level.reset_index()
    summary = order_level.groupby("customer_segment").agg(
        orders=("order_id", "nunique"),
        provinces=("province", "nunique"),
        avg_order_quantity=("quantity", "mean"),
        median_order_quantity=("quantity", "median"),
        avg_order_cbm=("cbm_total", "mean"),
        median_order_cbm=("cbm_total", "median"),
        avg_sku_breadth=("sku_breadth", "mean"),
        avg_lines_per_order=("line_count", "mean"),
    )
    segment_sku = known.groupby("customer_segment")["sku_code"].nunique().rename("segment_sku_breadth")
    return summary.join(segment_sku).reset_index()


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
        abc_xyz[["sku_code", "product_name", "category", "abc_quantity", "abc_frequency", "xyz", "quantity"]],
        on="sku_code",
        how="left",
    )
    return table.sort_values("safety_stock_units", ascending=False)
