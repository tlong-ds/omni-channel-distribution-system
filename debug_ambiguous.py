import pandas as pd

dist = pd.read_csv("outputs/round2/cleaned/distributors_cleaned.csv")
ambiguous_keys = dist[dist['customer_key_is_ambiguous'] == True]['customer_key'].unique()

print(f"Number of ambiguous customer keys: {len(ambiguous_keys)}")

# Let's see how many of these ambiguous keys have locations strictly in ONE province
multi_prov = 0
single_prov = 0
for key in ambiguous_keys:
    provs = dist[dist['customer_key'] == key]['province'].unique()
    if len(provs) == 1:
        single_prov += 1
    else:
        multi_prov += 1

print(f"Ambiguous keys with single province: {single_prov}")
print(f"Ambiguous keys with multiple provinces: {multi_prov}")

if single_prov > 0:
    print("\nKeys with single province:")
    for key in ambiguous_keys:
        provs = dist[dist['customer_key'] == key]['province'].unique()
        if len(provs) == 1:
            print(f"- {key}: {provs[0]}")
