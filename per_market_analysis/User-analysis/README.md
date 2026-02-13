# User Analysis: Investment-Weighted Odds Calculation

## Overview

This module calculates investment-weighted odds from blockchain trades data by analyzing user positions, aggregating by user segments, and comparing with Polymarket closing prices. The analysis provides insights into how different user segments (Small, Medium, Large) predict market outcomes compared to market prices.

## Methodology

### 1. Data Normalization and Day Offset Calculation

**Input**: Trades CSV files (`<market_id>_trades.csv`) containing:
- `timestamp`: Trade timestamp (ISO8601 format)
- `maker`, `taker`: User addresses (Ethereum addresses)
- `nonusdc_side`: Token type (`token1` = YES, `token2` = NO)
- `maker_direction`, `taker_direction`: Trade direction (BUY/SELL)
- `token_amount`: Quantity of tokens traded
- `usd_amount`: USD value of the trade

**Process**:
1. Parse timestamps to datetime and extract dates
2. Extract user_id from both `maker` and `taker` (each trade involves two users)
3. Map tokens: `token1` → YES, `token2` → NO
4. Determine closing date: `max(date)` for the market
5. Compute `day_offset = (date - closing_date).days` (closing day = 0, earlier days negative)

**Output**: Normalized DataFrame with columns:
- `user_id`, `side` (BUY/SELL), `quantity`, `unix_timestamp`, `date`, `token_type` (YES/NO), `day_offset`

### 2. Daily Token Series Construction

**Process**:
1. Group trades by `(user_id, token_type, day_offset)`
2. Sum BUY transactions → `daily_buy`
3. Sum SELL transactions → `daily_sell`
4. Compute `net_tokens = daily_buy - daily_sell`
5. Track `end_of_day_timestamp` (max unix_timestamp per bucket)

**Output**: DataFrame with columns:
- `user_id`, `token_type`, `day_offset`, `daily_buy`, `daily_sell`, `net_tokens`, `end_of_day_timestamp`

### 3. Cumulative Position Accumulation

**Process**:
1. Sort by `(user_id, token_type, day_offset)` in ascending order
2. For each `(user_id, token_type)` group:
   - Compute cumulative sum of `net_tokens` → `yes_cumulative_position` (if token_type=YES)
   - Compute cumulative sum of `net_tokens` → `no_cumulative_position` (if token_type=NO)
3. Forward-fill positions to handle days where users didn't trade

**Output**: DataFrame with columns:
- `user_id`, `day_offset`, `yes_cumulative_position`, `no_cumulative_position`

### 4. Individual Position Calculation

**Formulas**:

Let `Hy = yes_cumulative_position` and `Hn = no_cumulative_position` for each user/day.

**Individual YES exposure**:
```
individual_yes_position = (Hy > 0) * Hy + (Hn < 0) * (-Hn)
```

**Individual NO exposure**:
```
individual_no_position = (Hn > 0) * Hn + (Hy < 0) * (-Hy)
```

**Interpretation**:
- If a user has positive YES position (`Hy > 0`), their YES exposure equals that position
- If a user has negative NO position (`Hn < 0`), this represents a YES exposure (short NO = long YES)
- Same logic applies for NO exposure

**Output**: DataFrame with columns:
- `user_id`, `day_offset`, `individual_yes_position`, `individual_no_position`, `yes_cumulative_position`, `no_cumulative_position`

### 5. User Segmentation

**Method**: Segments are computed from total USD trading volume per user.

**Thresholds**:
- **Large**: `cumulative_total_value_max >= 1,000,000`
- **Medium**: `10,000 <= cumulative_total_value_max < 1,000,000`
- **Small**: `cumulative_total_value_max < 10,000`

**Data Sources**:
1. If `all_users_analysis.csv` exists (with columns `user_id`, `cumulative_total_value_max`), use it
2. Otherwise, compute from trades data by summing `usd_amount` per user across all trades

**Output**: Dictionary mapping `user_id` → `"small"`/`"medium"`/`"large"`

### 6. Aggregation by Segment and Day Offset

**Process**:
1. Map each user to their segment (or "all_users" if not segmented)
2. For each `(day_offset, segment)` combination:
   - Filter users where `yes_cumulative_position != 0` → sum `individual_yes_position` → `agg_yes`
   - Filter users where `no_cumulative_position != 0` → sum `individual_no_position` → `agg_no`
   - Compute **investment-weighted odds**: `odds = agg_yes / (agg_yes + agg_no)`

**Segments Computed**:
- `all_users`: Aggregate across all users
- `small`: Small segment only
- `medium`: Medium segment only
- `large`: Large segment only

**Output**: DataFrame with columns:
- `day_offset`, `segment`, `agg_yes`, `agg_no`, `odds`

### 7. Price-Based Market Odds

**Input**: `polymarket_prices.csv` with columns:
- `timestamp`: Unix timestamp
- `outcome_label`: Outcome label (e.g., "Democrat")
- `price`: Price (0-1 scale)

**Process**:
1. Filter for YES token outcomes (based on `outcome_label`)
2. Parse timestamps to dates
3. Compute `day_offset = (date - closing_date).days`
4. Drop rows where `day_offset > 0` (only historical prices)
5. Get last price per day (end-of-day price)

**Output**: DataFrame with columns:
- `day_offset`, `price_odds`

### 8. Visualization

**Charts Generated** (5 per market):

1. **All Segments Comparison** (`{market_id}_odds_comparison_all_segments.png`)
   - Price Odds (blue)
   - All Users (green)
   - Small Segment (orange)
   - Medium Segment (red)
   - Large Segment (purple)

2. **Price Odds vs All Users** (`{market_id}_odds_comparison_all_users.png`)
   - Two-line comparison

