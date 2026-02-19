# Summary Analysis

Summary analysis produces **one combined graph per frequency** (daily, weekly, monthly) for each event. Each graph plots **four lines** on a single 0–1 axis so you can compare donation-based and prediction-market-based signals over time.

---

## The Four Lines

### 1. Donation cumulative (All)

**What it is:** The share of total donations (so far) that went to Democrats, using only donations up to that period.

**How it is calculated:**

- **Data source:** `{slug}/output/{freq}_cumulative_aggregations.csv` (Segment = All).
- Donations are filtered to DEM/REP and to the Polymarket date range (earliest price date through closing date).
- For each period (day, week, or month):
  - Sum DEM donations and REP donations **from the start through that period** (cumulative).
  - **Dem_Ratio** = Cumulative_DEM / (Cumulative_DEM + Cumulative_REP).
- So each point is: “Of all donations made from the start through this period, what fraction went to Democrats?”

**Used in:** Main donation pipeline (`prepare_cumulative_per_slug.py` for All; `donation_analysis/prepare_cumulative_segments.py` for segments). Summary uses the **All** segment only.

---

### 2. Prediction cumulative (all users)

**What it is:** An investment-weighted “odds” from Polymarket **trades** (blockchain): the share of total YES exposure that is in the YES (win) outcome, aggregated over all users and carried forward over time.

**How it is calculated:**

- **Data source:** `trades_Plot/{slug}/{market_id}_all_users_segment.csv` (from User-analysis `calculate_trades_odds.py`).
- For each user and each day (by `day_offset` relative to market close):
  - Net tokens (buys − sells) per user per outcome (YES/NO) are summed by day.
  - **Cumulative position** = running sum of net tokens over time (carried forward on no-trade days).
  - **Individual exposure** to YES and NO is derived from these cumulative positions (long YES + short NO, etc.).
- For each day, across **all users**:
  - **agg_yes** = sum of individual YES exposure (users with non-zero YES position).
  - **agg_no** = sum of individual NO exposure.
  - **odds** = agg_yes / (agg_yes + agg_no).
- So each point is: “Given all positions built up through this day, what fraction of total exposure is on YES?”
- For **weekly** and **monthly** summary graphs, these daily odds are aggregated to the same period as donations: each period is assigned the **last** day’s odds in that period (end-of-period prediction). Days are mapped to calendar dates using the market’s closing date, then to Year_Date / Year_Week / Year_Month.

**Used in:** User-analysis (`User-analysis/calculate_trades_odds.py`). Summary uses the **all_users** segment and the first available market’s `*_all_users_segment.csv` per slug.

---

### 3. Donation non-cumulative (All)

**What it is:** The share of donations that went to Democrats **in that period only** (no carry-forward).

**How it is calculated:**

- **Data source:** `{slug}/non_cumulative_donations/output/{freq}_non_cumulative_aggregations.csv` (Segment = All).
- Same donation filter as cumulative (DEM/REP, Polymarket date range).
- For each period (day, week, or month):
  - Sum DEM and REP donations **in that period only** (no cumsum).
  - **Dem_Ratio** = Period_DEM / (Period_DEM + Period_REP).
- So each point is: “Of donations made in this period only, what fraction went to Democrats?”

**Used in:** Non-cumulative donation pipeline (`non_cumulative_donations/prepare_non_cumulative_segments.py`). Summary uses the **All** segment only.

---

### 4. Prediction non-cumulative (Polymarket, Democrat)

**What it is:** The Polymarket **price** (0–1) for the **Democrat** outcome in that period—i.e. the market’s implied probability for Democrat in that period only (no cumulation).

**How it is calculated:**

- **Data source:** `{slug}/polymarket_prices.csv` (timestamp, outcome_label, price).
- Prices are aggregated to the same period as donations (Year_Date, Year_Week, or Year_Month) by taking the **last** price in each period (same logic as `plot_donation_and_polymarket.aggregate_prices_to_period`).
- The **Democrat** outcome is chosen so the line is comparable to donation Dem_Ratio:
  - Prefer a column named **"Democrat"** (case-insensitive).
  - Else prefer a column whose label contains the **Democrat candidate’s last name** from `event_slugs.json` (e.g. “Ruben Gallego” for Arizona).
  - Else prefer a column containing **"Democratic"**, then fallback to the first non-“No” column.
- So each point is: “What was the Polymarket price (probability) for the Democrat outcome at the end of this period?”

**Used in:** Summary only; reuses the same price aggregation as other donation+Polymarket plots, but always selects the Democrat outcome for consistency with donation ratios.

---

## How the Four Lines Are Combined

- **X-axis:** The **donation cumulative** series defines the time axis. Its period list (e.g. list of Year_Date, Year_Week, or Year_Month from `output/{freq}_cumulative_aggregations.csv`, Segment = All) is the canonical list of periods.
- **Alignment:** The other three series are **reindexed** to this same period list:
  - **Donation non-cumulative:** Reindexed to donation cumulative periods; missing periods become NaN (gaps in the line).
  - **Prediction cumulative:** Reindexed to donation cumulative periods; missing periods are **forward-filled** so the line continues until the next observed value.
  - **Prediction non-cumulative:** Reindexed to donation cumulative periods; missing periods become NaN.
- **Y-axis:** All four series are on the same 0–1 scale (ratio or probability).
- **Output:** One figure per frequency per event: `output/{slug}/summary_daily.png`, `summary_weekly.png`, `summary_monthly.png`.

---

## Data Flow (Summary)

