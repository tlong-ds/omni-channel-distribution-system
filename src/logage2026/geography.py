import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import math
import re
import unicodedata
import vietnamadminunits as vau

import pandas as pd

from src.logage2026.config import WAREHOUSE_COORDINATES


# Mapping of old district names that became wards post-2025 reform
# Value is (new_ward_name, province_to_append_if_no_province_present)
_DISTRICT_TO_WARD_RENAMES: dict[str, tuple[str, str]] = {
    "hà đông": ("Phường Hà Đông", "Thành phố Hà Nội"),
}

# Regex to detect a city/town inside a province address
# e.g. "Thành phố Mỹ Tho, Tỉnh Tiền Giang"  →  strip "Thành phố Mỹ Tho,"
_CITY_IN_PROVINCE_RE = re.compile(
    r"(?:Thành\s+ph[oố]\s+\S[\w\s]*?|Th[iị]\s+x[aã]\s+\S[\w\s]*?)"
    r",\s*(?=(?:Tỉnh|Th[aà]nh\s+ph[oố]\s+(?!Hồ\s+Chí\s+Minh|Hà\s+Nội|Hải\s+Phòng|Đà\s+Nẵng|Huế)))",
    re.IGNORECASE,
)


def preprocess_address(address: str) -> str:
    """Normalise a raw distributor address before passing it to vietnamadminunits.

    Steps applied (in order):
    1. Strip parenthetical comments – e.g. "(Gần Vòng Xoay An Lạc)".
    2. Remove a sub-city level ("Thành phố X" or "Thị xã X") when the address
       already contains a Tỉnh/Thành phố top-level province.  These inner cities
       were abolished by the 2025 administrative reform.
    3. Apply known district→ward renames (e.g. "Hà Đông" → "Phường Hà Đông").
    """
    # 1. Remove bracketed comments
    address = re.sub(r"\(.*?\)", "", address).strip().rstrip(",").strip()

    # 2. Remove inner city/town when a province is present
    address = _CITY_IN_PROVINCE_RE.sub("", address).strip().rstrip(",").strip()

    # 3. District→ward renames — only replace if not already preceded by "Phường"
    for old_token, (new_ward, province_hint) in _DISTRICT_TO_WARD_RENAMES.items():
        pattern = r"(?<![Pp]h[\u01b0\u01a1][\u1edd]ng\s)\b" + re.escape(old_token) + r"\b"
        if re.search(pattern, address, flags=re.IGNORECASE):
            address = re.sub(pattern, new_ward, address, flags=re.IGNORECASE)
            # Append province if no province keyword already present
            if not re.search(r"(?:Tỉnh|Thành\s+phố|Tp\.?)", address, re.IGNORECASE):
                address = address.rstrip(",").strip() + ", " + province_hint

    return address.strip()


_PROVINCE_EXTRACT_RE = re.compile(
    r"(?:Tỉnh|Th[aà]nh\s+ph[oố])\s+([\w\s\-]+?)(?:,|$)",
    re.IGNORECASE,
)

# Bare province/city abbreviations with no Tỉnh/Thành phố prefix
# Also includes known old district names (Quận/Huyện) that imply a province
_BARE_PROVINCE_RE = re.compile(
    r"(?:^|,\s*)(?:TP\.?\s*|Tp\.?\s*|Quận\s*|Q\.?\s*)?(?P<name>"
    r"Hà\s*Nội|Hà\s*nội|HN|H\.?N\.?"
    r"|Hồ\s*Chí\s*Minh|TP\.?\s*HCM|Tp\.?\s*HCM|HCM|TP\.?HCM"
    r"|Hải\s*Phòng|Đà\s*Nẵng|Huế"
    r"|Bình\s*Dương|Đồng\s*Nai|Bắc\s*Ninh|Bắc\s*Giang"
    r"|Hưng\s*Yên|Hải\s*Dương|Vĩnh\s*Phúc|Thái\s*Nguyên"
    r"|Hoàng\s*Mai|Thanh\s*Xuân|Cầu\s*Giấy|Long\s*Biên|Nam\s*Từ\s*Liêm|Bắc\s*Từ\s*Liêm|Tây\s*Hồ|Ba\s*Đình|Hoàn\s*Kiếm|Hai\s*Bà\s*Trưng|Hà\s*Đông"
    r"|Tân\s*Bình|Tân\s*Phú|Bình\s*Tân|Gò\s*Vấp|Bình\s*Thạnh|Phú\s*Nhuận|Quận\s*12|Quận\s*9"
    r")(?:\s*,|\s*$)",
    re.IGNORECASE,
)

