# Per-Market Donation + Polymarket Time Series Analysis

For each Polymarket **event slug**, this pipeline:

1. Fetches event metadata and price history from Polymarket (Gamma + CLOB APIs).
2. Infers candidate names from the event (markets/outcomes) and matches them to `US_Election_Donation.csv` (Candidate column).
3. Filters donations by those candidates and saves `donations_filtered.csv` in a folder per slug.
4. Saves Polymarket metadata and price series (`polymarket_metadata.json`, `polymarket_prices.csv`).
5. Computes the same **cumulative donation ratio** (Dem/(Dem+Rep)) over time (weekly and monthly) for the filtered donations only (All donors, no segments).
6. Plots donation cumulative ratio and Polymarket price(s) on the **same 0–1 y-axis** for comparison.

## Requirements

- Python 3.x with: `pandas`, `numpy`, `matplotlib`, `seaborn`, `requests`
- `US_Election_Donation.csv` at the repository root (same as for `cumulative_ratio_analysis/`).

## Event slugs config

- **event_slugs.txt**: One Polymarket event slug per line; lines starting with `#` are ignored.
- **event_slugs.json**: JSON array of slug strings.

Example slugs: `presidential-election-winner-2024`. Add or edit slugs in either file; the script reads JSON first, then TXT.

## How to run

From the **repository root**:

```bash
python -m per_market_analysis.run_per_market_analysis
```

This will:

- Create one folder per slug under `per_market_analysis/<slug>/`.
- For each slug: fetch event → infer candidates → filter donations (chunked read of the full donation CSV) → fetch price history → save metadata and prices → compute weekly/monthly cumulative ratios → plot donation ratio + Polymarket prices.

## Folder layout per slug

For each event slug (e.g. `presidential-election-winner-2024`):

```
per_market_analysis/<slug>/
├── donations_filtered.csv          # Donations filtered by inferred candidates (DEM/REP)
├── polymarket_metadata.json       # Full event JSON from Gamma API
├── polymarket_prices.csv          # Price history: timestamp, outcome_label, price
├── output/
│   ├── weekly_cumulative_aggregations.csv
│   └── monthly_cumulative_aggregations.csv
└── plots/
    ├── cumulative_ratio_weekly_with_polymarket.png
    └── cumulative_ratio_monthly_with_polymarket.png
```

## Candidate inference

Candidate names for filtering donations are taken from Polymarket metadata first:

- **groupItemTitle**: Each market's `groupItemTitle` (e.g. "Kari Lake", "Ruben Gallego") is used as the canonical candidate name. Last names are extracted and matched to the donation CSV `Candidate` column (e.g. `"LAKE, KARI"`). Values like "Other" are skipped.
- **Fallback**: If no `groupItemTitle` values are present, names are inferred from the event title, market questions, and outcomes.
- Matching is normalized (lowercase, no punctuation) and done by last name (exact or substring, min length 3).

If no candidates are inferred for an event, donation filtering is skipped (empty `donations_filtered.csv`) but Polymarket metadata and prices are still saved.

## Polymarket APIs

- **Event + metadata**: `GET https://gamma-api.polymarket.com/events/slug/{slug}`
- **Price history**: `GET https://clob.polymarket.com/prices-history?market=<token_id>&interval=max`

Price history is fetched per token (from each market’s `clobTokenIds`); results are labeled by outcome and aggregated into `polymarket_prices.csv`. A short sleep between price-history requests is used to respect rate limits.

## Time alignment

- Donation dates are parsed from `Received` (MMDDYYYY) and aggregated by ISO week and month.
- Polymarket prices use Unix timestamps; they are aggregated to the same weekly/monthly periods (last price per period) so donation ratio and Polymarket series share the same x-axis on the plots.

Donation data typically spans a multi-year range (e.g. 2021–2025). Polymarket price history is requested with `interval=max` so the overlay covers the available history; you can align further by using `startTs`/`endTs` in the client if needed.

## Errors and skipping

- If event fetch fails for a slug, that slug is skipped and the next one runs.
- If no candidates are matched, donations are not filtered (empty filtered file) but metadata and prices are still saved and plots may show only Polymarket lines (or no donation line if no data).
- Failed price-history fetches are logged; other tokens for that slug still run.
