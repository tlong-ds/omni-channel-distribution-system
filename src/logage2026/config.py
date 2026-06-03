from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

SKU_MASTER_FILE = ROOT_DIR / "[LOGage2026] File 01_SKU Master Data.xlsx"
TRANSACTION_FILE = ROOT_DIR / "[LOGage2026] File 02_Transaction Log (My Phuoc & Vinh Loc Warehouses).xlsx"
DISTRIBUTOR_FILE = ROOT_DIR / "[LOGage 2026] File 03_Distributor Network.xlsx"

OUTPUT_DIR = ROOT_DIR / "outputs" / "round2"
CLEANED_DIR = OUTPUT_DIR / "cleaned"
TABLES_DIR = OUTPUT_DIR / "tables"
CHARTS_DIR = OUTPUT_DIR / "charts"
NOTES_DIR = OUTPUT_DIR / "notes"

CUSTOMER_SEGMENT_OVERRIDE_FILE = ROOT_DIR / "customer_segment_overrides.csv"

ABC_A_THRESHOLD = 0.80
ABC_B_THRESHOLD = 0.95
FAST_MOVING_ABC_QUANTITY = "A"
FAST_MOVING_ABC_FREQUENCY = "A"

XYZ_CV_X_MAX = 0.50
XYZ_CV_Y_MAX = 1.00
XYZ_MIN_NONZERO_WEEKS = 4
WINSORIZE_LIMITS = None

WAREHOUSE_COORDINATES = {
    "My Phuoc": (11.152, 106.615),
    "Vinh Loc": (10.785, 106.565),
}

