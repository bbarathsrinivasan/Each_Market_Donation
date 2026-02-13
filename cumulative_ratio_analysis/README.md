# Cumulative Donation Ratio Analysis

## Overview

This analysis generates cumulative donation ratio visualizations showing the proportion of donations received by each party over time. The ratios are calculated on a **0-1 scale** where:
- **0.0** = 100% Republican donations
- **0.5** = Equal donations from both parties
- **1.0** = 100% Democratic donations

---

## Democratic Cumulative Ratio (Normal Scale)

### Weekly Aggregation
- [plots_normal/cumulative_ratio_weekly_all_dem.png](plots_normal/cumulative_ratio_weekly_all_dem.png)
- [plots_normal/cumulative_ratio_weekly_small_dem.png](plots_normal/cumulative_ratio_weekly_small_dem.png)
- [plots_normal/cumulative_ratio_weekly_medium_dem.png](plots_normal/cumulative_ratio_weekly_medium_dem.png)
- [plots_normal/cumulative_ratio_weekly_large_dem.png](plots_normal/cumulative_ratio_weekly_large_dem.png)

### Monthly Aggregation
- [plots_normal/cumulative_ratio_monthly_all_dem.png](plots_normal/cumulative_ratio_monthly_all_dem.png)
- [plots_normal/cumulative_ratio_monthly_small_dem.png](plots_normal/cumulative_ratio_monthly_small_dem.png)
- [plots_normal/cumulative_ratio_monthly_medium_dem.png](plots_normal/cumulative_ratio_monthly_medium_dem.png)
- [plots_normal/cumulative_ratio_monthly_large_dem.png](plots_normal/cumulative_ratio_monthly_large_dem.png)

---

## Democratic Cumulative Ratio (Log Scale)

### Weekly Aggregation
- [plots_log/cumulative_ratio_weekly_all_dem_log.png](plots_log/cumulative_ratio_weekly_all_dem_log.png)
- [plots_log/cumulative_ratio_weekly_small_dem_log.png](plots_log/cumulative_ratio_weekly_small_dem_log.png)
- [plots_log/cumulative_ratio_weekly_medium_dem_log.png](plots_log/cumulative_ratio_weekly_medium_dem_log.png)
- [plots_log/cumulative_ratio_weekly_large_dem_log.png](plots_log/cumulative_ratio_weekly_large_dem_log.png)

### Monthly Aggregation
- [plots_log/cumulative_ratio_monthly_all_dem_log.png](plots_log/cumulative_ratio_monthly_all_dem_log.png)
- [plots_log/cumulative_ratio_monthly_small_dem_log.png](plots_log/cumulative_ratio_monthly_small_dem_log.png)
- [plots_log/cumulative_ratio_monthly_medium_dem_log.png](plots_log/cumulative_ratio_monthly_medium_dem_log.png)
- [plots_log/cumulative_ratio_monthly_large_dem_log.png](plots_log/cumulative_ratio_monthly_large_dem_log.png)

---

## Republican Cumulative Ratio (Normal Scale)

### Weekly Aggregation
- [plots_normal/cumulative_ratio_weekly_all_rep.png](plots_normal/cumulative_ratio_weekly_all_rep.png)
- [plots_normal/cumulative_ratio_weekly_small_rep.png](plots_normal/cumulative_ratio_weekly_small_rep.png)
- [plots_normal/cumulative_ratio_weekly_medium_rep.png](plots_normal/cumulative_ratio_weekly_medium_rep.png)
- [plots_normal/cumulative_ratio_weekly_large_rep.png](plots_normal/cumulative_ratio_weekly_large_rep.png)

### Monthly Aggregation
- [plots_normal/cumulative_ratio_monthly_all_rep.png](plots_normal/cumulative_ratio_monthly_all_rep.png)
- [plots_normal/cumulative_ratio_monthly_small_rep.png](plots_normal/cumulative_ratio_monthly_small_rep.png)
- [plots_normal/cumulative_ratio_monthly_medium_rep.png](plots_normal/cumulative_ratio_monthly_medium_rep.png)
- [plots_normal/cumulative_ratio_monthly_large_rep.png](plots_normal/cumulative_ratio_monthly_large_rep.png)

---

## Republican Cumulative Ratio (Log Scale)

### Weekly Aggregation
- [plots_log/cumulative_ratio_weekly_all_rep_log.png](plots_log/cumulative_ratio_weekly_all_rep_log.png)
- [plots_log/cumulative_ratio_weekly_small_rep_log.png](plots_log/cumulative_ratio_weekly_small_rep_log.png)
- [plots_log/cumulative_ratio_weekly_medium_rep_log.png](plots_log/cumulative_ratio_weekly_medium_rep_log.png)
- [plots_log/cumulative_ratio_weekly_large_rep_log.png](plots_log/cumulative_ratio_weekly_large_rep_log.png)

