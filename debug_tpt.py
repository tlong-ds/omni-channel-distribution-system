from pathlib import Path

import pandas as pd

ROOT_DIR = Path("/Users/bunnypro/Projects/LOGage2026")
FILE_03 = ROOT_DIR / "[LOGage 2026] File 03_Distributor Network.xlsx"

print("--- Workbook 03: Distributor Network (Raw Data) ---")
df_dist_net = pd.read_excel(FILE_03, sheet_name="Distributor Network", header=1)
df_dist_gen = pd.read_excel(FILE_03, sheet_name="Distributor General", header=1)

print("\nTPT in Distributor Network:")
tpt_net = df_dist_net[
    df_dist_net["Customer Name"].str.contains("TPT", case=False, na=False)
]
print(tpt_net[["Customer Name", "Delivery Address"]].to_string(index=False))

print("\nTPT in Distributor General:")
tpt_gen = df_dist_gen[
    df_dist_gen["Customer Name"].str.contains("TPT", case=False, na=False)
]
print(tpt_gen[["Customer Name", "Delivery Address"]].to_string(index=False))

print("\nLet's also check the cleaned data for TPT:")
dist_cleaned = pd.read_csv("outputs/round2/cleaned/distributors_cleaned.csv")
tpt_cleaned = dist_cleaned[
    dist_cleaned["customer_key"].str.contains("TPT", case=False, na=False)
]
print(
    tpt_cleaned[
        [
            "customer_key",
            "delivery_address",
            "customer_match_status",
            "customer_key_is_ambiguous",
        ]
    ].to_string(index=False)
)
