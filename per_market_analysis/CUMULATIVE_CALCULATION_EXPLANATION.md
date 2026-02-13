# Cumulative Donation Ratio Calculation - Explanation

## Overview

The cumulative donation ratio calculation tracks how the proportion of Democratic vs Republican donations changes over time. It uses a **cumulative sum** approach, meaning each period's donations are added to all previous periods' donations.

## How Cumulative Calculation Works

### Step-by-Step Process

#### 1. **Data Filtering and Date Alignment**

- **Start Date**: Donations are filtered to start from the **earliest Polymarket price date** (if Polymarket prices exist)
  - This ensures both donation ratios and Polymarket prices cover the same time period
  - If no Polymarket prices exist, all donation dates are used
- **Date Parsing**: Donation dates are parsed from MMDDYYYY format
- **Party Filtering**: Only DEM and REP donations are included

#### 2. **Period Aggregation**

Donations are grouped into time periods:
- **Daily**: Group by `Year_Date` (YYYY-MM-DD)
- **Weekly**: Group by `Year_Week` (YYYY-W##)
- **Monthly**: Group by `Year_Month` (YYYY-MM)

For each period, donations are summed by party:
```
Daily_Donation_DEM = sum of all DEM donations on that day
Daily_Donation_REP = sum of all REP donations on that day
```

#### 3. **Cumulative Sum Calculation**

The key step: **cumulative sum** (`cumsum()`) adds each period's donations to all previous periods.

**Example (Daily)**:

| Date | DEM (Daily) | REP (Daily) | Cumulative_DEM | Cumulative_REP |
|------|-------------|-------------|-----------------|----------------|
| 2024-04-04 | $100 | $50 | $100 | $50 |
| 2024-04-05 | $200 | $150 | $300 | $200 |
| 2024-04-06 | $50 | $100 | $350 | $300 |
| 2024-04-07 | $0 | $75 | $350 | $375 |

**How it works**:
- Row 1: First day → Cumulative = Daily amounts
- Row 2: Cumulative_DEM = $100 + $200 = $300, Cumulative_REP = $50 + $150 = $200
- Row 3: Cumulative_DEM = $300 + $50 = $350, Cumulative_REP = $200 + $100 = $300
- Row 4: Cumulative_DEM = $350 + $0 = $350, Cumulative_REP = $300 + $75 = $375

**In pandas code**:
```python
daily_pivot["Cumulative_DEM"] = daily_pivot["DEM"].cumsum()
daily_pivot["Cumulative_REP"] = daily_pivot["REP"].cumsum()
```

#### 4. **Ratio Calculation**

For each period, calculate the ratio:
```
Total_Cumulative = Cumulative_DEM + Cumulative_REP
Dem_Ratio = Cumulative_DEM / Total_Cumulative
Rep_Ratio = Cumulative_REP / Total_Cumulative
```

**From the example above**:

| Date | Cumulative_DEM | Cumulative_REP | Total_Cumulative | Dem_Ratio | Rep_Ratio |
|------|----------------|----------------|------------------|------------|-----------|
| 2024-04-04 | $100 | $50 | $150 | 0.667 | 0.333 |
| 2024-04-05 | $300 | $200 | $500 | 0.600 | 0.400 |
| 2024-04-06 | $350 | $300 | $650 | 0.538 | 0.462 |
| 2024-04-07 | $350 | $375 | $725 | 0.483 | 0.517 |

### Why Cumulative?

**Cumulative ratios show the overall trend** of donation patterns:
- **Early periods**: Reflect initial donation patterns
- **Later periods**: Include all donations from the start, showing how the overall balance changes
- **Interpretation**: A Dem_Ratio of 0.6 means "60% of all donations (from start to this date) went to Democrats"

### Key Properties

1. **Monotonicity**: Cumulative amounts always increase (or stay the same)
   - `Cumulative_DEM[t] >= Cumulative_DEM[t-1]`
   - This is because we're adding donations, never subtracting

2. **Ratio Stability**: As more donations accumulate, ratios become more stable
   - Early periods: Small changes in daily donations cause large ratio swings
   - Later periods: Large cumulative totals make ratios less sensitive to daily fluctuations

3. **Time Alignment**: 
   - **Before update**: Started from first donation date
   - **After update**: Starts from earliest Polymarket price date
   - This ensures both donation ratios and Polymarket prices cover the same time window

### Example: Why Start from Polymarket Date?

**Scenario**:
- Polymarket prices start: 2024-04-04
- First donation: 2024-01-15

**Before update**:
- Donation ratios start from 2024-01-15
- Polymarket prices start from 2024-04-04
- **Problem**: Can't compare ratios for Jan-Feb-Mar (no Polymarket data)

**After update**:
- Both start from 2024-04-04
- **Benefit**: Direct comparison possible for all periods

### Code Flow

```python
# 1. Get earliest Polymarket date
earliest_pm_date = get_earliest_polymarket_date(slug_dir)

# 2. Filter donations to start from that date
if earliest_pm_date is not None:
    df = df[df["Date"] >= earliest_pm_date]

# 3. Group by period and sum donations
daily_by_party = df.groupby(["Year_Date", "Party"])["Donation_Amount_USD"].sum()

# 4. Pivot to get DEM and REP columns
daily_pivot = daily_by_party.pivot(...)

# 5. Calculate cumulative sums
daily_pivot["Cumulative_DEM"] = daily_pivot["DEM"].cumsum()
daily_pivot["Cumulative_REP"] = daily_pivot["REP"].cumsum()

# 6. Calculate ratios
daily_pivot["Dem_Ratio"] = Cumulative_DEM / (Cumulative_DEM + Cumulative_REP)
```

### Visual Interpretation

When plotted, cumulative ratios show:
- **Upward trend**: Increasing Dem_Ratio means recent donations favor Democrats
- **Downward trend**: Decreasing Dem_Ratio means recent donations favor Republicans
- **Stable ratio**: Donations are balanced between parties
- **Convergence**: Ratio approaches a stable value as more data accumulates

### Comparison with Non-Cumulative

**Non-cumulative (period-by-period)**:
- Shows donation patterns for each period independently
- Example: "This week, 70% went to Democrats"
- Doesn't show overall trend

**Cumulative (our approach)**:
- Shows overall donation balance from start to each period
- Example: "From start to this week, 60% went to Democrats"
- Shows trend over time

## Summary

The cumulative calculation:
1. **Filters** donations to start from earliest Polymarket price date
2. **Groups** donations by time period (daily/weekly/monthly)
3. **Sums** donations per period by party
4. **Accumulates** using `cumsum()` to get running totals
5. **Calculates** ratios: `Dem_Ratio = Cumulative_DEM / Total_Cumulative`

This provides a time series showing how the overall donation balance changes over time, aligned with Polymarket price data for direct comparison.