3. **Price Odds vs Large Segment** (`{market_id}_odds_comparison_large.png`)
   - Two-line comparison

4. **Price Odds vs Medium Segment** (`{market_id}_odds_comparison_medium.png`)
   - Two-line comparison

5. **Price Odds vs Small Segment** (`{market_id}_odds_comparison_small.png`)
   - Two-line comparison

**Chart Features**:
- X-axis: Day Offset (0 = closing day, negative = days before closing)
- Y-axis: Odds (0-1 scale)
- Grid lines for readability
- Legend with segment labels
- High-resolution output (300 DPI)

## File Structure

```
per_market_analysis/
├── User-analysis/
│   ├── calculate_trades_odds.py  (main script)
│   └── README.md                (this file)
├── Trades/
│   └── <event_id>/
│       └── <market_id>_trades.csv
└── trades_Plot/
    └── <event_id>/
        ├── <market_id>_all_segments.csv
        ├── <market_id>_small_segment.csv
        ├── <market_id>_medium_segment.csv
        ├── <market_id>_large_segment.csv
        ├── <market_id>_odds_comparison_all_segments.png
        ├── <market_id>_odds_comparison_all_users.png
        ├── <market_id>_odds_comparison_large.png
        ├── <market_id>_odds_comparison_medium.png
        └── <market_id>_odds_comparison_small.png
```

## Usage

### Prerequisites

- Python 3.7+
- Required packages:
  - `pandas`
  - `matplotlib`
  - `seaborn`

### Running the Analysis

From the repository root:

```bash
python per_market_analysis/User-analysis/calculate_trades_odds.py
```

Or from the `per_market_analysis/User-analysis/` directory:

```bash
python calculate_trades_odds.py
```

### Input Files

1. **Trades Data**: `per_market_analysis/Trades/<event_id>/<market_id>_trades.csv`
   - Required columns: `timestamp`, `maker`, `taker`, `nonusdc_side`, `maker_direction`, `taker_direction`, `token_amount`, `usd_amount`

2. **Price Data** (optional): `per_market_analysis/<event_id>/polymarket_prices.csv`
   - Required columns: `timestamp`, `outcome_label`, `price`
   - If missing, price comparison line will be skipped in plots

3. **User Segments** (optional): `all_users_analysis.csv` in repo root or `per_market_analysis/`
   - Required columns: `user_id`, `cumulative_total_value_max`
   - If missing, segments will be computed from trades data

### Output Files

For each market, the script generates:

**CSV Files**:
- `{market_id}_all_segments.csv`: Aggregated odds for all users
- `{market_id}_small_segment.csv`: Aggregated odds for small segment
- `{market_id}_medium_segment.csv`: Aggregated odds for medium segment
- `{market_id}_large_segment.csv`: Aggregated odds for large segment

Each CSV contains columns:
- `day_offset`: Days from closing (0 = closing day)
- `segment`: Segment name
- `agg_yes`: Aggregated YES exposure
- `agg_no`: Aggregated NO exposure
- `odds`: Investment-weighted odds (agg_yes / (agg_yes + agg_no))

**PNG Files**:
- 5 visualization charts as described above

## Key Concepts

### Investment-Weighted Odds

Unlike simple vote-counting, investment-weighted odds weight each user's prediction by their position size. A user with a large position has more influence on the aggregated odds than a user with a small position.

**Formula**:
```
odds = Σ(individual_yes_position) / (Σ(individual_yes_position) + Σ(individual_no_position))
```

Where the sums are over users with non-zero positions in the respective token.

### Day Offset

Day offset measures time relative to market closing:
- **0**: Closing day
- **Negative values**: Days before closing (e.g., -10 = 10 days before closing)
- **Positive values**: After closing (filtered out, only historical prices used)

### Cumulative Positions

Cumulative positions track a user's net token holdings over time:
- **Positive YES position**: User holds YES tokens (betting on YES outcome)
- **Negative YES position**: User is short YES (betting against YES)
- Same logic applies for NO positions

### Individual Exposures

Individual exposures convert cumulative positions into directional bets:
- A positive YES position contributes to YES exposure
- A negative NO position (short NO) also contributes to YES exposure (since short NO = long YES)
- This captures all ways users can express a YES or NO prediction

## Interpretation

### Comparing Segments

- **All Users**: Overall market sentiment from all traders
- **Large Segment**: Sentiment from high-volume traders (may indicate informed trading)
- **Medium Segment**: Sentiment from moderate-volume traders
- **Small Segment**: Sentiment from low-volume traders (may indicate retail sentiment)

### Price Odds vs Segment Odds

- **Price Odds**: Market-clearing prices from Polymarket (aggregate of all traders)
- **Segment Odds**: Investment-weighted predictions from specific user segments

Differences between price odds and segment odds may indicate:
- Information asymmetry
- Different risk preferences
- Market inefficiencies
- Segment-specific biases

## Notes

- The script processes all markets in all event folders automatically
- Empty trades files are skipped with a warning
- Missing price files result in plots without price comparison line
- Segment computation from trades uses total USD volume across all trades per user
- All timestamps are converted to dates for day_offset calculation (time-of-day ignored)

## Troubleshooting

**Issue**: Only "all_users" segment appears in outputs
- **Solution**: Ensure `all_users_analysis.csv` exists or segments will be computed from trades data. Check that trades data includes `usd_amount` column.

**Issue**: Segfault or memory errors
- **Solution**: Large CSV files may require more memory. Consider processing markets individually or increasing system memory.

**Issue**: Empty plots
- **Solution**: Check that trades data exists and contains valid timestamps. Verify that `polymarket_prices.csv` exists if price comparison is needed.

**Issue**: Incorrect day_offset values
- **Solution**: Verify that timestamps in trades CSV are in ISO8601 format and that closing date is correctly identified as max(date).
