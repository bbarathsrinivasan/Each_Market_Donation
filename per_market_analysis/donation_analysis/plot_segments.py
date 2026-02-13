#!/usr/bin/env python3
"""
Generate segment-specific plots: all segments together and per-segment (Small, Medium, Large)
with Polymarket prices on the same 0-1 axis.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
try:
    import seaborn as sns
    sns.set_style("whitegrid")
except ImportError:
    pass

import sys
SCRIPT_DIR = Path(__file__).resolve().parent
PARENT = SCRIPT_DIR.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
from plot_donation_and_polymarket import (
    DONATION_COLOR,
    POLYMARKET_COLORS,
    aggregate_prices_to_period,
)

plt.rcParams["figure.figsize"] = (14, 6)
plt.rcParams["font.size"] = 10

SEGMENT_COLORS = {"All": "#2E86AB", "Small": "#44AF69", "Medium": "#F4A261", "Large": "#9B59B6"}


def _plot_one(
    slug_dir: Path,
    frequency: str,
    slug: str,
    segment_name: str,
    agg: pd.DataFrame,
    time_col: str,
    out_suffix: str,
) -> None:
    """Single plot: one segment's Dem_Ratio + Polymarket."""
    plots_dir = slug_dir / "plots"
    prices_file = slug_dir / "polymarket_prices.csv"
    plot_data = agg[[time_col, "Dem_Ratio"]].dropna()
    if plot_data.empty:
        return
    fig, ax = plt.subplots(figsize=(14, 6))
    x_pos = range(len(plot_data))
    color = SEGMENT_COLORS.get(segment_name, DONATION_COLOR)
    ax.plot(
        x_pos,
        plot_data["Dem_Ratio"],
        linewidth=2,
        color=color,
        marker="o",
        markersize=3,
        alpha=0.7,
        label=f"Donation Dem/(Dem+Rep) ({segment_name})",
    )
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5, label="0.5")
    if prices_file.exists():
        prices_df = pd.read_csv(prices_file)
        if not prices_df.empty and "timestamp" in prices_df.columns and "outcome_label" in prices_df.columns:
            period_col = {"daily": "Year_Date", "weekly": "Year_Week", "monthly": "Year_Month"}.get(frequency, "Year_Week")
            pm_agg = aggregate_prices_to_period(prices_df, period_col)
            if not pm_agg.empty:
                periods = plot_data[time_col].tolist()
                outcomes_to_plot = [c for c in pm_agg.columns if c != "No"]
                for i, outcome in enumerate(outcomes_to_plot):
                    c = POLYMARKET_COLORS[i % len(POLYMARKET_COLORS)]
                    series = [pm_agg.loc[p, outcome] if p in pm_agg.index else float("nan") for p in periods]
                    ax.plot(x_pos, series, linewidth=1.5, color=c, linestyle="--", marker="s", markersize=2, alpha=0.8, label=f"Polymarket: {outcome}")
    ax.set_xlabel(f"{frequency.capitalize()} Period", fontsize=12, fontweight="bold")
    ax.set_ylabel("Ratio / Price (0-1)", fontsize=12, fontweight="bold")
    ax.set_title(f"{slug} — Donation cumulative ratio ({segment_name}) + Polymarket ({frequency})", fontsize=14, fontweight="bold", pad=20)
    step = max(1, len(plot_data) // 15) if frequency != "daily" else max(1, len(plot_data) // 30)
    ax.set_xticks(range(0, len(plot_data), step))
    ax.set_xticklabels(plot_data[time_col].iloc[::step].tolist(), rotation=45, ha="right")
    ax.set_ylim([0, 1])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.2f}"))
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plots_dir.mkdir(parents=True, exist_ok=True)
    out_path = plots_dir / f"cumulative_ratio_{frequency}_{out_suffix}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path.name}")


def plot_segments_for_slug(slug_dir: Path, slug: str) -> None:
    """
    Generate segment plots for one slug: all segments on one chart, plus one chart per segment
    (Small, Medium, Large) for daily, weekly, and monthly.
    """
    output_dir = slug_dir / "output"
    time_cols = {"daily": "Year_Date", "weekly": "Year_Week", "monthly": "Year_Month"}
    for frequency in ["daily", "weekly", "monthly"]:
        time_col = time_cols[frequency]
        agg_file = output_dir / f"{frequency}_cumulative_aggregations.csv"
        if not agg_file.exists():
            continue
        full_agg = pd.read_csv(agg_file)
        segments_in_file = full_agg["Segment"].unique().tolist() if "Segment" in full_agg.columns else []

        # Plot 1: All segments together (All + Small + Medium + Large if present)
        for seg in ["All", "Small", "Medium", "Large"]:
            if seg not in segments_in_file:
                continue
            seg_agg = full_agg[full_agg["Segment"] == seg].copy()
            _plot_one(slug_dir, frequency, slug, seg, seg_agg, time_col, seg.lower())

        # One combined plot with all segments (multiple lines) + Polymarket
        all_agg = full_agg[full_agg["Segment"] == "All"]
        if all_agg.empty:
            continue
        periods = all_agg[time_col].dropna().tolist()
        n = len(periods)
        if n == 0:
            continue
        fig, ax = plt.subplots(figsize=(14, 6))
        plots_dir = slug_dir / "plots"
        prices_file = slug_dir / "polymarket_prices.csv"
        x_pos = range(n)
        for seg in ["All", "Small", "Medium", "Large"]:
            if seg not in segments_in_file:
                continue
            seg_agg = full_agg[full_agg["Segment"] == seg][[time_col, "Dem_Ratio"]].dropna()
            seg_agg = seg_agg.set_index(time_col).reindex(periods)["Dem_Ratio"]
            ratios = seg_agg.tolist()
            color = SEGMENT_COLORS.get(seg, DONATION_COLOR)
            ax.plot(x_pos, ratios, linewidth=2, color=color, marker="o", markersize=3, alpha=0.7, label=seg)
        ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
        if prices_file.exists():
            prices_df = pd.read_csv(prices_file)
            if not prices_df.empty and "timestamp" in prices_df.columns and "outcome_label" in prices_df.columns:
                period_col = time_cols[frequency]
                pm_agg = aggregate_prices_to_period(prices_df, period_col)
                if not pm_agg.empty:
                    for i, outcome in enumerate([c for c in pm_agg.columns if c != "No"]):
                        c = POLYMARKET_COLORS[i % len(POLYMARKET_COLORS)]
                        series = [pm_agg.loc[p, outcome] if p in pm_agg.index else float("nan") for p in periods]
                        ax.plot(x_pos, series, linewidth=1.5, color=c, linestyle="--", marker="s", markersize=2, alpha=0.8, label=f"Polymarket: {outcome}")
        ax.set_xlabel(f"{frequency.capitalize()} Period", fontsize=12, fontweight="bold")
        ax.set_ylabel("Ratio / Price (0-1)", fontsize=12, fontweight="bold")
        ax.set_title(f"{slug} — Donation cumulative ratio (all segments) + Polymarket ({frequency})", fontsize=14, fontweight="bold", pad=20)
        step = max(1, n // 15) if frequency != "daily" else max(1, n // 30)
        ax.set_xticks(range(0, n, step))
        ax.set_xticklabels(periods[::step], rotation=45, ha="right")
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
