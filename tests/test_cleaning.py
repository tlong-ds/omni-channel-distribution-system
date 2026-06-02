import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from logage2026.cleaning import clean_distributors, clean_shipments, clean_sku_master


def _raw_sku_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SAP Code": "111",
                "SAP Code (2)": "1001",
                "Product Name (VN)": "SKU A",
                "No": "1",
                "Type": "FG",
                "COM Code": "C1",
                "Unit": "pcs",
                "Category": "Cat",
                "Updated Date": "2026-01-01",
                "Pcs per Carton": "10",
                "Carton Length (mm)": "100",
                "Carton Width (mm)": "200",
                "Carton Height (mm)": "300",
                "Pcs per Pallet": "100",
                "Cartons per Layer": "5",
                "Layers per Pallet": "2",
                "Loose Pcs per Pallet": pd.NA,
                "Volume (m³)": "0",
                "CBM incl. Flap (m³)": "0.125",
                "Pcs Weight (kg)": "0.5",
                "Carton Weight (kg)": pd.NA,
            },
            {
                "SAP Code": "222",
                "SAP Code (2)": "1002",
                "Product Name (VN)": "SKU B",
                "No": "2",
                "Type": "FG",
                "COM Code": "C2",
                "Unit": "pcs",
                "Category": "Cat",
                "Updated Date": "2026-01-02",
                "Pcs per Carton": "8",
                "Carton Length (mm)": "0",
                "Carton Width (mm)": "50",
                "Carton Height (mm)": "60",
                "Pcs per Pallet": "70",
                "Cartons per Layer": "4",
                "Layers per Pallet": "2",
                "Loose Pcs per Pallet": pd.NA,
                "Volume (m³)": pd.NA,
                "CBM incl. Flap (m³)": "0.020",
                "Pcs Weight (kg)": pd.NA,
                "Carton Weight (kg)": "4.0",
            },
            {
                "SAP Code": "333",
                "SAP Code (2)": "1003",
                "Product Name (VN)": "SKU C",
                "No": "3",
                "Type": "FG",
                "COM Code": "C3",
                "Unit": "pcs",
                "Category": "Cat",
                "Updated Date": "2026-01-03",
                "Pcs per Carton": "6",
                "Carton Length (mm)": "40",
                "Carton Width (mm)": "50",
                "Carton Height (mm)": "60",
                "Pcs per Pallet": "40",
                "Cartons per Layer": "4",
                "Layers per Pallet": "1",
                "Loose Pcs per Pallet": "1",
                "Volume (m³)": "0.010",
                "CBM incl. Flap (m³)": "0.011",
                "Pcs Weight (kg)": "1.0",
                "Carton Weight (kg)": "10.0",
            },
            {
                "SAP Code": "444",
                "SAP Code (2)": "1003",
                "Product Name (VN)": "SKU C duplicate",
                "No": "4",
                "Type": "FG",
                "COM Code": "C4",
                "Unit": "pcs",
                "Category": "Cat",
                "Updated Date": "2026-01-04",
                "Pcs per Carton": "6",
                "Carton Length (mm)": "40",
                "Carton Width (mm)": "50",
                "Carton Height (mm)": "60",
                "Pcs per Pallet": "40",
                "Cartons per Layer": "4",
                "Layers per Pallet": "1",
                "Loose Pcs per Pallet": "1",
                "Volume (m³)": "0.010",
                "CBM incl. Flap (m³)": "0.011",
                "Pcs Weight (kg)": "1.0",
                "Carton Weight (kg)": "6.0",
            },
            {
                "SAP Code": "footer",
                "SAP Code (2)": "Prepared by",
                "Product Name (VN)": pd.NA,
                "No": pd.NA,
                "Type": pd.NA,
                "COM Code": pd.NA,
                "Unit": pd.NA,
                "Category": pd.NA,
                "Updated Date": pd.NA,
                "Pcs per Carton": pd.NA,
                "Carton Length (mm)": pd.NA,
                "Carton Width (mm)": pd.NA,
                "Carton Height (mm)": pd.NA,
                "Pcs per Pallet": pd.NA,
                "Cartons per Layer": pd.NA,
                "Layers per Pallet": pd.NA,
                "Loose Pcs per Pallet": pd.NA,
                "Volume (m³)": pd.NA,
                "CBM incl. Flap (m³)": pd.NA,
                "Pcs Weight (kg)": pd.NA,
                "Carton Weight (kg)": pd.NA,
            },
        ]
    )


def test_clean_sku_master_applies_strict_missingness_and_derivations() -> None:
    cleaned = clean_sku_master(_raw_sku_frame())

    assert cleaned["sku_code"].tolist() == ["1001", "1002", "1003"]
    assert cleaned["sap_code_2"].tolist() == ["1001", "1002", "1003"]
    assert str(cleaned["carton_length_mm"].dtype) == "Int64"
    assert str(cleaned["volume_m3"].dtype) == "Float64"
    assert str(cleaned["pcs_weight_kg"].dtype) == "Float64"

    sku_a = cleaned.loc[cleaned["sku_code"].eq("1001")].iloc[0]
    assert pd.isna(sku_a["volume_m3"])
    assert sku_a["cbm_incl_flap_m3"] == 0.125
    assert sku_a["carton_volume_from_dims_m3"] == 0.006
    assert sku_a["pallet_base_pcs_capacity"] == 100
    assert sku_a["loose_pcs_per_pallet"] == 0
    assert sku_a["carton_weight_kg"] == 5.0
    assert sku_a["pcs_weight_kg"] == 0.5
    assert sku_a["weight_conflict_flag"] == 0
    assert sku_a["imputation_notes"] == "loose_pcs_from_pallet_residual;carton_weight_from_piece_weight"

    sku_b = cleaned.loc[cleaned["sku_code"].eq("1002")].iloc[0]
    assert pd.isna(sku_b["carton_length_mm"])
    assert pd.isna(sku_b["carton_volume_from_dims_m3"])
    assert sku_b["loose_pcs_per_pallet"] == 6
    assert sku_b["pcs_weight_kg"] == 0.5
    assert sku_b["carton_weight_kg"] == 4.0
    assert sku_b["imputation_notes"] == "loose_pcs_from_pallet_residual;piece_weight_from_carton_weight"

    sku_c = cleaned.loc[cleaned["sku_code"].eq("1003")].iloc[0]
    assert sku_c["weight_conflict_flag"] == 1
    assert sku_c["pcs_weight_kg"] == 1.0
    assert sku_c["carton_weight_kg"] == 10.0


