import pandas as pd

dist = pd.read_csv("outputs/round2/cleaned/distributors_cleaned.csv")
ambiguous_keys = dist[dist['customer_key_is_ambiguous'] == True]['customer_key'].unique()

print("Keys with multiple provinces:")
for key in ambiguous_keys:
    provs = dist[dist['customer_key'] == key]['province'].unique()
    if len(provs) > 1:
        print(f"- {key}: {list(provs)}")
