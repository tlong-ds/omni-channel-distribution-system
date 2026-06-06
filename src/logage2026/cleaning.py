import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import re
import pandas as pd

from src.logage2026.geography import (
    add_distance_columns,
    normalize_text,
    parse_province,
    parse_province_with_alias,
    parse_ward,
    parse_ward_with_alias,
    region_group,
    parse_address_components,
    to_new_province,
)


DEMAND_DOCUMENT_TYPES = {"A/R INVOICE"}


import functools
from typing import Callable

def log_quality(metrics_func: Callable[[pd.DataFrame], list[str]]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            df = func(*args, **kwargs)
            from src.logage2026.config import ROOT_DIR
            log_path = ROOT_DIR / "data.log"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}] --- Data Quality Log: {func.__name__} ---\n")
                f.write(f"Shape: {df.shape}\n")
                if metrics_func:
                    for line in metrics_func(df):
                        f.write(f"  - {line}\n")
                f.write("\n")
            return df
        return wrapper
    return decorator

def _replace_blank_like_values(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.replace(r"^\s*$", pd.NA, regex=True)


def _to_nullable_code(series: pd.Series) -> pd.Series:
    code = series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    return code.replace("", pd.NA)


def _to_nullable_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").round().astype("Int64")


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Float64")


def _zero_to_na(series: pd.Series) -> pd.Series:
    return series.mask(series.eq(0))


def _append_imputation_note(notes: pd.Series, mask: pd.Series, note: str) -> pd.Series:
    notes = notes.copy()
    empty_mask = mask & notes.isna()
    existing_mask = mask & notes.notna()
    notes.loc[empty_mask] = note
    notes.loc[existing_mask] = notes.loc[existing_mask] + f";{note}"
    return notes


def _normalize_string(series: pd.Series, default: str = "") -> pd.Series:
    normalized = series.astype("string").fillna(default).str.strip()
    normalized = normalized.mask(normalized.eq(""), default)
    return normalized


def _normalize_document_type(series: pd.Series) -> pd.Series:
    return _normalize_string(series).str.upper()


def _analysis_document_flag(document_type: pd.Series) -> pd.Series:
    return document_type.isin(DEMAND_DOCUMENT_TYPES)


def _analysis_exclusion_reason(document_type: pd.Series, flag: pd.Series) -> pd.Series:
    reasons = pd.Series("", index=document_type.index, dtype="string")
    reasons.loc[~flag] = "excluded_document_type:" + document_type.loc[~flag].fillna("UNKNOWN")
    return reasons


def _sku_metrics(df: pd.DataFrame) -> list[str]:
    return [
        f"Total Unique SKUs: {df['sku_code'].nunique() if 'sku_code' in df.columns else df.shape[0]}",
        f"Imputed values: {df['imputation_notes'].notna().sum()}",
        f"Weight conflicts: {df['weight_conflict_flag'].sum() if 'weight_conflict_flag' in df.columns else 0}",
        f"Top 3 Categories: {', '.join(df['category'].value_counts().head(3).index) if 'category' in df.columns else 'N/A'}"
    ]

@log_quality(_sku_metrics)
def clean_sku_master(raw: pd.DataFrame) -> pd.DataFrame:
    frame = _replace_blank_like_values(raw.copy())
    sap_code_2 = _to_nullable_code(frame["SAP Code (2)"])
    valid_rows = sap_code_2.notna() & frame["Product Name (VN)"].notna()
    frame = frame.loc[valid_rows].copy()

    text_cols = ["No", "Type", "COM Code", "Product Name (VN)", "Unit", "Category"]
    for column in text_cols:
        frame[column] = frame[column].astype("string").str.strip()

    frame["Updated Date"] = pd.to_datetime(frame["Updated Date"], errors="coerce")
    frame["sap_code"] = _to_nullable_code(frame["SAP Code"])
    frame["sap_code_2"] = _to_nullable_code(frame["SAP Code (2)"])
    frame["sku_code"] = frame["sap_code_2"]

    int_cols = [
        "Pcs per Carton",
        "Carton Length (mm)",
        "Carton Width (mm)",
        "Carton Height (mm)",
        "Pcs per Pallet",
        "Cartons per Layer",
        "Layers per Pallet",
        "Loose Pcs per Pallet",
    ]
    for column in int_cols:
        frame[column] = _to_nullable_int(frame[column])

    float_cols = ["Volume (m³)", "CBM incl. Flap (m³)", "Pcs Weight (kg)", "Carton Weight (kg)"]
    for column in float_cols:
        frame[column] = _to_float(frame[column])

    placeholder_zero_cols = [
        "Carton Length (mm)",
        "Carton Width (mm)",
        "Carton Height (mm)",
        "Pcs per Pallet",
        "Cartons per Layer",
        "Layers per Pallet",
        "Volume (m³)",
        "Pcs Weight (kg)",
        "Carton Weight (kg)",
    ]
    for column in placeholder_zero_cols:
        frame[column] = _zero_to_na(frame[column])

    frame["carton_volume_from_dims_m3"] = (
        frame["Carton Length (mm)"] * frame["Carton Width (mm)"] * frame["Carton Height (mm)"]
    ) / 1_000_000_000
    frame["carton_volume_from_dims_m3"] = frame["carton_volume_from_dims_m3"].where(
        frame[["Carton Length (mm)", "Carton Width (mm)", "Carton Height (mm)"]].notna().all(axis=1)
    )

    frame["pallet_base_pcs_capacity"] = (
        frame["Pcs per Carton"] * frame["Cartons per Layer"] * frame["Layers per Pallet"]
    )
    frame["pallet_base_pcs_capacity"] = frame["pallet_base_pcs_capacity"].where(
        frame[["Pcs per Carton", "Cartons per Layer", "Layers per Pallet"]].notna().all(axis=1)
    )

    loose_residual = frame["Pcs per Pallet"] - frame["pallet_base_pcs_capacity"]
    valid_loose_residual = loose_residual.notna() & loose_residual.ge(0) & loose_residual.eq(loose_residual.round())
    imputation_notes = pd.Series(pd.NA, index=frame.index, dtype="string")
    missing_loose = frame["Loose Pcs per Pallet"].isna()
    frame.loc[missing_loose & valid_loose_residual, "Loose Pcs per Pallet"] = (
        loose_residual.loc[missing_loose & valid_loose_residual].round().astype("Int64")
    )
    imputation_notes = _append_imputation_note(
        imputation_notes,
        missing_loose & frame["Loose Pcs per Pallet"].notna(),
        "loose_pcs_from_pallet_residual",
    )

    both_weights_present = (
        frame["Pcs Weight (kg)"].notna()
        & frame["Carton Weight (kg)"].notna()
        & frame["Pcs per Carton"].notna()
    )

    derived_carton_weight = frame["Pcs Weight (kg)"] * frame["Pcs per Carton"]
    derived_piece_weight = frame["Carton Weight (kg)"] / frame["Pcs per Carton"]
    can_derive_carton = (
        frame["Carton Weight (kg)"].isna()
        & frame["Pcs Weight (kg)"].notna()
        & frame["Pcs per Carton"].notna()
    )
    can_derive_piece = (
        frame["Pcs Weight (kg)"].isna()
        & frame["Carton Weight (kg)"].notna()
        & frame["Pcs per Carton"].notna()
    )
    frame.loc[can_derive_carton, "Carton Weight (kg)"] = derived_carton_weight.loc[can_derive_carton]
    frame.loc[can_derive_piece, "Pcs Weight (kg)"] = derived_piece_weight.loc[can_derive_piece]
    imputation_notes = _append_imputation_note(imputation_notes, can_derive_carton, "carton_weight_from_piece_weight")
    imputation_notes = _append_imputation_note(imputation_notes, can_derive_piece, "piece_weight_from_carton_weight")

    weight_delta = (frame["Carton Weight (kg)"] - (frame["Pcs Weight (kg)"] * frame["Pcs per Carton"])).abs()
    frame["weight_conflict_flag"] = (both_weights_present & weight_delta.gt(1e-9)).astype("Int64")
    frame["imputation_notes"] = imputation_notes

    rename = {
        "Updated Date": "updated_date",
        "No": "sku_row_no",
        "Type": "type",
        "COM Code": "com_code",
        "Product Name (VN)": "product_name",
        "Unit": "unit",
        "Category": "category",
        "Pcs per Carton": "pcs_per_carton",
        "Carton Length (mm)": "carton_length_mm",
        "Carton Width (mm)": "carton_width_mm",
        "Carton Height (mm)": "carton_height_mm",
        "Pcs per Pallet": "pcs_per_pallet",
        "Cartons per Layer": "cartons_per_layer",
        "Layers per Pallet": "layers_per_pallet",
        "Loose Pcs per Pallet": "loose_pcs_per_pallet",
        "Volume (m³)": "volume_m3",
        "CBM incl. Flap (m³)": "cbm_incl_flap_m3",
        "Pcs Weight (kg)": "pcs_weight_kg",
        "Carton Weight (kg)": "carton_weight_kg",
    }
    frame = frame.rename(columns=rename)
    keep = [
        "sku_code",
        "sap_code",
        "sap_code_2",
        "updated_date",
        "sku_row_no",
        "type",
        "com_code",
        "product_name",
        "unit",
        "category",
        "pcs_per_carton",
        "carton_length_mm",
        "carton_width_mm",
        "carton_height_mm",
        "pcs_per_pallet",
        "cartons_per_layer",
        "layers_per_pallet",
        "loose_pcs_per_pallet",
        "volume_m3",
        "carton_volume_from_dims_m3",
        "cbm_incl_flap_m3",
        "pcs_weight_kg",
        "carton_weight_kg",
        "pallet_base_pcs_capacity",
        "weight_conflict_flag",
        "imputation_notes",
    ]
    for column in keep:
        if column not in frame.columns:
            frame[column] = pd.NA
    frame = frame[keep].drop_duplicates("sku_code", keep="first")
    return frame


def _dist_metrics(df: pd.DataFrame) -> list[str]:
    return [
        f"Unique Customers: {df['customer_key'].nunique()}",
        f"Ambiguous locations (Multi-branch): {df['customer_key_is_ambiguous'].sum()}",
        f"Unusable/Unknown geography: {df['province'].eq('Unknown').sum()}",
        f"Top 3 Provinces: {', '.join(df['province'].value_counts().head(3).index)}"
    ]

@log_quality(_dist_metrics)
def clean_distributors(raw: pd.DataFrame) -> pd.DataFrame:
    frame = _replace_blank_like_values(raw.copy())
    frame["Customer Name"] = frame["Customer Name"].ffill()
    frame = frame.dropna(subset=["Customer Name", "Delivery Address"]).copy()
    frame["customer_name"] = _normalize_string(frame["Customer Name"])
    frame["customer_key"] = frame["customer_name"].map(normalize_text)
    
    # Parse the address components using vietnamadminunits
    
    # Cache addresses to speed up vietnamadminunits
    unique_addresses = frame["Delivery Address"].dropna().unique()
    address_cache = {}
    for i, addr in enumerate(unique_addresses):
        if i % 100 == 0:
            print(f"Parsing address {i}/{len(unique_addresses)}...")
        address_cache[addr] = parse_address_components(addr)
    
    # Map from the address cache directly to avoid eager evaluation / re-parsing
    components = list(frame["Delivery Address"].map(address_cache))

    frame["address_street"] = _normalize_string(pd.Series([c["street"] for c in components], index=frame.index))
    frame["address_ward"] = _normalize_string(pd.Series([c["ward"] for c in components], index=frame.index))
    frame["address_district"] = _normalize_string(pd.Series([c["district"] for c in components], index=frame.index))
    frame["address_province"] = _normalize_string(pd.Series([c["province"] for c in components], index=frame.index))
    frame["latitude"] = [c.get("latitude") for c in components]
    frame["longitude"] = [c.get("longitude") for c in components]
    frame["delivery_address"] = _normalize_string(pd.Series([c["full_address"] for c in components], index=frame.index))
    
    frame["customer_location_key"] = (
        frame["customer_key"] + " | " + frame["delivery_address"].map(normalize_text)
    )
    frame["province"] = frame["address_province"]
    frame["district"] = frame["address_district"]
    frame["ward"] = frame["address_ward"]
    frame["region"] = frame["province"].map(region_group)
    def _get_base_address(addr: str) -> str:
        if pd.isna(addr): return ""
        first_part = str(addr).split(',')[0].lower()
        first_part = re.sub(r'\b(số|đường|tầng|khu phố|kp|ấp|thôn|lô|km|kcn|tòa nhà|tòa)\b', '', first_part)
        return re.sub(r'[^a-z0-9]', '', first_part)

    frame["base_address"] = frame["delivery_address"].apply(_get_base_address)
    frame["address_length"] = frame["delivery_address"].str.len()
    frame["has_geo"] = frame["latitude"].notna()
    
    # Sort so the record with the most complete information is kept
    frame = frame.sort_values(
        ["customer_key", "province", "has_geo", "address_length"], 
        ascending=[True, True, False, False]
    )

    # First deduplicate by exact lat/long
    frame = frame.drop_duplicates(subset=["customer_key", "province", "latitude", "longitude"])
    
    # Next deduplicate by base address (excluding empty base addresses)
    valid_base_mask = frame["base_address"] != ""
    duplicates = frame.duplicated(subset=["customer_key", "province", "base_address"]) & valid_base_mask
    frame = frame[~duplicates]

    frame = frame.drop(columns=["base_address", "address_length", "has_geo"])
    dedupe_columns = ["customer_key", "province", "latitude", "longitude"]
    frame = frame.drop_duplicates(subset=dedupe_columns).copy()
    frame["customer_location_count"] = frame.groupby("customer_key")["customer_location_key"].transform("nunique")
    frame["customer_key_is_ambiguous"] = frame["customer_location_count"].gt(1)
    frame["customer_match_status"] = "unique_resolvable_customer_geography"
    frame.loc[frame["customer_key_is_ambiguous"], "customer_match_status"] = "ambiguous_multi_location_customer"
    unusable_geo = frame["province"].eq("Unknown")
    frame.loc[unusable_geo, "customer_match_status"] = "unusable_or_missing_geography"
    frame = add_distance_columns(frame)
    keep = [
        "customer_name",
        "customer_key",
        "customer_location_key",
        "delivery_address",
        "customer_location_count",
        "customer_key_is_ambiguous",
        "customer_match_status",
        "province",
        "district",
        "ward",
        "region",
        "latitude",
        "longitude",
        "distance_from_my_phuoc_km",
        "distance_from_vinh_loc_km",
        "Source Sheet",
    ]
    return frame[keep].reset_index(drop=True)


def _build_segment_override_map(overrides: pd.DataFrame | None) -> dict[str, str]:
    if overrides is None or overrides.empty:
        return {}
    columns = {col.strip().lower(): col for col in overrides.columns}
    if "customer_segment" not in columns:
        raise ValueError("Segment overrides must include a 'customer_segment' column")
    if "customer_key" in columns:
        keys = overrides[columns["customer_key"]].map(normalize_text)
    elif "customer_name" in columns:
        keys = overrides[columns["customer_name"]].map(normalize_text)
    else:
        raise ValueError("Segment overrides must include 'customer_key' or 'customer_name'")
    segments = overrides[columns["customer_segment"]].astype("string")
    mapping = {
        key: segment
        for key, segment in zip(keys, segments, strict=False)
        if pd.notna(key) and pd.notna(segment) and str(segment).strip()
    }
    return mapping


def _shipment_metrics(df: pd.DataFrame) -> list[str]:
    lines = [
        f"Total Quantity: {df['quantity'].sum():,.2f}",
        f"Total Volume (CBM): {df['cbm_total'].sum():,.2f}",
        f"Date Range: {df['created_date'].min().strftime('%Y-%m-%d')} to {df['created_date'].max().strftime('%Y-%m-%d')}",
        f"Unknown Provinces remaining: {df['province'].eq('Unknown').sum()}",
        f"Geographic source breakdown:"
    ]
    for source, count in df['geography_source'].value_counts().items():
        lines.append(f"    * {source}: {count}")
    return lines

@log_quality(_shipment_metrics)
def clean_shipments(
    raw: pd.DataFrame, distributors: pd.DataFrame, segment_overrides: pd.DataFrame | None = None
) -> pd.DataFrame:
    frame = _replace_blank_like_values(raw.copy())
    frame["sku_code"] = _to_nullable_code(frame["SKU Code (CMMF)"])
    frame["document_no"] = _to_nullable_code(frame["Document No."]).fillna("unknown")
    frame["source_warehouse"] = _normalize_string(frame["Source Warehouse"], default="unknown")
    frame["order_id"] = frame["source_warehouse"] + "-" + frame["document_no"]
    frame["document_type"] = _normalize_document_type(frame["Document Type"])
    frame["unit"] = _normalize_string(frame["Unit"], default="")
    quantity = pd.to_numeric(frame["Quantity"], errors="coerce")
    cbm_total = pd.to_numeric(frame["CBM Total"], errors="coerce")
    frame["quantity"] = quantity
    frame["cbm_total"] = cbm_total
    frame["quantity_missing_flag"] = quantity.isna()
    frame["cbm_missing_flag"] = cbm_total.isna()
    frame["data_error_flag"] = frame["quantity_missing_flag"] | frame["cbm_missing_flag"]
    frame["created_date"] = pd.to_datetime(frame["Created Date"], errors="coerce")
    frame["ship_to_customer"] = _normalize_string(frame["Ship-to Customer"], default="unknown").str.replace(r"\s*\(FOC\)\s*", "", regex=True, flags=re.IGNORECASE)
    frame["customer_key"] = frame["ship_to_customer"].map(normalize_text)
    
    b2b_pattern = r"CÔNG TY|CTY|HỘ KINH DOANH|HKD|CHI NHÁNH|SIÊU THỊ|CỬA HÀNG|\bCH\b|ĐẠI LÝ|NPP|TTMS|TRUNG TÂM|TNHH|COOP|GO!|EB|LOTTE|AEON|MM MEGA|DOANH NGHIỆP|DNTN|PHÂN PHỐI|LTD|LIMITED|HTX|HỢP TÁC XÃ|SCHENKER|LOGISTICS|TAX"
    b2b_mask = frame["ship_to_customer"].str.contains(b2b_pattern, case=False, na=False)
    frame["channel"] = "B2C"
    frame.loc[b2b_mask, "channel"] = "B2B"
    
    frame.loc[frame["ship_to_customer"].eq("unknown"), "customer_key"] = "UNKNOWN"
    frame["analysis_document_flag"] = _analysis_document_flag(frame["document_type"])
    frame["exclusion_reason"] = _analysis_exclusion_reason(frame["document_type"], frame["analysis_document_flag"])

    distributor_match = _build_distributor_match_table(distributors)
    frame = frame.merge(distributor_match, on="customer_key", how="left")
    frame["customer_match_status"] = frame["customer_match_status"].fillna("unmatched_customer_key")
    frame["customer_location_count"] = frame["customer_location_count"].fillna(0).astype("Int64")
    frame["customer_key_is_ambiguous"] = frame["customer_key_is_ambiguous"].astype("boolean").fillna(False)

    # Build cache of parsed components for all unique ship-to customer names to extract coordinates
    unique_ship_to = frame["ship_to_customer"].dropna().unique()
    ship_to_cache = {name: parse_address_components(name) for name in unique_ship_to}

    frame["parsed_province"] = [ship_to_cache[name]["province"] for name in frame["ship_to_customer"]]
    frame["parsed_district"] = [ship_to_cache[name]["district"] for name in frame["ship_to_customer"]]
    frame["parsed_ward"] = [ship_to_cache[name]["ward"] for name in frame["ship_to_customer"]]
    frame["latitude_parsed"] = [ship_to_cache[name]["latitude"] for name in frame["ship_to_customer"]]
    frame["longitude_parsed"] = [ship_to_cache[name]["longitude"] for name in frame["ship_to_customer"]]

    frame["province_alias_match_flag"] = frame["parsed_province"].ne("Unknown")
    parsed_has_geo = frame["parsed_province"].ne("Unknown")

    frame["geography_source"] = "unresolved"
    distributor_geo_mask = frame["customer_match_status"].isin(["unique_resolvable_customer_geography", "ambiguous_multi_location_customer"])
    transaction_geo_mask = ~distributor_geo_mask & parsed_has_geo

    frame["province"] = "Unknown"
    frame["district"] = ""
    frame["ward"] = ""
    frame["region"] = "Unknown"
    frame["latitude"] = pd.Series([float("nan")] * len(frame), dtype="float64", index=frame.index)
    frame["longitude"] = pd.Series([float("nan")] * len(frame), dtype="float64", index=frame.index)

    # Assign coordinates and regions for distributor matched customers
    frame.loc[distributor_geo_mask, "province"] = frame.loc[distributor_geo_mask, "province_distributor"]
    frame.loc[distributor_geo_mask, "district"] = frame.loc[distributor_geo_mask, "district_distributor"]
    frame.loc[distributor_geo_mask, "ward"] = frame.loc[distributor_geo_mask, "ward_distributor"]
    frame.loc[distributor_geo_mask, "region"] = frame.loc[distributor_geo_mask, "region_distributor"]
    frame.loc[distributor_geo_mask, "latitude"] = frame.loc[distributor_geo_mask, "latitude_distributor"]
    frame.loc[distributor_geo_mask, "longitude"] = frame.loc[distributor_geo_mask, "longitude_distributor"]
    frame.loc[distributor_geo_mask, "geography_source"] = "distributor_match"

    # Assign coordinates and regions for transaction text parsed customers
    frame.loc[transaction_geo_mask, "province"] = frame.loc[transaction_geo_mask, "parsed_province"]
    frame.loc[transaction_geo_mask, "district"] = frame.loc[transaction_geo_mask, "parsed_district"]
    frame.loc[transaction_geo_mask, "ward"] = frame.loc[transaction_geo_mask, "parsed_ward"]
    frame.loc[transaction_geo_mask, "region"] = frame.loc[transaction_geo_mask, "province"].map(region_group)
    frame.loc[transaction_geo_mask, "latitude"] = frame.loc[transaction_geo_mask, "latitude_parsed"]
    frame.loc[transaction_geo_mask, "longitude"] = frame.loc[transaction_geo_mask, "longitude_parsed"]
    frame.loc[transaction_geo_mask, "geography_source"] = "transaction_text_parse"

    frame.loc[frame["ship_to_customer"].eq("unknown"), "customer_match_status"] = "missing_customer_name"

    frame["province"] = frame["province"].fillna("Unknown")
    frame["region"] = frame["province"].map(region_group)

    # Filter out shipments where the customer doesn't exist in the distributor network
    matched_mask = ~frame["customer_match_status"].isin(["unmatched_customer_key", "missing_customer_name"])
    frame = frame[matched_mask].copy()

    frame["known_geography_flag"] = frame["province"].ne("Unknown")
    frame["segment_source"] = "unresolved"
    frame["customer_segment"] = "Unknown"
    frame["segment_confidence"] = "unknown"
    eligible_segment_mask = frame["analysis_document_flag"] & frame["ship_to_customer"].ne("unknown")
    derived_segment = frame.loc[eligible_segment_mask, "ship_to_customer"].map(classify_customer_segment)
    frame.loc[eligible_segment_mask, "customer_segment"] = derived_segment
    resolved_segment_idx = derived_segment[derived_segment.ne("Unknown")].index
    unresolved_segment_idx = derived_segment[derived_segment.eq("Unknown")].index
    frame.loc[resolved_segment_idx, "segment_source"] = "customer_name_rule"
    frame.loc[unresolved_segment_idx, "segment_source"] = "unresolved"
    frame.loc[resolved_segment_idx, "segment_confidence"] = "rule"

    override_map = _build_segment_override_map(segment_overrides)
    if override_map:
        override_idx = frame["customer_key"].isin(override_map.keys()) & eligible_segment_mask
        frame.loc[override_idx, "customer_segment"] = frame.loc[override_idx, "customer_key"].map(override_map)
        frame.loc[override_idx, "segment_source"] = "override_mapping"
        frame.loc[override_idx, "segment_confidence"] = "override"

    frame = add_distance_columns(frame)
    keep = [
        "order_id",
        "document_no",
        "document_type",
        "analysis_document_flag",
        "exclusion_reason",
        "source_warehouse",
        "sku_code",
        "unit",
        "quantity",
        "cbm_total",
        "quantity_missing_flag",
        "cbm_missing_flag",
        "data_error_flag",
        "ship_to_customer",
        "customer_key",
        "customer_match_status",
        "customer_location_count",
        "customer_key_is_ambiguous",
        "geography_source",
        "known_geography_flag",
        "customer_segment",
        "segment_source",
        "segment_confidence",
        "created_date",
        "province",
        "district",
        "ward",
        "region",
        "parsed_province",
        "province_alias_match_flag",
        "latitude",
        "longitude",
        "distance_from_my_phuoc_km",
        "distance_from_vinh_loc_km",
        "channel",
    ]
    return frame[keep]


def _build_distributor_match_table(distributors: pd.DataFrame) -> pd.DataFrame:
    valid_status = ["unique_resolvable_customer_geography", "ambiguous_multi_location_customer"]
    unique = distributors[distributors["customer_match_status"].isin(valid_status)].copy()
    unique["has_geo"] = unique["latitude"].notna()
    
    unique["name_matches_province"] = unique.apply(
        lambda row: normalize_text(row["province"]) in row["customer_key"] if pd.notna(row["province"]) else False,
        axis=1
    )
    
    unique = unique.sort_values(
        by=["customer_key", "name_matches_province", "has_geo", "Source Sheet"],
        ascending=[True, False, False, True]
    )
    unique = unique.drop_duplicates("customer_key", keep="first")
    counts = (
        distributors.groupby("customer_key")
        .agg(
            customer_location_count=("customer_location_key", "nunique"),
            customer_key_is_ambiguous=("customer_key_is_ambiguous", "max"),
            customer_match_status=("customer_match_status", "first"),
        )
        .reset_index()
    )
    match = counts.merge(
        unique[
            [
                "customer_key",
                "province",
                "district",
                "ward",
                "region",
                "latitude",
                "longitude",
                "distance_from_my_phuoc_km",
                "distance_from_vinh_loc_km",
            ]
        ].rename(
            columns={
                "province": "province_distributor",
                "district": "district_distributor",
                "ward": "ward_distributor",
                "region": "region_distributor",
                "latitude": "latitude_distributor",
                "longitude": "longitude_distributor",
                "distance_from_my_phuoc_km": "distance_from_my_phuoc_km_distributor",
                "distance_from_vinh_loc_km": "distance_from_vinh_loc_km_distributor",
            }
        ),
        on="customer_key",
        how="left",
    )
    return match


def classify_customer_segment(customer: object) -> str:
    text = normalize_text(customer)
    modern_keywords = [
        "AEON",
        "BIG C",
        "CENTRAL RETAIL",
        "CO.OP",
        "COOP",
        "DIEN MAY XANH",
        "FPT",
        "GO!",
        "KOHNAN",
        "LOTTE",
        "MM MEGA",
        "NGUYEN KIM",
        "THAP NHAT PHONG",
        "THE GIOI DI DONG",
        "WINCOMMERCE",
    ]
    if any(keyword in text for keyword in modern_keywords):
        return "Modern Trade"
    if text == "UNKNOWN":
        return "Unknown"
    return "Traditional Trade / Distributor"


if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path
    
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    
    try:
        from src.logage2026.loading import load_sku_master, load_transactions, load_distributors, load_segment_overrides
        from src.logage2026.config import CLEANED_DIR
    except ImportError:
        from loading import load_sku_master, load_transactions, load_distributors, load_segment_overrides
        from config import CLEANED_DIR
        
    parser = argparse.ArgumentParser(description="Clean datasets for LOGage 2026 analysis.")
    parser.add_argument("--sku", action="store_true", help="Clean SKU Master Data only")
    parser.add_argument("--distributor", action="store_true", help="Clean Distributor Network only")
    parser.add_argument("--shipment", action="store_true", help="Clean Outbound Shipment Transactions only")
    parser.add_argument("--geography", action="store_true", help="Run geography address parsing / cleaning demo")
    parser.add_argument("--all", action="store_true", help="Clean all datasets (default)")
    
    args = parser.parse_args()
    
    if not (args.sku or args.distributor or args.shipment or args.geography):
        args.all = True
        
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.sku or args.all:
        sku = clean_sku_master(load_sku_master())
        out_path = CLEANED_DIR / "sku_master_cleaned.csv"
        sku.to_csv(out_path, index=False)
        
    if args.distributor or args.all:
        dist = clean_distributors(load_distributors())
        out_path = CLEANED_DIR / "distributors_cleaned.csv"
        dist.to_csv(out_path, index=False)
        
    if args.shipment or args.all:
        dist = clean_distributors(load_distributors())
        overrides = load_segment_overrides()
        shipments = clean_shipments(load_transactions(), dist, segment_overrides=overrides)
        out_path = CLEANED_DIR / "shipments_cleaned.csv"
        shipments.to_csv(out_path, index=False)
