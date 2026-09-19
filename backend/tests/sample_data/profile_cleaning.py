import pandas as pd
import cProfile
import pstats

from app.cleaning.pipeline import clean_dataframe

csv_path = "../sample_db/data.csv"

df = pd.read_csv(csv_path, encoding="cp1252")

print("Rows:", len(df))
print("Columns:", list(df.columns))

profiler = cProfile.Profile()

profiler.enable()
cleaned = clean_dataframe(df)
profiler.disable()

print("\nCleaning completed.")
print("Cleaned rows:", len(cleaned))

stats = pstats.Stats(profiler)
stats.sort_stats("cumulative")
stats.print_stats(30)