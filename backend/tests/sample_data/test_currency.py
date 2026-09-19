import pandas as pd
from app.cleaning.currency_normalizer import normalize_currency_column

s = pd.Series([
    "$1,234.50",
    "500.00",
    "1,000.25",
    "250.75",
    "bad",
    None
])

cleaned, failed = normalize_currency_column(s)

print("CLEANED:")
print(cleaned)

print("\nFAILED:", failed)