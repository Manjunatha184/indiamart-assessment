# IndiaMART Mini-Assessment 🚀

## 1. Objective
1. **Crawl** two sample categories on IndiaMART – `wheat` and `tractor`.
2. **Store** raw results as CSV (`data/*.csv`).
3. **Run EDA** to generate a quick HTML report with charts.

The code is modular so more categories / pages can be added with one flag.

---

## 2. Tech stack
| Layer            | Choice & why                               |
|------------------|--------------------------------------------|
| Crawling         | **Playwright (headless Chromium)** – renders JS, handles Cloudflare/CAPTCHA easily, fast scroll API. |
| Data cleaning    | **pandas + regex** in `pipelines.py`. |
| Visualisation    | **Matplotlib + Seaborn** – lightweight, no heavy dashboard libs. |

---

## 3. Quick-start

```bash
# 0. create venv
python -m venv .venv && . .venv/bin/activate         # Windows: .venv\Scripts\activate

# 1. install deps & browsers
pip install -r requirements.txt
playwright install chromium

# 2. crawl (3 pages each as demo)
python src/scraper.py --categories wheat tractor --max-pages 3

# 3. run EDA
python src/eda.py
open data/indiamart_report.html     # Mac; use start/wslview on Windows