def test_clean_distributors_marks_ambiguous_customer_keys() -> None:
    raw = pd.DataFrame(
        [
            {
                "Customer Name": "Alpha Co",
                "Delivery Address": "123 Nguyen Trai, Quan 1, TP HCM",
                "Source Sheet": "pivot",
            },
            {
                "Customer Name": "Alpha Co",
                "Delivery Address": "456 Nguyen Van Linh, Quan 7, TP HCM",
                "Source Sheet": "general",
            },
            {
                "Customer Name": "Beta Mart",
                "Delivery Address": "Thu Dau Mot, Binh Duong",
                "Source Sheet": "pivot",
            },
        ]
    )

    cleaned = clean_distributors(raw)

    alpha = cleaned.loc[cleaned["customer_key"].eq("ALPHA CO")]
    beta = cleaned.loc[cleaned["customer_key"].eq("BETA MART")].iloc[0]

    assert len(alpha) == 2
    assert alpha["customer_key_is_ambiguous"].all()
    assert set(alpha["customer_match_status"]) == {"ambiguous_multi_location_customer"}
    assert int(beta["customer_location_count"]) == 1
    assert bool(beta["customer_key_is_ambiguous"]) is False
    assert beta["customer_match_status"] == "unique_resolvable_customer_geography"


def test_clean_shipments_uses_demand_only_and_avoids_ambiguous_distributor_geo() -> None:
    distributors = clean_distributors(
        pd.DataFrame(
            [
                {
                    "Customer Name": "Alpha Co",
                    "Delivery Address": "123 Nguyen Trai, Quan 1, TP HCM",
                    "Source Sheet": "pivot",
                },
                {
                    "Customer Name": "Alpha Co",
                    "Delivery Address": "456 Nguyen Van Linh, Quan 7, TP HCM",
                    "Source Sheet": "general",
                },
                {
                    "Customer Name": "Beta Mart",
                    "Delivery Address": "Thu Dau Mot, Binh Duong",
                    "Source Sheet": "pivot",
                },
            ]
        )
    )
    raw = pd.DataFrame(
        [
            {
                "SKU Code (CMMF)": "1001",
                "Document No.": "1",
                "Source Warehouse": "My Phuoc",
                "Document Type": "A/R Invoice",
                "Unit": "pcs",
                "Quantity": 10,
                "CBM Total": 1.5,
                "Created Date": "2025-07-10",
                "Ship-to Customer": "Alpha Co",
            },
            {
                "SKU Code (CMMF)": "1002",
                "Document No.": "2",
                "Source Warehouse": "My Phuoc",
                "Document Type": "Goods Issue",
                "Unit": "pcs",
                "Quantity": 5,
                "CBM Total": 0.5,
                "Created Date": "2025-07-11",
                "Ship-to Customer": "Beta Mart",
            },
            {
                "SKU Code (CMMF)": "1003",
                "Document No.": "3",
                "Source Warehouse": "Vinh Loc",
                "Document Type": "A/R Invoice",
                "Unit": "pcs",
                "Quantity": 8,
                "CBM Total": 0.8,
                "Created Date": "2025-07-12",
                "Ship-to Customer": "Customer C - Quan 1, TP HCM",
            },
        ]
    )

    cleaned = clean_shipments(raw, distributors).set_index("document_no")

    ambiguous = cleaned.loc["1"]
    excluded = cleaned.loc["2"]
    parsed = cleaned.loc["3"]

    assert bool(ambiguous["analysis_document_flag"]) is True
    assert pd.isna(ambiguous["exclusion_reason"])
    assert ambiguous["customer_match_status"] == "ambiguous_multi_location_customer"
    assert ambiguous["geography_source"] == "unresolved"
    assert ambiguous["province"] == "Unknown"
    assert ambiguous["customer_segment"] == "Traditional Trade / Distributor"
    assert ambiguous["segment_source"] == "customer_name_rule"

    assert bool(excluded["analysis_document_flag"]) is False
    assert excluded["exclusion_reason"] == "excluded_document_type:GOODS ISSUE"
    assert excluded["customer_segment"] == "Unknown"
    assert excluded["segment_source"] == "unresolved"
    assert excluded["geography_source"] == "distributor_match"
    assert excluded["province"] == "Binh Duong"

    assert parsed["customer_match_status"] == "unmatched_customer_key"
    assert parsed["geography_source"] == "transaction_text_parse"
    assert parsed["province"] == "Ho Chi Minh City"
    assert parsed["hcmc_district"] == "District 1"
