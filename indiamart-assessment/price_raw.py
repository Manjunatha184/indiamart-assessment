import pandas as pd

for cat in ["wheat", "tractor"]:
    df = pd.read_csv(f"data/{cat}.csv")
    print(f"\n== {cat} ==")
    print(df[["product_name", "price_raw"]].head())