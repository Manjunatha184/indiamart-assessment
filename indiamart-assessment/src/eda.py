from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pipelines import tidy

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
csv_files = list(DATA_DIR.glob("*.csv"))

if not csv_files:
    raise SystemExit("❌  No CSV files found in data/. Run the scraper first.")

# ── load & clean ────────────────────────────────────────────────
df = pd.concat([tidy(pd.read_csv(f)) for f in csv_files], ignore_index=True)

report = [
    "<h1>IndiaMART quick-look EDA</h1>",
    f"<p><b>Total rows (raw):</b> {len(df):,}</p>",
]


# ── TOP STATES BAR ──────────────────────────────────────────────
if "state" in df.columns and not df["state"].dropna().empty:
    top_states = (df["state"]
                    .value_counts()
                    .head(10)
                    .sort_values())
    if not top_states.empty:
        top_states.plot(kind="barh")
        plt.title("Top supplier states (count)")
        states_png = DATA_DIR / "top_states.png"
        plt.savefig(states_png, bbox_inches="tight")
        plt.clf()
        report.append(f'<img src="{states_png.name}" width="600">')

# ── WRITE REPORT ────────────────────────────────────────────────
(DATA_DIR / "indiamart_report.html").write_text("\n".join(report), encoding="utf-8")
print("✅  EDA finished → open data/indiamart_report.html")
