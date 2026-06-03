import pandas as pd

from .config import CUSTOMER_SEGMENT_OVERRIDE_FILE, DISTRIBUTOR_FILE, SKU_MASTER_FILE, TRANSACTION_FILE


def load_sku_master() -> pd.DataFrame:
    return pd.read_excel(SKU_MASTER_FILE, sheet_name="SKU Master Data", header=1)


def load_transactions() -> pd.DataFrame:
    sheets = [
        ("My Phuoc", "My Phuoc Shipment"),
        ("Vinh Loc", "Vinh Loc Shipment"),
    ]
    frames = []
    for warehouse, sheet_name in sheets:
        frame = pd.read_excel(TRANSACTION_FILE, sheet_name=sheet_name, header=1)
        frame["Source Warehouse"] = warehouse
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def load_distributors() -> pd.DataFrame:
    frames = []
    for source, sheet_name in [
        ("pivot", "Distributor Network"),
        ("general", "Distributor General"),
    ]:
        frame = pd.read_excel(DISTRIBUTOR_FILE, sheet_name=sheet_name, header=1)
        frame["Source Sheet"] = source
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def load_segment_overrides() -> pd.DataFrame:
    if CUSTOMER_SEGMENT_OVERRIDE_FILE.exists():
        return pd.read_csv(CUSTOMER_SEGMENT_OVERRIDE_FILE)
    return pd.DataFrame()