_BARE_PROVINCE_MAP: dict[str, str] = {
    "hà nội": "Hà Nội", "hn": "Hà Nội", "h.n.": "Hà Nội",
    "hồ chí minh": "Hồ Chí Minh", "hcm": "Hồ Chí Minh", "tp.hcm": "Hồ Chí Minh",
    "tp hcm": "Hồ Chí Minh",
    "hải phòng": "Hải Phòng", "đà nẵng": "Đà Nẵng", "huế": "Huế",
    "bình dương": "Bình Dương", "đồng nai": "Đồng Nai",
    "bắc ninh": "Bắc Ninh", "bắc giang": "Bắc Giang",
    "hưng yên": "Hưng Yên", "hải dương": "Hải Dương",
    "vĩnh phúc": "Vĩnh Phúc", "thái nguyên": "Thái Nguyên",
    # Old Hà Nội districts — imply Hà Nội province
    "hoàng mai": "Hà Nội", "thanh xuân": "Hà Nội", "cầu giấy": "Hà Nội",
    "long biên": "Hà Nội", "nam từ liêm": "Hà Nội", "bắc từ liêm": "Hà Nội",
    "tây hồ": "Hà Nội", "ba đình": "Hà Nội", "hoàn kiếm": "Hà Nội",
    "hai bà trưng": "Hà Nội", "hà đông": "Hà Nội",
    # Old HCM districts — imply Hồ Chí Minh province
    "tân bình": "Hồ Chí Minh", "tân phú": "Hồ Chí Minh",
    "bình tân": "Hồ Chí Minh", "gò vấp": "Hồ Chí Minh",
    "bình thạnh": "Hồ Chí Minh", "phú nhuận": "Hồ Chí Minh",
    "quận 12": "Hồ Chí Minh", "quận 9": "Hồ Chí Minh",
}

_PROVINCE_SHORT_NAMES: dict[str, str] = {
    "yên bái": "Yên Bái",
    "tiền giang": "Tiền Giang",
    "quảng nam": "Quảng Nam",
    "quảng bình": "Quảng Bình",
    "quảng trị": "Quảng Trị",
    "bình phước": "Bình Phước",
    "bình dương": "Bình Dương",
    "trà vinh": "Trà Vinh",
    "sóc trăng": "Sóc Trăng",
    "bến tre": "Bến Tre",
    "hậu giang": "Hậu Giang",
    "bạc liêu": "Bạc Liêu",
    "đồng tháp": "Đồng Tháp",
    "vĩnh long": "Vĩnh Long",
    "an giang": "An Giang",
    "kiên giang": "Kiên Giang",
    "đắk nông": "Đắk Nông",
    "kon tum": "Kon Tum",
    "ninh bình": "Ninh Bình",
    "nam định": "Nam Định",
    "hà nam": "Hà Nam",
    "thái bình": "Thái Bình",
    "hải dương": "Hải Dương",
    "hưng yên": "Hưng Yên",
    "vĩnh phúc": "Vĩnh Phúc",
    "bắc kạn": "Bắc Kạn",
    "hà giang": "Hà Giang",
    "yên bái": "Yên Bái",
    "lào cai": "Lào Cai",
    "lai châu": "Lai Châu",
    "điện biên": "Điện Biên",
}