### Monthly Aggregation
- [plots_log/cumulative_ratio_monthly_all_rep_log.png](plots_log/cumulative_ratio_monthly_all_rep_log.png)
- [plots_log/cumulative_ratio_monthly_small_rep_log.png](plots_log/cumulative_ratio_monthly_small_rep_log.png)
- [plots_log/cumulative_ratio_monthly_medium_rep_log.png](plots_log/cumulative_ratio_monthly_medium_rep_log.png)
- [plots_log/cumulative_ratio_monthly_large_rep_log.png](plots_log/cumulative_ratio_monthly_large_rep_log.png)

---

## Interpretation Guide

### Understanding the Ratios

**Democratic Ratio: Dem / (Dem + Rep)**
| Value | Meaning |
|-------|---------|
| 0.0 | All donations are to Republicans |
| 0.33 | Democrats received 1/3 of total donations |
| 0.5 | Democrats and Republicans received equal donations |
| 0.67 | Democrats received 2/3 of total donations |
| 1.0 | All donations are to Democrats |

**Republican Ratio: Rep / (Dem + Rep)**
- Same scale as Democratic, just inverted party interpretation
- Rep Ratio = 1 - Dem Ratio

### Normal Scale vs Log Scale

**Normal Scale** (`plots_normal/`)
- Y-axis ranges from 0 to 1
- Good for seeing overall proportion
- Variations near 0.5 (equal donations) appear small

**Log Scale** (`plots_log/`)
- Logarithmic y-axis scaling
- Better for seeing small variations around 0.5
- Highlights deviation from equal donations
- Useful when Democratic ratio stays close to 0.73 (as shown in data)

## Summary Statistics

Final cumulative ratios (All Donors):
- **Democratic Ratio**: 0.7265 (72.65% of total donations)
- **Republican Ratio**: 0.2735 (27.35% of total donations)

Total processed:
- **Donations**: 3.8M records
- **Donors**: 47,032 unique
- **Time span**: Jan 2021 - Sep 2025
- **Democratic donations**: $371M
- **Republican donations**: $140M

## Technical Details

### Cumulative Calculation
For each time period (week or month), the script:
1. Sums all donations in that period by party
2. Adds this sum to all previous periods (running total)
3. Calculates ratio as: Party Total / (Dem Total + Rep Total)

Example:
- Week 1: Dem donations = $100, Rep = $50, Cumulative Dem = $100, Cumulative Rep = $50, Ratio = 0.667
- Week 2: Dem donations = $75, Rep = $100, Cumulative Dem = $175, Cumulative Rep = $150, Ratio = 0.538
- Week 3: Dem donations = $50, Rep = $50, Cumulative Dem = $225, Cumulative Rep = $200, Ratio = 0.529

### Data Segments
- **All Donors**: Combined all donor sizes
- **Small Donors**: Bottom 33.3% by cumulative donation amount
- **Medium Donors**: 33.3rd to 66.6th percentile
- **Large Donors**: Top 33.3%

### Time Periods
- **Weekly**: ISO weeks (Monday-Sunday)
- **Monthly**: Calendar months

## File Structure

```
cumulative_ratio_analysis/
├── prepare_cumulative_donations.py      # Data preparation script
├── plot_cumulative_donations.py         # Plot generation script
├── run_cumulative_analysis.py           # Master orchestration (optional)
├── README.md                            # This file
├── output/
│   ├── weekly_cumulative_aggregations.csv
│   ├── monthly_cumulative_aggregations.csv
│   └── cumulative_ratio_summary.csv
├── plots_normal/                        # Normal scale plots (32)
│   ├── cumulative_ratio_weekly_all_dem.png
│   ├── cumulative_ratio_weekly_all_rep.png
│   ├── cumulative_ratio_weekly_small_dem.png
│   ├── ... (16 total normal scale plots)
│   └── cumulative_ratio_monthly_large_rep.png
└── plots_log/                           # Log scale plots (32)
    ├── cumulative_ratio_weekly_all_dem_log.png
    ├── cumulative_ratio_weekly_all_rep_log.png
    ├── cumulative_ratio_weekly_small_dem_log.png
    ├── ... (16 total log scale plots)
    └── cumulative_ratio_monthly_large_rep_log.png
```

## Troubleshooting

**Issue:** "Aggregation files not found"
- **Solution:** Run `prepare_cumulative_donations.py` first

**Issue:** Out of memory
- **Solution:** Reduce `chunk_size` in prepare script (line 49)

**Issue:** Plots look flat**
- **Solution:** This is expected if all donors show similar ratio trends. Try log scale version which enhances small variations.

## Next Steps

1. Review normal scale plots to understand overall donation trends
2. Check log scale plots for detailed variations
3. Compare across donor segments to see different behaviors
4. Use weekly plots for fine-grained trends, monthly for smoothed patterns
