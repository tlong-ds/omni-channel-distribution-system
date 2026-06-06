import pandas as pd

df = pd.read_csv("outputs/round2/cleaned/shipments_cleaned.csv")

print(f"Total shipments: {len(df)}")

unknown_province = df[df['province'] == 'Unknown']
print(f"Shipments with Unknown province: {len(unknown_province)} ({(len(unknown_province)/len(df))*100:.2f}%)")

print("\n--- Breakdown of Unknown Provinces by Customer Match Status ---")
print(unknown_province['customer_match_status'].value_counts(dropna=False))

print("\n--- Top 'ship_to_customer' strings that result in Unknown province ---")
print(unknown_province['ship_to_customer'].value_counts(dropna=False).head(20))

print("\n--- Top 'customer_key' strings that result in Unknown province ---")
print(unknown_province['customer_key'].value_counts(dropna=False).head(20))

print("\n--- Summary of customer_segment for Unknown province ---")
print(unknown_province['customer_segment'].value_counts(dropna=False))