def _extract_province_from_text(address: str) -> str:
    """Extract a short province name from raw address text as a last-resort fallback.

    Tries two strategies:
    1. Look for explicit Tỉnh/Thành phố prefix.
    2. Look for a bare known province/city name at the end of the address.
    """
    # Strategy 1: explicit Tỉnh/Thành phố prefix
    m = _PROVINCE_EXTRACT_RE.search(address)
    if m:
        raw = m.group(1).strip().lower()
        raw = re.sub(r"\s*việt\s*nam\s*$", "", raw, flags=re.IGNORECASE).strip()
        return _PROVINCE_SHORT_NAMES.get(raw, raw.title())

    # Strategy 2: bare province name (no prefix)
    m2 = _BARE_PROVINCE_RE.search(address)
    if m2:
        raw = m2.group("name").strip().lower()
        raw = re.sub(r"\s+", " ", raw)
        return _BARE_PROVINCE_MAP.get(raw, raw.title())

    return "Unknown"


def parse_address_components(address: object) -> dict:
    if not isinstance(address, str) or not address.strip():
        return {
            "street": "",
            "ward": "",
            "district": "",
            "province": "",
            "full_address": str(address) if not pd.isna(address) else "",
            "latitude": None,
            "longitude": None
        }
    try:
        address = preprocess_address(address)

        legacy_db = None
        result = None
        street = ""

        # 1. Try parsing with LEGACY mode first
        try:
            result_legacy = vau.parse_address(address, mode=vau.ParseMode.LEGACY)
        except Exception:
            result_legacy = None

        if result_legacy and getattr(result_legacy, "ward_code", None):
            try:
                from vietnamadminunits.database import main as db_main
                res_db = db_main.query(f"SELECT * FROM admin_units_legacy WHERE wardCode='{result_legacy.ward_code}'")
                if res_db:
                    legacy_db = res_db[0]
                    result = result_legacy
                    street = result_legacy.street or ""
            except Exception:
                pass

        # 2. If LEGACY mode failed or ward_code was not in admin_units_legacy, try FROM_2025 mode
        if not legacy_db:
            try:
                result_2025 = vau.parse_address(address, mode=vau.ParseMode.FROM_2025)
            except Exception:
                result_2025 = None

            if result_2025 and getattr(result_2025, "ward_code", None):
                try:
                    from vietnamadminunits.database import main as db_main
                    res_db = db_main.query(f"SELECT * FROM admin_units_legacy WHERE wardCode='{result_2025.ward_code}'")
                    if res_db:
                        legacy_db = res_db[0]
                        result = result_2025
                        street = result_2025.street or ""
                except Exception:
                    pass

        if legacy_db:
            province = legacy_db["provinceShort"] or ""
            district = legacy_db["districtShort"] or ""
            ward = legacy_db["wardShort"] or ""
            latitude = legacy_db["wardLat"] or result.latitude
            longitude = legacy_db["wardLon"] or result.longitude
            
            parts = []
            if street:
                parts.append(street)
            if ward:
                parts.append(ward)
            if district:
                parts.append(district)
            if province:
                parts.append(province)
            parts.append("Vietnam")
            full_address = ", ".join(parts)
        else:
            # Fall back to using the raw result_legacy or result_2025 properties directly
            res = result_legacy or (result_2025 if 'result_2025' in locals() else None)
            if res:
                province = getattr(res, "short_province", None) or ""
                district = getattr(res, "short_district", None) or ""
                ward = getattr(res, "short_ward", None) or ""
                latitude = getattr(res, "latitude", None)
                longitude = getattr(res, "longitude", None)
                street = getattr(res, "street", None) or ""
                
                parts = []
                if street:
                    parts.append(street)
                if ward:
                    parts.append(ward)
                if district:
                    parts.append(district)
                if province:
                    parts.append(province)
                parts.append("Vietnam")
                full_address = ", ".join(parts)
            else:
                province = ""
                district = ""
                ward = ""
                latitude = None
                longitude = None
                full_address = str(address)
                street = str(address)

        if not province:
            province = _extract_province_from_text(address)

        return {
            "street": street,
            "ward": ward,
            "district": district,
            "province": province,
            "full_address": full_address,
            "latitude": latitude,
            "longitude": longitude
        }
    except Exception:
        fallback_prov = _extract_province_from_text(address)
        return {
            "street": str(address),
            "ward": "",
            "district": "",
            "province": fallback_prov,
            "full_address": str(address),
            "latitude": None,
            "longitude": None
        }



