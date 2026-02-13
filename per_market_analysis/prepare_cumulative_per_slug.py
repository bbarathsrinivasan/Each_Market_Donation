#!/usr/bin/env python3
"""
Prepare cumulative donation ratio time series for one event slug (All donors only).
Reads slug_dir/donations_filtered.csv, computes daily/weekly/monthly cumulative Dem/(Dem+Rep)
and Rep/(Dem+Rep), saves to slug_dir/output/.
"""

from pathlib import Path

import numpy as np
import pandas as pd


def parse_date(date_str):
    """Parse date from MMDDYYYY format (same as cumulative_ratio_analysis)."""
    if pd.isna(date_str):
        return pd.NaT
    try:
        date_str = str(int(date_str))
    except (ValueError, TypeError):
        return pd.NaT
    if len(date_str) < 7:
        return pd.NaT
    try:
        if len(date_str) == 8:
            month = int(date_str[:2])
            day = int(date_str[2:4])
            year = int(date_str[4:])
        elif len(date_str) == 7:
            month = int(date_str[0])
            day = int(date_str[1:3])
            year = int(date_str[3:])
        else:
            return pd.NaT
        return pd.Timestamp(year=year, month=month, day=day)
    except Exception:
        return pd.NaT


def get_polymarket_date_range(slug_dir: Path) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """
    Get the earliest and latest (closing) date from polymarket_prices.csv.
    Also checks polymarket_metadata.json for endDate if available.
    Returns (earliest_date, closing_date) or (None, None) if file doesn't exist or is empty.
    """
    prices_file = slug_dir / "polymarket_prices.csv"
    metadata_file = slug_dir / "polymarket_metadata.json"
    
    earliest_date = None
    closing_date = None
    
    # Try to get closing date from metadata first
    if metadata_file.exists():
        try:
            import json
            with open(metadata_file) as f:
                metadata = json.load(f)
            # Check if it's an event with markets
            if "markets" in metadata and len(metadata["markets"]) > 0:
                # Get endDate from first market
                market = metadata["markets"][0]
                if "endDate" in market:
                    closing_date = pd.to_datetime(market["endDate"]).normalize()
                    # Remove timezone info to make it timezone-naive
                    if closing_date.tz is not None:
                        closing_date = closing_date.tz_localize(None)
            elif "endDate" in metadata:
                closing_date = pd.to_datetime(metadata["endDate"]).normalize()
                # Remove timezone info to make it timezone-naive
                if closing_date.tz is not None:
                    closing_date = closing_date.tz_localize(None)
        except Exception as e:
            print(f"  Warning: Could not read Polymarket metadata: {e}")
    
    # Get date range from prices file
    if prices_file.exists():
        try:
            prices_df = pd.read_csv(prices_file)
            if not prices_df.empty and "timestamp" in prices_df.columns:
                # Convert Unix timestamp to datetime
                prices_df["dt"] = pd.to_datetime(prices_df["timestamp"], unit="s")
                earliest_dt = prices_df["dt"].min()
                latest_dt = prices_df["dt"].max()
                # Convert to date (midnight)
                earliest_date = pd.Timestamp(year=earliest_dt.year, month=earliest_dt.month, day=earliest_dt.day)
                # Use latest date from prices if no metadata closing date
                if closing_date is None:
                    closing_date = pd.Timestamp(year=latest_dt.year, month=latest_dt.month, day=latest_dt.day)
        except Exception as e:
            print(f"  Warning: Could not read Polymarket prices: {e}")
    
    return earliest_date, closing_date


