#!/usr/bin/env python3
"""
Compute cumulative donation ratios per segment (Small, Medium, Large) and append
to existing output aggregations (which contain All segment from prepare_cumulative_per_slug).
"""

from pathlib import Path

import numpy as np
import pandas as pd

# Reuse date parsing and Polymarket date range from main prepare script
import sys
SCRIPT_DIR = Path(__file__).resolve().parent
PARENT = SCRIPT_DIR.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
from prepare_cumulative_per_slug import get_polymarket_date_range, parse_date


def _compute_segment_aggregations(
    df: pd.DataFrame,
    freq: str,
    time_col: str,
) -> pd.DataFrame:
    """Compute cumulative DEM/REP and ratios for one segment DataFrame."""
    if freq == "daily":
        by_party = df.groupby(["Year_Date", "Party"])["Donation_Amount_USD"].sum().reset_index()
        by_party.columns = ["Year_Date", "Party", "_amt"]
        pivot = by_party.pivot(index="Year_Date", columns="Party", values="_amt").fillna(0)
        pivot = pivot.sort_index()
    elif freq == "weekly":
        by_party = df.groupby(["Year_Week", "Party"])["Donation_Amount_USD"].sum().reset_index()
        by_party.columns = ["Year_Week", "Party", "_amt"]
        pivot = by_party.pivot(index="Year_Week", columns="Party", values="_amt").fillna(0)
    else:
        by_party = df.groupby(["Year_Month", "Party"])["Donation_Amount_USD"].sum().reset_index()
        by_party.columns = ["Year_Month", "Party", "_amt"]
        pivot = by_party.pivot(index="Year_Month", columns="Party", values="_amt").fillna(0)

    if "DEM" not in pivot.columns:
        pivot["DEM"] = 0
    if "REP" not in pivot.columns:
        pivot["REP"] = 0
    pivot["Cumulative_DEM"] = pivot["DEM"].cumsum()
    pivot["Cumulative_REP"] = pivot["REP"].cumsum()
    pivot["Total_Cumulative"] = pivot["Cumulative_DEM"] + pivot["Cumulative_REP"]
    pivot["Dem_Ratio"] = pivot.apply(
        lambda r: (r["Cumulative_DEM"] / r["Total_Cumulative"]) if r["Total_Cumulative"] > 0 else np.nan,
        axis=1,
    )
    pivot["Rep_Ratio"] = pivot.apply(
        lambda r: (r["Cumulative_REP"] / r["Total_Cumulative"]) if r["Total_Cumulative"] > 0 else np.nan,
        axis=1,
    )
    return pivot.reset_index()


def prepare_cumulative_segments_for_slug(slug_dir: Path) -> bool:
    """
    Load donations_filtered.csv and donor_segments.csv, filter to Polymarket date range,
    compute cumulative ratios for Small, Medium, Large segments, and append to
    existing output/*_cumulative_aggregations.csv (which already have All).
    Returns True if successful.
    """
    donations_path = slug_dir / "donations_filtered.csv"
    segments_path = slug_dir / "donor_segments.csv"
    output_dir = slug_dir / "output"

    if not donations_path.exists():
        print(f"  ✗ Not found: {donations_path}")
        return False
    if not segments_path.exists():
        print(f"  ✗ Not found: {segments_path} (run segment_donors first)")
        return False

    df = pd.read_csv(donations_path, low_memory=False)
    segments_df = pd.read_csv(segments_path)
    if "Donator" not in segments_df.columns or "Donor_Segment" not in segments_df.columns:
        print(f"  ✗ donor_segments.csv must have Donator, Donor_Segment")
        return False

    donor_to_segment = dict(zip(segments_df["Donator"], segments_df["Donor_Segment"]))
    df = df[df["Party"].isin(["DEM", "REP"])].copy()
    df["Date"] = df["Received"].apply(parse_date)
    df = df[df["Date"].notna()].copy()
    df["Donation_Amount_USD"] = pd.to_numeric(df["Donation_Amount_USD"], errors="coerce")
    df = df[df["Donation_Amount_USD"] > 0].copy()
    df["Donor_Segment"] = df["Donator"].map(donor_to_segment)
    df = df[df["Donor_Segment"].notna()].copy()

    if len(df) == 0:
        print(f"  No donations with segment; skipping segment aggregations.")
        return True

    earliest_pm_date, closing_pm_date = get_polymarket_date_range(slug_dir)
    df["Date"] = pd.to_datetime(df["Date"])
    if earliest_pm_date is not None:
        if earliest_pm_date.tz is not None:
            earliest_pm_date = earliest_pm_date.tz_localize(None)
        df = df[df["Date"] >= earliest_pm_date].copy()
    if closing_pm_date is not None:
        if closing_pm_date.tz is not None:
            closing_pm_date = closing_pm_date.tz_localize(None)
        df = df[df["Date"] <= closing_pm_date].copy()

    if len(df) == 0:
        return True

    df["Year"] = df["Date"].dt.year
    df["Week"] = df["Date"].dt.isocalendar().week
    df["Month"] = df["Date"].dt.month
    df["Year_Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df["Year_Week"] = df["Year"].astype(str) + "-W" + df["Week"].astype(str).str.zfill(2)
    df["Year_Month"] = df["Date"].dt.to_period("M").astype(str)

    for freq, time_col in [("daily", "Year_Date"), ("weekly", "Year_Week"), ("monthly", "Year_Month")]:
        agg_path = output_dir / f"{freq}_cumulative_aggregations.csv"
        if not agg_path.exists():
            continue
        existing = pd.read_csv(agg_path)
        extra_list = []
        for seg in ["Small", "Medium", "Large"]:
            seg_df = df[df["Donor_Segment"] == seg]
            if len(seg_df) == 0:
                continue
            agg = _compute_segment_aggregations(seg_df, freq, time_col)
            agg["Segment"] = seg
            extra_list.append(agg)
        if not extra_list:
            continue
        combined = pd.concat([existing] + extra_list, ignore_index=True)
        combined.to_csv(agg_path, index=False)
    print(f"  ✓ Appended Small/Medium/Large segment aggregations -> {output_dir}")
    return True