def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).upper().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).replace("Đ", "D")


def parse_province_with_alias(text: object) -> tuple[str, str]:
    if pd.isna(text) or not str(text).strip():
        return "Unknown", ""
    try:
        components = parse_address_components(text)
        return components["province"] or "Unknown", str(text)
    except Exception:
        return "Unknown", ""


def parse_province(text: object) -> str:
    province, _ = parse_province_with_alias(text)
    return province


def parse_ward_with_alias(text: object) -> tuple[str, str]:
    if pd.isna(text) or not str(text).strip():
        return "", ""
    try:
        components = parse_address_components(text)
        return components["ward"] or "", str(text)
    except Exception:
        return "", ""


def parse_ward(text: object) -> str:
    ward, _ = parse_ward_with_alias(text)
    return ward


def region_group(province: str) -> str:
    prov = normalize_text(province)
    if prov in {"", "UNKNOWN"}:
        return "Không xác định"

    if prov in {

        "HA GIANG", "CAO BANG", "BAC KAN", "TUYEN QUANG", "LAO CAI",

        "YEN BAI", "THAI NGUYEN", "LANG SON", "BAC GIANG", "PHU THO",

        "DIEN BIEN", "LAI CHAU", "SON LA", "HOA BINH", "QUANG NINH"

    }:

        return "Trung du và miền núi phía Bắc"

    if prov in {

        "HA NOI", "HAI PHONG", "VINH PHUC", "BAC NINH", "HAI DUONG",

        "HUNG YEN", "THAI BINH", "HA NAM", "NAM DINH", "NINH BINH"

    }:

        return "Đồng bằng sông Hồng"

    if prov in {

        "THANH HOA", "NGHE AN", "HA TINH", "QUANG BINH", "QUANG TRI",

        "HUE", "DA NANG", "QUANG NAM", "QUANG NGAI",

        "BINH DINH", "PHU YEN", "KHANH HOA", "NINH THUAN", "BINH THUAN"

    }:

        return "Bắc Trung Bộ và Duyên hải miền Trung"

    if prov in {

        "KON TUM", "GIA LAI", "DAK LAK", "DAK NONG", "LAM DONG"

    }:

        return "Tây Nguyên"

    if prov in {

        "HO CHI MINH", "HO CHI MINH CITY", "TP HCM", "TP. HO CHI MINH",

        "HCMC", "BINH PHUOC", "TAY NINH", "BINH DUONG", "DONG NAI",

        "BA RIA VUNG TAU", "BA RIA - VUNG TAU"

    }:

        return "Đông Nam Bộ"

    if prov in {

        "LONG AN", "TIEN GIANG", "BEN TRE", "TRA VINH", "VINH LONG",

        "DONG THAP", "AN GIANG", "KIEN GIANG", "CAN THO", "HAU GIANG",

        "SOC TRANG", "BAC LIEU", "CA MAU"

    }:

        return "Đồng bằng sông Cửu Long"

    return "Khác"


def haversine_km(origin: tuple[float, float], destination: tuple[float, float]) -> float:
    lat1, lon1 = origin
    lat2, lon2 = destination
    if lat2 is None or lon2 is None or pd.isna(lat2) or pd.isna(lon2):
        return float("nan")
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def add_distance_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "latitude" not in result.columns or "longitude" not in result.columns:
        return result
        
    for warehouse, origin in WAREHOUSE_COORDINATES.items():
        result[f"distance_from_{warehouse.lower().replace(' ', '_')}_km"] = [
            haversine_km(origin, (lat, lon)) for lat, lon in zip(result["latitude"], result["longitude"])
        ]
    return result


from vietnamadminunits.converter.converter_2025 import DICT_PROVINCE

def strip_province_prefix(s: str) -> str:
    if s.startswith('tinh'):
        return s[4:]
    if s.startswith('thanhpho'):
        return s[8:]
    return s

