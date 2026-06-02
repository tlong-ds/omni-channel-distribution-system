import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from logage2026.analysis import (
    ASSIGNMENT_END,
    ASSIGNMENT_START,
    build_abc_xyz,
    build_abc_xyz_matrix_summary,
    build_customer_cluster_summary,
    build_customer_match_quality_summary,
    build_document_type_summary,
    build_fast_moving_summary,
    build_geography_coverage_summary,
    build_geography_source_summary,
    build_order_profile_segments,
    build_unresolved_customer_summary,
    build_warehouse_imbalance_summary,
    build_warehouse_region_summary,
    filter_assignment_shipments,
)


def _sku_master() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"sku_code": "1001", "product_name": "SKU A", "category": "Cat", "pcs_per_carton": 10, "pcs_per_pallet": 100, "cbm_incl_flap_m3": 0.1, "pcs_weight_kg": 0.5, "carton_weight_kg": 5.0},
            {"sku_code": "1002", "product_name": "SKU B", "category": "Cat", "pcs_per_carton": 10, "pcs_per_pallet": 100, "cbm_incl_flap_m3": 0.1, "pcs_weight_kg": 0.5, "carton_weight_kg": 5.0},
            {"sku_code": "1003", "product_name": "SKU C", "category": "Cat", "pcs_per_carton": 10, "pcs_per_pallet": 100, "cbm_incl_flap_m3": 0.1, "pcs_weight_kg": 0.5, "carton_weight_kg": 5.0},
            {"sku_code": "1004", "product_name": "SKU D", "category": "Cat", "pcs_per_carton": 10, "pcs_per_pallet": 100, "cbm_incl_flap_m3": 0.1, "pcs_weight_kg": 0.5, "carton_weight_kg": 5.0},
        ]
    )


