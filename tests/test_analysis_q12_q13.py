import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.logage2026.analysis import (
    build_q12_province_correlation_input_summary,
    build_q12_province_cluster_summary,
    build_q12_province_demand_summary,
    build_q12_province_warehouse_dominance_summary,
    build_q12_region_orders_quantity_summary,
    build_q12_urban_provincial_summary,
    build_q12_warehouse_imbalance_visual_summary,
    build_q13_segment_geographic_spread_summary,
    build_q13_segment_packaging_summary,
    build_q13_segment_province_spread_summary,
    build_q13_segment_profile_summary,
)
from src.logage2026.visuals import boundary_province_names


def _sample_shipments() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "order_id": "MT-1",
                "sku_code": "SKU1",
                "analysis_document_flag": True,
                "known_geography_flag": True,
                "customer_segment": "Modern Trade",
                "source_warehouse": "My Phuoc",
                "quantity": 100.0,
                "cbm_total": 10.0,
                "customer_key": "CUST-MT-1",
                "province": "Hồ Chí Minh",
                "region": "Đông Nam Bộ",
                "distance_from_my_phuoc_km": 12.0,
                "distance_from_vinh_loc_km": 999.0,
            },
            {
                "order_id": "MT-1",
                "sku_code": "SKU2",
                "analysis_document_flag": True,
                "known_geography_flag": True,
                "customer_segment": "Modern Trade",
                "source_warehouse": "My Phuoc",
                "quantity": 20.0,
                "cbm_total": 2.0,
                "customer_key": "CUST-MT-1",
                "province": "Hồ Chí Minh",
                "region": "Đông Nam Bộ",
                "distance_from_my_phuoc_km": 12.0,
                "distance_from_vinh_loc_km": 999.0,
            },
            {
                "order_id": "MT-2",
                "sku_code": "SKU2",
                "analysis_document_flag": True,
                "known_geography_flag": True,
                "customer_segment": "Modern Trade",
                "source_warehouse": "Vinh Loc",
                "quantity": 24.0,
                "cbm_total": 3.0,
                "customer_key": "CUST-MT-2",
                "province": "Đà Nẵng",
                "region": "Bắc Trung Bộ và Duyên hải miền Trung",
                "distance_from_my_phuoc_km": 777.0,
                "distance_from_vinh_loc_km": 34.0,
            },
            {
                "order_id": "TT-1",
                "sku_code": "SKU3",
                "analysis_document_flag": True,
                "known_geography_flag": True,
                "customer_segment": "Traditional Trade / Distributor",
                "source_warehouse": "Vinh Loc",
                "quantity": 18.0,
                "cbm_total": 1.8,
                "customer_key": "CUST-TT-1",
                "province": "Bình Dương",
                "region": "Đông Nam Bộ",
                "distance_from_my_phuoc_km": 400.0,
                "distance_from_vinh_loc_km": 21.0,
            },
            {
                "order_id": "TT-2",
                "sku_code": "SKU3",
                "analysis_document_flag": True,
                "known_geography_flag": True,
                "customer_segment": "Traditional Trade / Distributor",
                "source_warehouse": "My Phuoc",
                "quantity": 8.0,
                "cbm_total": 0.8,
                "customer_key": "CUST-TT-2",
                "province": "Long An",
                "region": "Đồng bằng sông Cửu Long",
                "distance_from_my_phuoc_km": 55.0,
                "distance_from_vinh_loc_km": 888.0,
            },
            {
                "order_id": "UNK-1",
                "sku_code": "SKU4",
                "analysis_document_flag": True,
                "known_geography_flag": True,
                "customer_segment": "Unknown",
                "source_warehouse": "My Phuoc",
                "quantity": 5.0,
                "cbm_total": 0.5,
                "customer_key": "CUST-UNK-1",
                "province": "Hà Nội",
                "region": "Đồng bằng sông Hồng",
                "distance_from_my_phuoc_km": 80.0,
                "distance_from_vinh_loc_km": 90.0,
            },
        ]
    )