# Build mapping from old clean name to new clean name
_OLD_TO_NEW_MAP = {}
for new_prov, old_provs in DICT_PROVINCE.items():
    new_bare = strip_province_prefix(new_prov)
    # Define standard name for the new province
    std_new = "Hồ Chí Minh" if new_bare == "hochiminh" else (
        "Hà Nội" if new_bare == "hanoi" else (
            "Hải Phòng" if new_bare == "haiphong" else (
                "Đà Nẵng" if new_bare == "danang" else (
                    "Cần Thơ" if new_bare == "cantho" else (
                        "Huế" if new_bare == "hue" else new_bare.title()
                    )
                )
            )
        )
    )
    if new_bare == "angiang": std_new = "An Giang"
    elif new_bare == "bacninh": std_new = "Bắc Ninh"
    elif new_bare == "camau": std_new = "Cà Mau"
    elif new_bare == "caobang": std_new = "Cao Bằng"
    elif new_bare == "daklak": std_new = "Đắk Lắk"
    elif new_bare == "dongnai": std_new = "Đồng Nai"
    elif new_bare == "dongthap": std_new = "Đồng Tháp"
    elif new_bare == "gialai": std_new = "Gia Lai"
    elif new_bare == "hungyen": std_new = "Hưng Yên"
    elif new_bare == "khanhhoa": std_new = "Khánh Hòa"
    elif new_bare == "laichau": std_new = "Lai Châu"
    elif new_bare == "lamdong": std_new = "Lâm Đồng"
    elif new_bare == "langson": std_new = "Lạng Sơn"
    elif new_bare == "laocai": std_new = "Lào Cai"
    elif new_bare == "nghean": std_new = "Nghệ An"
    elif new_bare == "ninhbinh": std_new = "Ninh Bình"
    elif new_bare == "phutho": std_new = "Phú Thọ"
    elif new_bare == "quangngai": std_new = "Quảng Ngãi"
    elif new_bare == "quangninh": std_new = "Quảng Ninh"
    elif new_bare == "quangtri": std_new = "Quảng Trị"
    elif new_bare == "sonla": std_new = "Sơn La"
    elif new_bare == "tayninh": std_new = "Tây Ninh"
    elif new_bare == "thainguyen": std_new = "Thái Nguyên"
    elif new_bare == "thanhhoa": std_new = "Thanh Hóa"
    elif new_bare == "tuyenquang": std_new = "Tuyên Quang"
    elif new_bare == "vinhlong": std_new = "Vĩnh Long"
    elif new_bare == "hatinh": std_new = "Hà Tĩnh"
    elif new_bare == "dienbien": std_new = "Điện Biên"
    
    for old_prov in old_provs:
        old_bare = strip_province_prefix(old_prov)
        _OLD_TO_NEW_MAP[old_bare] = std_new

def to_new_province(province_name: str) -> str:
    if pd.isna(province_name) or not isinstance(province_name, str) or province_name == "Unknown":
        return "Unknown"
    
    import unicodedata
    n = province_name.lower().replace(" ", "").replace("-", "")
    n = "".join(c for c in unicodedata.normalize("NFKD", n) if not unicodedata.combining(c))
    n = n.replace("đ", "d")
    
    if n == "thuathienhue" or n == "hue":
        return "Huế"
        
    if n in _OLD_TO_NEW_MAP:
        return _OLD_TO_NEW_MAP[n]
        
    for k, v in _OLD_TO_NEW_MAP.items():
        if k in n or n in k:
            return v
            
    return province_name.title()


if __name__ == "__main__":
    test_addresses = [
        "Số 129 Trần Hưng Đạo, Phường Long Xuyên, Tỉnh An Giang, Việt Nam",
        "270Bis Ly Thuong Kiet, Ward 14, District 10, Ho Chi Minh City"
    ]
    for addr in test_addresses:
        parsed = parse_address_components(addr)
        print(f"Parsed address components for '{addr}':")
        for k, v in parsed.items():
            print(f"  {k}: {v}")
        print()

