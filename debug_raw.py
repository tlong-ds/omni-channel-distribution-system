import pandas as pd
from pathlib import Path

ROOT_DIR = Path("/Users/bunnypro/Projects/LOGage2026")
FILE_02 = ROOT_DIR / "[LOGage2026] File 02_Transaction Log (My Phuoc & Vinh Loc Warehouses).xlsx"
FILE_03 = ROOT_DIR / "[LOGage 2026] File 03_Distributor Network.xlsx"

print("--- Workbook 03: Distributor Network (Raw Data) ---")
df_dist_net = pd.read_excel(FILE_03, sheet_name="Distributor Network", header=1)
df_dist_gen = pd.read_excel(FILE_03, sheet_name="Distributor General", header=1)

# Check MediaMart
print("\nMediaMart in Distributor Network:")
mediamart_net = df_dist_net[df_dist_net['Customer Name'].str.contains("MEDIAMART", case=False, na=False)]
print(mediamart_net[['Customer Name', 'Delivery Address']].head(5).to_string(index=False))
print(f"... and {len(mediamart_net) - 5} more branches" if len(mediamart_net) > 5 else "")

print("\nMediaMart in Distributor General:")
mediamart_gen = df_dist_gen[df_dist_gen['Customer Name'].str.contains("MEDIAMART", case=False, na=False)]
print(mediamart_gen[['Customer Name', 'Delivery Address']].head(5).to_string(index=False))

print("\n--- Workbook 02: Transaction Log (Raw Data) ---")
df_tx_mp = pd.read_excel(FILE_02, sheet_name="My Phuoc Shipment", header=1)
df_tx_vl = pd.read_excel(FILE_02, sheet_name="Vinh Loc Shipment", header=1)

df_tx = pd.concat([df_tx_mp, df_tx_vl])

print("\nTransactions for MediaMart:")
mediamart_tx = df_tx[df_tx['Ship-to Customer'].str.contains("MEDIAMART", case=False, na=False)]
print(mediamart_tx[['Ship-to Customer', 'Document No.', 'Quantity']].head(5).to_string(index=False))
print(f"... and {len(mediamart_tx) - 5} more transactions" if len(mediamart_tx) > 5 else "")

# Are there any other columns in Workbook 02 that we are missing?
print("\nAll columns in Workbook 02 (My Phuoc Shipment):")
print(list(df_tx_mp.columns))