def _shipments() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "order_id": "MP-1",
                "source_warehouse": "My Phuoc",
                "sku_code": "1001",
                "quantity": 20.0,
                "cbm_total": 2.0,
                "created_date": pd.Timestamp("2025-07-05"),
                "ship_to_customer": "Cust 1",
                "customer_key": "CUST1",
                "customer_segment": "Traditional Trade / Distributor",
                "province": "Ho Chi Minh City",
                "hcmc_district": "District 1",
                "region": "HCMC",
                "analysis_document_flag": True,
                "exclusion_reason": pd.NA,
                "customer_match_status": "unique_resolvable_customer_geography",
                "customer_location_count": 1,
                "customer_key_is_ambiguous": False,
                "geography_source": "distributor_match",
                "known_geography_flag": True,
                "segment_source": "customer_name_rule",
                "document_type": "A/R INVOICE",
            },
            {
                "order_id": "MP-2",
                "source_warehouse": "My Phuoc",
                "sku_code": "1001",
                "quantity": 20.0,
                "cbm_total": 2.0,
                "created_date": pd.Timestamp("2025-07-12"),
                "ship_to_customer": "Cust 2",
                "customer_key": "CUST2",
                "customer_segment": "Traditional Trade / Distributor",
                "province": "Ho Chi Minh City",
                "hcmc_district": "District 1",
                "region": "HCMC",
                "analysis_document_flag": True,
                "exclusion_reason": pd.NA,
                "customer_match_status": "unique_resolvable_customer_geography",
                "customer_location_count": 1,
                "customer_key_is_ambiguous": False,
                "geography_source": "distributor_match",
                "known_geography_flag": True,
                "segment_source": "customer_name_rule",
                "document_type": "A/R INVOICE",
            },
            {
                "order_id": "VL-3",
                "source_warehouse": "Vinh Loc",
                "sku_code": "1001",
                "quantity": 20.0,
                "cbm_total": 2.0,
                "created_date": pd.Timestamp("2025-07-19"),
                "ship_to_customer": "Cust 3 - Quan 7, TP HCM",
                "customer_key": "CUST3",
                "customer_segment": "Traditional Trade / Distributor",
                "province": "Ho Chi Minh City",
                "hcmc_district": "District 7",
                "region": "HCMC",
                "analysis_document_flag": True,
                "exclusion_reason": pd.NA,
                "customer_match_status": "unmatched_customer_key",
                "customer_location_count": 0,
                "customer_key_is_ambiguous": False,
                "geography_source": "transaction_text_parse",
                "known_geography_flag": True,
                "segment_source": "customer_name_rule",
                "document_type": "A/R INVOICE",
            },
            {
                "order_id": "MP-4",
                "source_warehouse": "My Phuoc",
                "sku_code": "1001",
                "quantity": 20.0,
                "cbm_total": 2.0,
                "created_date": pd.Timestamp("2025-07-26"),
                "ship_to_customer": "Cust 4",
                "customer_key": "CUST4",
                "customer_segment": "Traditional Trade / Distributor",
                "province": "Binh Duong",
                "hcmc_district": "",
                "region": "Southeast / HCMC fringe",
                "analysis_document_flag": True,
                "exclusion_reason": pd.NA,
                "customer_match_status": "unique_resolvable_customer_geography",
                "customer_location_count": 1,
                "customer_key_is_ambiguous": False,
                "geography_source": "distributor_match",
                "known_geography_flag": True,
                "segment_source": "customer_name_rule",
                "document_type": "A/R INVOICE",
            },
            {
                "order_id": "VL-5",
                "source_warehouse": "Vinh Loc",
                "sku_code": "1002",
                "quantity": 10.0,
                "cbm_total": 1.0,
                "created_date": pd.Timestamp("2025-07-19"),
                "ship_to_customer": "Cust 5",
                "customer_key": "CUST5",
                "customer_segment": "Unknown",
                "province": "Unknown",
                "hcmc_district": "",
                "region": "Unknown",
                "analysis_document_flag": True,
                "exclusion_reason": pd.NA,
                "customer_match_status": "ambiguous_multi_location_customer",
                "customer_location_count": 2,
                "customer_key_is_ambiguous": True,
                "geography_source": "unresolved",
                "known_geography_flag": False,
                "segment_source": "unresolved",
                "document_type": "A/R INVOICE",
            },
            {
                "order_id": "VL-6",
                "source_warehouse": "Vinh Loc",
                "sku_code": "1003",
                "quantity": 10.0,
                "cbm_total": 1.0,
                "created_date": pd.Timestamp("2025-07-26"),
                "ship_to_customer": "unknown",
                "customer_key": "UNKNOWN",
                "customer_segment": "Unknown",
                "province": "Unknown",
                "hcmc_district": "",
                "region": "Unknown",
                "analysis_document_flag": False,
                "exclusion_reason": "excluded_document_type:GOODS ISSUE",
                "customer_match_status": "missing_customer_name",
                "customer_location_count": 0,
                "customer_key_is_ambiguous": False,
                "geography_source": "unresolved",
                "known_geography_flag": False,
                "segment_source": "unresolved",
                "document_type": "GOODS ISSUE",
            },
            {
                "order_id": "VL-7",
                "source_warehouse": "Vinh Loc",
                "sku_code": "1004",
                "quantity": 1_000.0,
                "cbm_total": 10.0,
                "created_date": pd.Timestamp("2025-06-30"),
                "ship_to_customer": "Cust 6",
                "customer_key": "CUST6",
                "customer_segment": "Traditional Trade / Distributor",
                "province": "Ho Chi Minh City",
                "hcmc_district": "District 1",
                "region": "HCMC",
                "analysis_document_flag": True,
                "exclusion_reason": pd.NA,
                "customer_match_status": "unique_resolvable_customer_geography",
                "customer_location_count": 1,
                "customer_key_is_ambiguous": False,
                "geography_source": "distributor_match",
                "known_geography_flag": True,
                "segment_source": "customer_name_rule",
                "document_type": "A/R INVOICE",
            },
        ]
    )


def test_assignment_filter_excludes_out_of_window_and_non_demand_rows() -> None:
    filtered = filter_assignment_shipments(_shipments())

    assert len(filtered) == 5
    assert filtered["quantity"].sum() == 90.0
    assert filtered["created_date"].min() >= ASSIGNMENT_START
    assert filtered["created_date"].max() <= ASSIGNMENT_END
    assert "1004" not in set(filtered["sku_code"])
    assert "1003" not in set(filtered["sku_code"])
    assert filtered["analysis_document_flag"].all()


