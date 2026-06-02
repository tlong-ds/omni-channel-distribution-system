import math
import re
import unicodedata

import pandas as pd

from .config import HCMC_DISTRICT_COORDINATES, WAREHOUSE_COORDINATES


PROVINCE_ALIASES = {
    "AN GIANG": "An Giang",
    "BA RIA": "Ba Ria - Vung Tau",
    "BAC GIANG": "Bac Giang",
    "BAC NINH": "Bac Ninh",
    "BINH DINH": "Binh Dinh",
    "BINH DUONG": "Binh Duong",
    "BINH PHUOC": "Binh Phuoc",
    "BINH THUAN": "Binh Thuan",
    "CAN THO": "Can Tho",
    "DA NANG": "Da Nang",
    "DONG NAI": "Dong Nai",
    "DONG THAP": "Dong Thap",
    "HA NOI": "Ha Noi",
    "HAI PHONG": "Hai Phong",
    "HO CHI MINH": "Ho Chi Minh City",
    "HCM": "Ho Chi Minh City",
    "KHANH HOA": "Khanh Hoa",
    "KIEN GIANG": "Kien Giang",
    "LAM DONG": "Lam Dong",
    "LONG AN": "Long An",
    "NGHE AN": "Nghe An",
    "QUANG NAM": "Quang Nam",
    "TIEN GIANG": "Tien Giang",
    "TP HCM": "Ho Chi Minh City",
    "TP. HCM": "Ho Chi Minh City",
    "TPHCM": "Ho Chi Minh City",
    "VINH LONG": "Vinh Long",
}

PROVINCE_COORDINATES = {
    "An Giang": (10.521, 105.125),
    "Ba Ria - Vung Tau": (10.541, 107.243),
    "Bac Giang": (21.273, 106.194),
    "Bac Ninh": (21.186, 106.076),
    "Binh Dinh": (13.782, 109.219),
    "Binh Duong": (11.050, 106.667),
    "Binh Phuoc": (11.751, 106.723),
    "Binh Thuan": (10.933, 108.101),
    "Can Tho": (10.045, 105.746),
    "Da Nang": (16.067, 108.221),
    "Dong Nai": (10.957, 106.843),
    "Dong Thap": (10.493, 105.689),
    "Ha Noi": (21.028, 105.854),
    "Hai Phong": (20.844, 106.688),
    "Ho Chi Minh City": (10.776, 106.701),
    "Khanh Hoa": (12.238, 109.196),
    "Kien Giang": (10.012, 105.080),
    "Lam Dong": (11.575, 108.142),
    "Long An": (10.695, 106.243),
    "Nghe An": (18.679, 105.681),
    "Quang Nam": (15.539, 108.019),
    "Tien Giang": (10.449, 106.342),
    "Vinh Long": (10.254, 105.973),
}

HCMC_DISTRICT_ALIASES = {
    "BINH CHANH": "Binh Chanh",
    "BINH TAN": "Binh Tan",
    "QUAN 1": "District 1",
    "Q 1": "District 1",
    "QUAN 3": "District 3",
    "Q 3": "District 3",
    "QUAN 5": "District 5",
    "Q 5": "District 5",
    "QUAN 7": "District 7",
    "Q 7": "District 7",
    "QUAN 10": "District 10",
    "Q 10": "District 10",
    "QUAN 12": "District 12",
    "Q 12": "District 12",
    "GO VAP": "Go Vap",
    "PHU NHUAN": "Phu Nhuan",
    "TAN BINH": "Tan Binh",
    "TAN PHU": "Tan Phu",
    "THU DUC": "Thu Duc",
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).upper().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text)


def parse_province(text: object) -> str:
    normalized = normalize_text(text)
    for needle, province in PROVINCE_ALIASES.items():
        if needle in normalized:
            return province
    return "Unknown"


def parse_hcmc_district(text: object) -> str:
    normalized = normalize_text(text)
    if parse_province(text) != "Ho Chi Minh City":
        return ""
    for needle, district in HCMC_DISTRICT_ALIASES.items():
        if needle in normalized:
            return district
    return "HCMC unspecified"


def region_group(province: str) -> str:
    if province == "Unknown":
        return "Unknown"
    if province == "Ho Chi Minh City":
        return "HCMC"
    if province in {"Binh Duong", "Dong Nai", "Long An", "Ba Ria - Vung Tau", "Binh Phuoc", "Tien Giang"}:
        return "Southeast / HCMC fringe"
    if province in {"Can Tho", "An Giang", "Dong Thap", "Kien Giang", "Vinh Long"}:
        return "Mekong Delta"
    if province in {"Ha Noi", "Hai Phong", "Bac Ninh", "Bac Giang"}:
        return "North"
    if province in {"Da Nang", "Quang Nam", "Binh Dinh", "Khanh Hoa", "Binh Thuan", "Nghe An"}:
        return "Central"
    return "Other Vietnam"


def coordinates_for(province: str, district: str = "") -> tuple[float, float] | tuple[None, None]:
    if district in HCMC_DISTRICT_COORDINATES:
        return HCMC_DISTRICT_COORDINATES[district]
    return PROVINCE_COORDINATES.get(province, (None, None))


def haversine_km(origin: tuple[float, float], destination: tuple[float, float]) -> float:
    lat1, lon1 = origin
    lat2, lon2 = destination
    if lat2 is None or lon2 is None:
        return float("nan")
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def add_distance_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    coords = result.apply(lambda row: coordinates_for(row["province"], row.get("hcmc_district", "")), axis=1)
    result["latitude"] = [coord[0] for coord in coords]
    result["longitude"] = [coord[1] for coord in coords]
    for warehouse, origin in WAREHOUSE_COORDINATES.items():
        result[f"distance_from_{warehouse.lower().replace(' ', '_')}_km"] = [
            haversine_km(origin, (lat, lon)) for lat, lon in zip(result["latitude"], result["longitude"])
        ]
    return result

