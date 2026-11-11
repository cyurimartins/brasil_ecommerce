import pandas as pd

df_orders = pd.read_csv("olist_orders_dataset.csv")
df_orders.to_csv("data/ods/orders.csv", index=False)