def test_q11_outputs_use_filtered_demand_data_and_fast_mover_is_a_a_intersection() -> None:
    filtered = filter_assignment_shipments(_shipments())
    abc_xyz = build_abc_xyz(filtered, _sku_master())
    fast = build_fast_moving_summary(abc_xyz).iloc[0]
    matrix = build_abc_xyz_matrix_summary(abc_xyz)

    by_sku = abc_xyz.set_index("sku_code")
    assert by_sku.loc["1001", "abc_quantity"] == "B"
    assert by_sku.loc["1001", "abc_frequency"] == "A"
    assert by_sku.loc["1001", "xyz"] == "X"
    assert by_sku.loc["1002", "abc_quantity"] == "C"
    assert int(by_sku["fast_moving_flag"].sum()) == 0

    assert int(fast["sku_count"]) == 0
    assert fast["quantity"] == 0.0
    assert fast["quantity_share"] == pytest.approx(0.0)
    assert fast["order_frequency"] == 0
    assert fast["frequency_share"] == pytest.approx(0.0)
    assert matrix["sku_count"].sum() == 2
    assert matrix["quantity"].sum() == pytest.approx(90.0)


def test_q12_geography_outputs_exclude_unresolved_rows_and_reconcile() -> None:
    filtered = filter_assignment_shipments(_shipments())
    coverage = build_geography_coverage_summary(filtered).iloc[0]
    warehouse_region = build_warehouse_region_summary(filtered)
    clusters = build_customer_cluster_summary(filtered, top_n=10)
    imbalance = build_warehouse_imbalance_summary(filtered)

    assert int(coverage["shipment_rows_total"]) == 5
    assert int(coverage["shipment_rows_known_geography"]) == 4
    assert coverage["shipment_row_coverage"] == pytest.approx(4 / 5)
    assert coverage["quantity_known_geography"] == pytest.approx(80.0)
    assert coverage["quantity_coverage"] == pytest.approx(80 / 90)
    assert int(coverage["rows_distributor_match"]) == 3
    assert int(coverage["rows_transaction_text_parse"]) == 1
    assert int(coverage["rows_unresolved"]) == 1
    assert int(coverage["rows_ambiguous_customer"]) == 1

    assert warehouse_region["quantity"].sum() == pytest.approx(80.0)
    assert set(warehouse_region["region"]) == {"HCMC", "Southeast / HCMC fringe"}
    assert set(warehouse_region["geography_source"]) == {"distributor_match", "transaction_text_parse"}

    provinces = clusters[clusters["geography_level"].eq("province")].set_index("geography_name")
    districts = clusters[clusters["geography_level"].eq("hcmc_district")].set_index("geography_name")
    assert provinces.loc["Ho Chi Minh City", "orders"] == 3
    assert provinces.loc["Ho Chi Minh City", "quantity"] == pytest.approx(60.0)
    assert int(provinces.loc["Ho Chi Minh City", "rank_by_orders"]) == 1
    assert int(districts.loc["District 1", "rank_by_quantity"]) == 1

    assert imbalance["quantity"].sum() == pytest.approx(80.0)
    hcmc_my_phuoc = imbalance[
        imbalance["region"].eq("HCMC") & imbalance["source_warehouse"].eq("My Phuoc")
    ].iloc[0]
    assert hcmc_my_phuoc["quantity"] == pytest.approx(40.0)
    assert hcmc_my_phuoc["region_quantity_share"] == pytest.approx(40 / 60)


def test_diagnostics_and_segment_outputs_reconcile() -> None:
    shipments = _shipments()
    filtered = filter_assignment_shipments(shipments)

    document_summary = build_document_type_summary(shipments)
    match_summary = build_customer_match_quality_summary(filtered)
    geography_summary = build_geography_source_summary(filtered)
    unresolved = build_unresolved_customer_summary(filtered)
    segments = build_order_profile_segments(filtered)

    assert int(document_summary["shipment_rows"].sum()) == len(shipments)
    assert int(document_summary.loc[document_summary["analysis_document_flag"], "shipment_rows"].sum()) == 6
    assert int(match_summary["shipment_rows"].sum()) == len(filtered)
    assert int(geography_summary["shipment_rows"].sum()) == len(filtered)
    assert set(unresolved["customer_match_status"]) == {
        "ambiguous_multi_location_customer",
        "unmatched_customer_key",
    }
    assert "Cust 5" in set(unresolved["ship_to_customer"])
    assert set(segments["customer_segment"]) == {"Traditional Trade / Distributor"}
    assert segments.iloc[0]["orders"] == 4