```
Donation cumulative     → output/{freq}_cumulative_aggregations.csv (All)
Donation non-cumulative → non_cumulative_donations/output/{freq}_non_cumulative_aggregations.csv (All)
Prediction cumulative   → trades_Plot/{slug}/{market_id}_all_users_segment.csv (day_offset → period via closing_date)
Prediction non-cumulative → polymarket_prices.csv → aggregate by period → Democrat outcome column
                              ↓
                    Common x-axis = donation cumulative periods
                    Reindex other three; plot 4 lines on one graph
```

---

## Prerequisites

- **Donation cumulative and non-cumulative:** Run the main per-market pipeline (`run_per_market_analysis.py`) so that `output/` and `non_cumulative_donations/output/` exist for each slug.
- **Prediction cumulative:** Run User-analysis (`User-analysis/calculate_trades_odds.py`) so that `trades_Plot/{slug}/{market_id}_all_users_segment.csv` exists for at least one market per slug.
- **Prediction non-cumulative:** `polymarket_prices.csv` in each slug directory (also produced by the main pipeline).
- **Event list:** Slugs are read from `event_slugs.json` (or `event_slugs.txt`) in `per_market_analysis/`.

---

## How to Run

From the repository root:

```bash
python -m per_market_analysis.Summary_analysis.run_summary_analysis
```

Or from `per_market_analysis/Summary_analysis/` (with repo root on `PYTHONPATH`):

```bash
python run_summary_analysis.py
```

Outputs are written to:

`per_market_analysis/Summary_analysis/output/{slug}/summary_daily.png`, `summary_weekly.png`, `summary_monthly.png`.

---

## Summary of Formulas

| Line                      | Formula (conceptually) |
|---------------------------|-------------------------|
| Donation cumulative       | Cumulative_DEM / (Cumulative_DEM + Cumulative_REP) over time |
| Prediction cumulative     | agg_yes / (agg_yes + agg_no) from cumulative trade positions (all users) |
| Donation non-cumulative   | Period_DEM / (Period_DEM + Period_REP) per period |
| Prediction non-cumulative| Last Polymarket price for Democrat outcome in each period |

All four are plotted on the same period index (from donation cumulative) and the same 0–1 y-axis.

---

## Weekly summary CSVs

Two CSV files are built from the same data used for the summary graphs (weekly frequency only). They give one row per **(election name, week)** for use in regressions or other analysis.

### 1. `output/summary_odds_weekly.csv`

| Column | Description |
|--------|-------------|
| **election_name** | Event slug (e.g. `arizona-us-senate-election-winner`). Part of primary key. |
| **week** | Period label (e.g. `2024-W14`). Part of primary key. |
| **winning_side_dem** | 1 = Democrat won, 0 = Republican won. Inferred from Polymarket resolution (first “Will a Democrat win?” market `outcomePrices`). Empty if not resolved or not found. |
| **cumulative_prediction_odds** | Prediction cumulative (all users) for that week — same source as the red line in summary_weekly. Can be updated separately when better trade data is available (see below). |
| **non_cumulative_prediction_odds** | Polymarket price for Democrat outcome at end of that week (last price in week). |
| **cumulative_donation_odds** | Donation cumulative Dem_Ratio (All) for that week. |
| **non_cumulative_donation_odds** | Donation non-cumulative Dem_Ratio (All) for that week. |

All “odds” columns are on a 0–1 scale (Dem share or probability).

### 2. `output/summary_segment_odds_weekly.csv`

Same primary key **(election_name, week)**. Additional columns are donation odds by donor segment (Small / Medium / Large, based on cumulative donation amount percentiles):

- **cumulative_donation_odds_small**, **cumulative_donation_odds_medium**, **cumulative_donation_odds_large**
- **non_cumulative_donation_odds_small**, **non_cumulative_donation_odds_medium**, **non_cumulative_donation_odds_large**

Data come from `output/weekly_cumulative_aggregations.csv` and `non_cumulative_donations/output/weekly_non_cumulative_aggregations.csv` (Segment = Small/Medium/Large).

### How the CSVs are created

1. **Prerequisites:** Same as for summary graphs (donation cumulative and non-cumulative outputs, optional trades_Plot data, Polymarket prices, event slugs in `event_slugs.json` or `event_slugs.txt`).

2. **Build both CSVs** (from repo root):

   ```bash
   python -m per_market_analysis.Summary_analysis.build_summary_csvs
   ```

   This writes `Summary_analysis/output/summary_odds_weekly.csv` and `Summary_analysis/output/summary_segment_odds_weekly.csv`. Slugs are read from `per_market_analysis/event_slugs.json` (or `event_slugs.txt`). Any slug with missing data is skipped for that file (e.g. no donation cumulative → no row for that election).

### Updating cumulative prediction odds

When better or updated **trade data** is available (e.g. new or corrected `trades_Plot/{slug}/*_all_users_segment.csv` from User-analysis), you can refresh only the **cumulative_prediction_odds** column in `summary_odds_weekly.csv` without regenerating donation or Polymarket columns:

```bash
python -m per_market_analysis.Summary_analysis.update_cumulative_prediction_odds
```

- Reads `Summary_analysis/output/summary_odds_weekly.csv`.
- Recomputes cumulative prediction odds per (election_name, week) from the current `trades_Plot` data (same logic as the summary plots).
- Overwrites `summary_odds_weekly.csv` with the same rows and columns, only **cumulative_prediction_odds** updated.

Run this after (re)running User-analysis so that `trades_Plot` contains the new trade data. Other columns (donation odds, non-cumulative prediction odds, winning_side_dem) are unchanged.
