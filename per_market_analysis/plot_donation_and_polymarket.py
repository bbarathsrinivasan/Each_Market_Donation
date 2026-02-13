#!/usr/bin/env python3
"""
Plot donation cumulative ratio (Dem/(Dem+Rep)) and Polymarket price(s) on the same 0-1 axis.
One figure per frequency (daily, weekly, monthly) per slug.
"""

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
try:
    import seaborn as sns
    sns.set_style("whitegrid")
except ImportError:
    pass

plt.rcParams["figure.figsize"] = (14, 6)
plt.rcParams["font.size"] = 10

DONATION_COLOR = "#2E86AB"
POLYMARKET_COLORS = ["#E94F37", "#3F88C5", "#44AF69", "#F4A261", "#9B59B6", "#F39C12"]


def aggregate_prices_to_period(
    prices_df: pd.DataFrame, period_col: str
) -> pd.DataFrame:
    """
    Aggregate polymarket_prices by period (Year_Date, Year_Week, or Year_Month).
    prices_df must have columns: timestamp (unix), outcome_label, price.
    Returns DataFrame with one row per (period, outcome_label), price = last in period.
    """
    if prices_df.empty or "timestamp" not in prices_df.columns:
        return pd.DataFrame()
    df = prices_df.copy()
    df["dt"] = pd.to_datetime(df["timestamp"], unit="s")
    if period_col == "Year_Date":
        df["period"] = df["dt"].dt.strftime("%Y-%m-%d")
    elif period_col == "Year_Week":
        df["period"] = df["dt"].dt.isocalendar().year.astype(str) + "-W" + df["dt"].dt.isocalendar().week.astype(str).str.zfill(2)
    else:
        df["period"] = df["dt"].dt.to_period("M").astype(str)
    last = df.sort_values("timestamp").groupby(["period", "outcome_label"])["price"].last().reset_index()
    return last.pivot(index="period", columns="outcome_label", values="price")


def plot_ratio_with_polymarket(
    slug_dir: Path,
    frequency: str,
    slug: str,
) -> None:
    """
    Load donation cumulative ratio (All segment) and Polymarket prices for slug;
    aggregate Polymarket to same frequency; plot on same 0-1 axis.
    """
    output_dir = slug_dir / "output"
    plots_dir = slug_dir / "plots"
    time_col = {"daily": "Year_Date", "weekly": "Year_Week", "monthly": "Year_Month"}.get(frequency, "Year_Week")
    agg_file = output_dir / f"{frequency}_cumulative_aggregations.csv"
    prices_file = slug_dir / "polymarket_prices.csv"

    if not agg_file.exists():
        print(f"  ✗ Missing {agg_file}")
        return

    agg = pd.read_csv(agg_file)
    agg = agg[agg["Segment"] == "All"].copy()
    if agg.empty:
        print(f"  No All-segment data in {agg_file}")
        return

    plot_data = agg[[time_col, "Dem_Ratio"]].dropna()
    if plot_data.empty:
        print(f"  No Dem_Ratio data for {frequency}")
        return

    fig, ax = plt.subplots(figsize=(14, 6))
    x_pos = range(len(plot_data))
    ax.plot(
        x_pos,
        plot_data["Dem_Ratio"],
        linewidth=2,
        color=DONATION_COLOR,
        marker="o",
        markersize=3,
        alpha=0.7,
        label="Donation Dem/(Dem+Rep)",
    )
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5, label="0.5")

    # Polymarket: align by period
    if prices_file.exists():
        prices_df = pd.read_csv(prices_file)
        if not prices_df.empty and "timestamp" in prices_df.columns and "outcome_label" in prices_df.columns:
            period_col = {"daily": "Year_Date", "weekly": "Year_Week", "monthly": "Year_Month"}.get(frequency, "Year_Week")
            pm_agg = aggregate_prices_to_period(prices_df, period_col)
            if not pm_agg.empty:
                periods = plot_data[time_col].tolist()
                outcomes_to_plot = [c for c in pm_agg.columns if c != "No"]
                for i, outcome in enumerate(outcomes_to_plot):
                    color = POLYMARKET_COLORS[i % len(POLYMARKET_COLORS)]
                    series = []
                    for p in periods:
                        if p in pm_agg.index:
                            series.append(pm_agg.loc[p, outcome])
                        else:
                            series.append(float("nan"))
                    ax.plot(
                        x_pos,
                        series,
                        linewidth=1.5,
                        color=color,
                        linestyle="--",
                        marker="s",
                        markersize=2,
                        alpha=0.8,
                        label=f"Polymarket: {outcome}",
                    )

    ax.set_xlabel(f"{frequency.capitalize()} Period", fontsize=12, fontweight="bold")
    ax.set_ylabel("Ratio / Price (0-1)", fontsize=12, fontweight="bold")
    ax.set_title(f"{slug} — Donation cumulative ratio + Polymarket ({frequency})", fontsize=14, fontweight="bold", pad=20)
    step = max(1, len(plot_data) // 15) if frequency != "daily" else max(1, len(plot_data) // 30)
    ax.set_xticks(range(0, len(plot_data), step))
    ax.set_xticklabels(plot_data[time_col].iloc[::step].tolist(), rotation=45, ha="right")
    ax.set_ylim([0, 1])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.2f}"))
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plots_dir.mkdir(parents=True, exist_ok=True)
    out_path = plots_dir / f"cumulative_ratio_{frequency}_with_polymarket.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path.name}")


def run_plots_for_slug(slug: str, slug_dir: Path) -> None:
    """Generate daily, weekly, and monthly donation+Polymarket plots for one slug."""
    plot_ratio_with_polymarket(slug_dir, "daily", slug)
    plot_ratio_with_polymarket(slug_dir, "weekly", slug)
    plot_ratio_with_polymarket(slug_dir, "monthly", slug)
