# Cumulative Ratio Analysis - Quick Reference

## ✅ Completed Tasks

### 1. Data Preparation ✓
- **Script**: `prepare_cumulative_donations.py`
- **Input**: 70.6M donation records (US_Election_Donation.csv)
- **Output**: Cumulative aggregations by party, segment, and time period
- **Time**: ~10-15 minutes

### 2. Visualization Generation ✓
- **Script**: `plot_cumulative_donations.py`
- **Output**: 32 high-quality plots (16 normal + 16 log scale)
- **Time**: ~2-3 minutes

### 3. Documentation ✓
- **README.md**: Full technical documentation with interpretation guide
- **Scenario Table**: Clear summary of what each plot shows
- **This File**: Quick reference and status

---

## 📊 Output Summary

### Data Files (output/)
```
├── weekly_cumulative_aggregations.csv     (782 rows, 75 KB)
├── monthly_cumulative_aggregations.csv    (228 rows, 21 KB)
└── cumulative_ratio_summary.csv           (statistics, 2.3 KB)
```

### Plots - Normal Scale (plots_normal/)
16 plots showing 0-1 ratio scale
```
Democratic Ratio:
  ├── Weekly: all, small, medium, large (4 plots)
  └── Monthly: all, small, medium, large (4 plots)

Republican Ratio:
  ├── Weekly: all, small, medium, large (4 plots)
  └── Monthly: all, small, medium, large (4 plots)
```

### Plots - Log Scale (plots_log/)
16 plots with logarithmic y-axis for better visibility
```
Democratic Ratio:
  ├── Weekly: all_dem_log, small_dem_log, medium_dem_log, large_dem_log
  └── Monthly: all_dem_log, small_dem_log, medium_dem_log, large_dem_log

Republican Ratio:
  ├── Weekly: all_rep_log, small_rep_log, medium_rep_log, large_rep_log
  └── Monthly: all_rep_log, small_rep_log, medium_rep_log, large_rep_log
```

---

## 🔑 Key Metrics

### Final Cumulative Ratios (All Donors)
```
Democratic Ratio: 0.7265 (72.65% of total donations)
Republican Ratio: 0.2735 (27.35% of total donations)
```

### Data Coverage
```
Total Donations Processed:  3,795,249
Unique Donors:              47,032
Date Range:                 Jan 2021 - Sep 2025 (57 months, 215 weeks)

By Party:
  Democratic:  $370,997,993 (2,225,591 donations)
  Republican:  $139,679,730 (1,569,658 donations)

By Segment:
  Small:       $58,501,416  (1,011,618 donations)
  Medium:      $106,153,931 (1,082,759 donations)
  Large:       $346,022,376 (1,700,872 donations)
```

---

## 📈 Understanding the Plots

### Ratio Values

| Value | Meaning |
|-------|---------|
| 0.00  | 100% went to Republicans (Dem ratio) or Democrats (Rep ratio) |
| 0.25  | 25% to that party, 75% to the other |
| 0.50  | **EQUAL** - Both parties received equal amounts |
| 0.75  | 75% to that party, 25% to the other |
| 1.00  | 100% went to Democrats (Dem ratio) or Republicans (Rep ratio) |

### Scale Comparison

**Normal Scale** (`plots_normal/`)
- Shows actual proportion clearly
- Good for overall trends
- Ratio stays mostly between 0.2 and 0.9

**Log Scale** (`plots_log/`)
- Magnifies variations around 0.5
- Better for subtle changes
- Good when ratio is clustered around 0.73

---

## 🚀 How to Use

### View Plots
Navigate to:
- `cumulative_ratio_analysis/plots_normal/` for standard 0-1 scale
- `cumulative_ratio_analysis/plots_log/` for logarithmic scale

### Analyze Data
Load CSVs:
```python
import pandas as pd
weekly = pd.read_csv('cumulative_ratio_analysis/output/weekly_cumulative_aggregations.csv')
```

### Regenerate (if needed)
```bash
cd cumulative_ratio_analysis
python3 prepare_cumulative_donations.py    # ~15 min
python3 plot_cumulative_donations.py       # ~3 min
```

---

## 📋 File Locations

### Main Analysis Folder
```
cumulative_ratio_analysis/
├── README.md                              (Full documentation)
├── prepare_cumulative_donations.py        (Data script)
├── plot_cumulative_donations.py           (Plot script)
├── run_cumulative_analysis.py             (Master script)
├── output/                                (Data files)
├── plots_normal/                          (16 normal scale plots)
└── plots_log/                             (16 log scale plots)
```

### Summary Files in Root
```
CUMULATIVE_RATIO_ANALYSIS_SUMMARY.md       (This folder's summary)
```

---

## 🔄 Calculation Method

### What is Cumulative?
Running total from the start of the time period, not just that week/month.

**Example:**
```
Week 1: Dem donations = $100, Rep = $50
        Cumulative: Dem = $100, Rep = $50, Dem Ratio = 0.667

Week 2: Dem donations = $75, Rep = $100
        Cumulative: Dem = $175, Rep = $150, Dem Ratio = 0.538
        (NOT: Dem = 0.43, which would be 75/(75+100))

Week 3: Dem donations = $50, Rep = $50
        Cumulative: Dem = $225, Rep = $200, Dem Ratio = 0.529
```

### Formula
```
Democratic Ratio = Cumulative_Dem / (Cumulative_Dem + Cumulative_Rep)
Republican Ratio = Cumulative_Rep / (Cumulative_Dem + Cumulative_Rep)
```

---

## ✨ Key Features

✓ **0-1 Scale**: Easy to understand proportions  
✓ **Cumulative**: Shows trend over entire time period  
✓ **Dual Views**: Normal and log scales for different insights  
✓ **Donor Segments**: Separate analysis for Small/Medium/Large donors  
✓ **Time Granularity**: Both weekly and monthly views  
✓ **Professional**: 300 DPI, publication-quality plots  
✓ **Reusable**: Modular scripts for future updates  
✓ **Documented**: Comprehensive README with interpretation guide  

---

## 📖 Full Documentation

For detailed information, see:
- **[cumulative_ratio_analysis/README.md](cumulative_ratio_analysis/README.md)** - Complete technical guide
- **[CUMULATIVE_RATIO_ANALYSIS_SUMMARY.md](CUMULATIVE_RATIO_ANALYSIS_SUMMARY.md)** - Implementation summary

---

## Status: ✅ COMPLETE

All 32 plots have been successfully generated and are ready for analysis.

**Last Generated**: February 6, 2026
**Total Processing Time**: ~15-20 minutes
**Quality**: Production-ready (300 DPI PNG)