def _sample_sku_master() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"sku_code": "SKU1", "pcs_per_pallet": 100.0, "pcs_per_carton": 10.0},
            {"sku_code": "SKU2", "pcs_per_pallet": 50.0, "pcs_per_carton": 12.0},
            {"sku_code": "SKU3", "pcs_per_pallet": 24.0, "pcs_per_carton": 6.0},
            {"sku_code": "SKU4", "pcs_per_pallet": 10.0, "pcs_per_carton": 5.0},
        ]
    )


def test_q12_urban_provincial_summary_uses_fixed_municipality_rule() -> None:
    shipments = _sample_shipments()

    summary = build_q12_urban_provincial_summary(shipments)

    urban_quantity = summary.loc[summary["geography_tier"].eq("urban"), "quantity"].sum()
    provincial_quantity = summary.loc[summary["geography_tier"].eq("provincial"), "quantity"].sum()

    assert urban_quantity == 149.0
    assert provincial_quantity == 26.0


def test_q12_summaries_reconcile_and_capture_warehouse_dominance() -> None:
    shipments = _sample_shipments()
    known_total = shipments.loc[shipments["known_geography_flag"], "quantity"].sum()

    region_summary = build_q12_region_orders_quantity_summary(shipments)
    province_summary = build_q12_province_cluster_summary(shipments, top_n=10)
    province_demand = build_q12_province_demand_summary(shipments)
    warehouse_dominance = build_q12_province_warehouse_dominance_summary(shipments)
    correlation_summary = build_q12_province_correlation_input_summary(shipments)
    imbalance_summary = build_q12_warehouse_imbalance_visual_summary(shipments)

    assert region_summary["quantity"].sum() == known_total
    assert province_demand["quantity"].sum() == known_total
    assert warehouse_dominance["quantity"].sum() == known_total
    assert "Hồ Chí Minh" in province_summary["province"].tolist()
    hcm = province_summary.loc[province_summary["province"].eq("Hồ Chí Minh")].iloc[0]
    assert hcm["dominant_warehouse"] == "My Phuoc"
    assert correlation_summary.loc[correlation_summary["province"].eq("Hồ Chí Minh"), "avg_distance_km"].iloc[0] == 12.0
    assert imbalance_summary["region_quantity"].sum() == known_total
    assert imbalance_summary["dominant_warehouse"].isin({"My Phuoc", "Vinh Loc", "Balanced"}).all()


def test_q13_segment_profile_uses_serving_warehouse_distance_proxy() -> None:
    shipments = _sample_shipments()
    sku_master = _sample_sku_master()

    profile = build_q13_segment_profile_summary(shipments, sku_master).set_index("customer_segment")

    modern_trade_distance = profile.loc["Modern Trade", "avg_distance_km"]
    traditional_distance = profile.loc["Traditional Trade / Distributor", "avg_distance_km"]

    assert modern_trade_distance == 23.0
    assert traditional_distance == 38.0


def test_q13_packaging_and_geographic_spread_reconcile_by_segment() -> None:
    shipments = _sample_shipments()
    sku_master = _sample_sku_master()

    profile = build_q13_segment_profile_summary(shipments, sku_master)
    packaging = build_q13_segment_packaging_summary(shipments, sku_master)
    spread = build_q13_segment_geographic_spread_summary(shipments).set_index("customer_segment")
    province_spread = build_q13_segment_province_spread_summary(shipments)

    assert int(profile["orders"].sum()) == 4
    packaging_share = packaging.groupby("customer_segment")["quantity_share"].sum().round(6)
    assert packaging_share.eq(1.0).all()
    assert spread.loc["Modern Trade", "province_count"] == 2
    assert spread.loc["Traditional Trade / Distributor", "province_count"] == 2
    assert set(province_spread["customer_segment"]) == {"Modern Trade", "Traditional Trade / Distributor"}
    assert province_spread["quantity"].sum() == shipments.loc[
        shipments["customer_segment"].isin({"Modern Trade", "Traditional Trade / Distributor"}),
        "quantity",
    ].sum()


def test_boundary_layer_reconciles_with_province_summaries() -> None:
    shipments = _sample_shipments()

    boundary_names = boundary_province_names()
    demand_summary = build_q12_province_demand_summary(shipments)
    segment_summary = build_q13_segment_province_spread_summary(shipments)

    assert set(demand_summary["province"]).issubset(boundary_names)
    assert set(segment_summary["province"]).issubset(boundary_names)
