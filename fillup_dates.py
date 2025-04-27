import pandas as pd

# 1. Load your data
df = pd.read_csv('prices.csv', parse_dates=['date'])

# 2. Index by date
df = df.set_index('date')

# 3. Build a complete daily date index
full_idx = pd.date_range(start=df.index.min(),
                         end=df.index.max(),
                         freq='D')

# 4. Reindex + forward-fill
df_filled = df.reindex(full_idx).ffill()

# 5. Restore date as a column (if you don’t want it as the index anymore)
df_filled = df_filled.rename_axis('date').reset_index()

# (Optional) Save to CSV
df_filled.to_csv('output_filled.csv', index=False)
