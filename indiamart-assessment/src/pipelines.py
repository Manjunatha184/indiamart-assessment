import re
import pandas as pd
import numpy as np

RUPEE_RE = re.compile(r"(\d[\d,\.]*)")

def rup_to_float(val):
    """Convert '1,250 / Kg' or '₹ 2,100' → 1250.0 / 2100.0 ; NaN if no digits."""
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    m = RUPEE_RE.search(str(val))
    return float(m.group(1).replace(",", "")) if m else np.nan

def tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned DataFrame ready for EDA."""
    df["price"] = df["price_raw"].apply(rup_to_float)

    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    for col in ("state", "city"):
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string", copy=False)
                .fillna("")
                .str.title()
            )
    return df