def prepare_cumulative_aggregations(donations_path: Path, output_dir: Path, slug_dir: Path) -> bool:
    """
    Read donations_filtered.csv, compute daily, weekly, and monthly cumulative ratios (All donors).
    Start cumulative calculation from the earliest Polymarket price date (if available).
    Write daily/weekly/monthly_cumulative_aggregations.csv to output_dir.
    Returns True if successful.
    """
    if not donations_path.exists():
        print(f"  ✗ Not found: {donations_path}")
        return False

    df = pd.read_csv(donations_path, low_memory=False)
    if len(df) == 0:
        output_dir.mkdir(parents=True, exist_ok=True)
        for freq, col in [("daily", "Year_Date"), ("weekly", "Year_Week"), ("monthly", "Year_Month")]:
            empty = pd.DataFrame(columns=[
                col, "DEM", "REP", "Cumulative_DEM", "Cumulative_REP",
                "Total_Cumulative", "Dem_Ratio", "Rep_Ratio", "Segment"
            ])
            empty.to_csv(output_dir / f"{freq}_cumulative_aggregations.csv", index=False)
        print(f"  No donation rows; wrote empty aggregations.")
        return True

    df = df[df["Party"].isin(["DEM", "REP"])].copy()
    df["Date"] = df["Received"].apply(parse_date)
    df = df[df["Date"].notna()].copy()
    df["Donation_Amount_USD"] = pd.to_numeric(df["Donation_Amount_USD"], errors="coerce")
    df = df[df["Donation_Amount_USD"] > 0].copy()
    
    # Filter donations to Polymarket date range (start from earliest, end at closing)
    earliest_pm_date, closing_pm_date = get_polymarket_date_range(slug_dir)
    df["Date"] = pd.to_datetime(df["Date"])
    
    if earliest_pm_date is not None:
        # Ensure timezone-naive for comparison
        if earliest_pm_date.tz is not None:
            earliest_pm_date = earliest_pm_date.tz_localize(None)
        df = df[df["Date"] >= earliest_pm_date].copy()
        print(f"  Filtered donations to start from Polymarket date: {earliest_pm_date.date()}")
    
    if closing_pm_date is not None:
        # Ensure timezone-naive for comparison
        if closing_pm_date.tz is not None:
            closing_pm_date = closing_pm_date.tz_localize(None)
        df = df[df["Date"] <= closing_pm_date].copy()
        print(f"  Filtered donations to end at Polymarket closing date: {closing_pm_date.date()}")
    
    if len(df) == 0:
        print(f"  No donations in Polymarket date range; wrote empty aggregations.")
        output_dir.mkdir(parents=True, exist_ok=True)
        for freq, col in [("daily", "Year_Date"), ("weekly", "Year_Week"), ("monthly", "Year_Month")]:
            pd.DataFrame(columns=[col, "DEM", "REP", "Cumulative_DEM", "Cumulative_REP",
                                  "Total_Cumulative", "Dem_Ratio", "Rep_Ratio", "Segment"]).to_csv(
                output_dir / f"{freq}_cumulative_aggregations.csv", index=False)
        return True
    
    if earliest_pm_date is None and closing_pm_date is None:
        print(f"  No Polymarket prices found; using all donation dates")
    df["Year"] = df["Date"].dt.year
    df["Week"] = df["Date"].dt.isocalendar().week
    df["Month"] = df["Date"].dt.month
    df["Year_Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df["Year_Week"] = df["Year"].astype(str) + "-W" + df["Week"].astype(str).str.zfill(2)
    df["Year_Month"] = df["Date"].dt.to_period("M").astype(str)

    # Daily
    daily_by_party = df.groupby(["Year_Date", "Party"])["Donation_Amount_USD"].sum().reset_index()
    daily_by_party.columns = ["Year_Date", "Party", "Daily_Donation"]
    daily_pivot = daily_by_party.pivot(index="Year_Date", columns="Party", values="Daily_Donation").fillna(0)
    daily_pivot = daily_pivot.sort_index()
    if "DEM" not in daily_pivot.columns:
        daily_pivot["DEM"] = 0
    if "REP" not in daily_pivot.columns:
        daily_pivot["REP"] = 0
    daily_pivot["Cumulative_DEM"] = daily_pivot["DEM"].cumsum()
    daily_pivot["Cumulative_REP"] = daily_pivot["REP"].cumsum()
    daily_pivot["Total_Cumulative"] = daily_pivot["Cumulative_DEM"] + daily_pivot["Cumulative_REP"]
    daily_pivot["Dem_Ratio"] = daily_pivot.apply(
        lambda r: (r["Cumulative_DEM"] / r["Total_Cumulative"]) if r["Total_Cumulative"] > 0 else np.nan, axis=1
    )
    daily_pivot["Rep_Ratio"] = daily_pivot.apply(
        lambda r: (r["Cumulative_REP"] / r["Total_Cumulative"]) if r["Total_Cumulative"] > 0 else np.nan, axis=1
    )
    daily_pivot["Segment"] = "All"
    daily_pivot = daily_pivot.reset_index()

    # Weekly
    weekly_by_party = df.groupby(["Year_Week", "Party"])["Donation_Amount_USD"].sum().reset_index()
    weekly_by_party.columns = ["Year_Week", "Party", "Weekly_Donation"]
    weekly_pivot = weekly_by_party.pivot(index="Year_Week", columns="Party", values="Weekly_Donation").fillna(0)
    if "DEM" not in weekly_pivot.columns:
        weekly_pivot["DEM"] = 0
    if "REP" not in weekly_pivot.columns:
        weekly_pivot["REP"] = 0
    weekly_pivot["Cumulative_DEM"] = weekly_pivot["DEM"].cumsum()
    weekly_pivot["Cumulative_REP"] = weekly_pivot["REP"].cumsum()
    weekly_pivot["Total_Cumulative"] = weekly_pivot["Cumulative_DEM"] + weekly_pivot["Cumulative_REP"]
    weekly_pivot["Dem_Ratio"] = weekly_pivot.apply(
        lambda r: (r["Cumulative_DEM"] / r["Total_Cumulative"]) if r["Total_Cumulative"] > 0 else np.nan, axis=1
    )
    weekly_pivot["Rep_Ratio"] = weekly_pivot.apply(
        lambda r: (r["Cumulative_REP"] / r["Total_Cumulative"]) if r["Total_Cumulative"] > 0 else np.nan, axis=1
    )
    weekly_pivot["Segment"] = "All"
    weekly_pivot = weekly_pivot.reset_index()

    # Monthly
    monthly_by_party = df.groupby(["Year_Month", "Party"])["Donation_Amount_USD"].sum().reset_index()
    monthly_by_party.columns = ["Year_Month", "Party", "Monthly_Donation"]
    monthly_pivot = monthly_by_party.pivot(index="Year_Month", columns="Party", values="Monthly_Donation").fillna(0)
    if "DEM" not in monthly_pivot.columns:
        monthly_pivot["DEM"] = 0
    if "REP" not in monthly_pivot.columns:
        monthly_pivot["REP"] = 0
    monthly_pivot["Cumulative_DEM"] = monthly_pivot["DEM"].cumsum()
    monthly_pivot["Cumulative_REP"] = monthly_pivot["REP"].cumsum()
    monthly_pivot["Total_Cumulative"] = monthly_pivot["Cumulative_DEM"] + monthly_pivot["Cumulative_REP"]
    monthly_pivot["Dem_Ratio"] = monthly_pivot.apply(
        lambda r: (r["Cumulative_DEM"] / r["Total_Cumulative"]) if r["Total_Cumulative"] > 0 else np.nan, axis=1
    )
    monthly_pivot["Rep_Ratio"] = monthly_pivot.apply(
        lambda r: (r["Cumulative_REP"] / r["Total_Cumulative"]) if r["Total_Cumulative"] > 0 else np.nan, axis=1
    )
    monthly_pivot["Segment"] = "All"
    monthly_pivot = monthly_pivot.reset_index()

    output_dir.mkdir(parents=True, exist_ok=True)
    daily_pivot.to_csv(output_dir / "daily_cumulative_aggregations.csv", index=False)
    weekly_pivot.to_csv(output_dir / "weekly_cumulative_aggregations.csv", index=False)
    monthly_pivot.to_csv(output_dir / "monthly_cumulative_aggregations.csv", index=False)
    print(f"  ✓ Daily/weekly/monthly aggregations -> {output_dir}")
    return True


def run_prepare_cumulative_for_slug(slug_dir: Path) -> bool:
    """Run cumulative aggregation for one slug; donations_filtered.csv -> output/."""
    donations_path = slug_dir / "donations_filtered.csv"
    output_dir = slug_dir / "output"
    return prepare_cumulative_aggregations(donations_path, output_dir, slug_dir)
