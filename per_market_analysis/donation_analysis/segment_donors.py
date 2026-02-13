#!/usr/bin/env python3
"""
Segment election donors per event into Small, Medium, and Large categories
based on cumulative donation amounts using percentile thresholds (33.3rd and 66.6th).
"""

from pathlib import Path

import pandas as pd


def segment_donors_for_slug(slug_dir: Path) -> bool:
    """
    Segment donors for one event slug based on cumulative donation amounts.
    Reads slug_dir/donations_filtered.csv, computes percentiles, assigns segments,
    saves slug_dir/donor_segments.csv.
    Returns True if successful.
    """
    donations_path = slug_dir / "donations_filtered.csv"
    if not donations_path.exists():
        print(f"  ✗ Not found: {donations_path}")
        return False

    try:
        df = pd.read_csv(donations_path, low_memory=False)
    except Exception as e:
        print(f"  ✗ Error loading donations: {e}")
        return False

    if len(df) == 0:
        print(f"  No donation rows; skipping segmentation.")
        return True

    # Required columns
    if "Donator" not in df.columns or "Donation_Amount_USD" not in df.columns:
        print(f"  ✗ Missing required columns (Donator, Donation_Amount_USD)")
        return False

    df["Donation_Amount_USD"] = pd.to_numeric(df["Donation_Amount_USD"], errors="coerce").fillna(0)
    donor_stats = df.groupby("Donator").agg(
        Cumulative_Donation_USD=("Donation_Amount_USD", "sum"),
        Number_of_Donations=("Donation_Amount_USD", "count"),
    ).reset_index()
    donor_stats = donor_stats[donor_stats["Cumulative_Donation_USD"] > 0]

    if len(donor_stats) == 0:
        print(f"  No donors with positive donations; skipping segmentation.")
        return True

    # Percentile thresholds
    p33_3 = donor_stats["Cumulative_Donation_USD"].quantile(0.333)
    p66_6 = donor_stats["Cumulative_Donation_USD"].quantile(0.666)

    def classify_segment(cumulative_donation: float) -> str:
        if cumulative_donation <= p33_3:
            return "Small"
        elif cumulative_donation <= p66_6:
            return "Medium"
        else:
            return "Large"

    donor_stats["Donor_Segment"] = donor_stats["Cumulative_Donation_USD"].apply(classify_segment)
    donor_stats = donor_stats.sort_values("Cumulative_Donation_USD", ascending=False)

    out_path = slug_dir / "donor_segments.csv"
    donor_stats.to_csv(out_path, index=False)
    print(f"  ✓ Segmented {len(donor_stats):,} donors -> {out_path.name} (p33.3=${p33_3:,.2f}, p66.6=${p66_6:,.2f})")
    return True
