#!/usr/bin/env python3
"""
Build 4-line summary graphs per slug and frequency: donation cumulative (All),
prediction cumulative (all_users from trades_Plot), donation non-cumulative (All),
prediction non-cumulative (Polymarket price per period).
"""

import json
from datetime import timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import sys
SCRIPT_DIR = Path(__file__).resolve().parent
PARENT = SCRIPT_DIR.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
from prepare_cumulative_per_slug import get_polymarket_date_range
from plot_donation_and_polymarket import aggregate_prices_to_period

try:
    import seaborn as sns
    sns.set_style("whitegrid")
except ImportError:
    pass

plt.rcParams["figure.figsize"] = (14, 6)
plt.rcParams["font.size"] = 10

TIME_COLS = {"daily": "Year_Date", "weekly": "Year_Week", "monthly": "Year_Month"}

# Colors for the 4 lines
LINE_COLORS = {
    "donation_cumulative": "#2E86AB",
    "prediction_cumulative": "#E94F37",
    "donation_non_cumulative": "#44AF69",
    "prediction_non_cumulative": "#9B59B6",
}


def load_donation_cumulative(slug_dir: Path, freq: str) -> pd.DataFrame:
    """Load donation cumulative All segment. Returns DataFrame with time_col and Dem_Ratio."""
    time_col = TIME_COLS[freq]
    path = slug_dir / "output" / f"{freq}_cumulative_aggregations.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df[df["Segment"] == "All"].copy()
    if df.empty:
        return pd.DataFrame()
    return df[[time_col, "Dem_Ratio"]].dropna()


def load_donation_non_cumulative(slug_dir: Path, freq: str) -> pd.DataFrame:
    """Load donation non-cumulative All segment. Returns DataFrame with time_col and Dem_Ratio."""
    time_col = TIME_COLS[freq]
    path = slug_dir / "non_cumulative_donations" / "output" / f"{freq}_non_cumulative_aggregations.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df[df["Segment"] == "All"].copy()
    if df.empty:
        return pd.DataFrame()
    return df[[time_col, "Dem_Ratio"]].dropna()


def _date_to_period(date_val, time_col: str) -> str:
    """Convert a date to period string (Year_Date, Year_Week, or Year_Month)."""
    if hasattr(date_val, "strftime"):
        d = date_val
    else:
        d = pd.Timestamp(date_val)
    if time_col == "Year_Date":
        return d.strftime("%Y-%m-%d")
    if time_col == "Year_Week":
        y, w, _ = d.isocalendar()
        return f"{y}-W{w:02d}"
    # Year_Month (match donation: to_period("M").astype(str) -> "2024-04")
    return str(pd.Timestamp(d).to_period("M"))


def load_prediction_cumulative(
    trades_plot_base: Path,
    slug: str,
    slug_dir: Path,
    freq: str,
    time_col: str,
    closing_date,
) -> pd.Series:
    """
    Load prediction cumulative (all_users) from trades_Plot. Map day_offset to period,
    aggregate to frequency, return Series index=period, value=odds.
    """
    event_dir = trades_plot_base / slug
    if not event_dir.exists():
        return pd.Series(dtype=float)
    # First *_all_users_segment.csv
    candidates = sorted(event_dir.glob("*_all_users_segment.csv"))
    if not candidates:
        return pd.Series(dtype=float)
    path = candidates[0]
    df = pd.read_csv(path)
    df = df[df["segment"] == "all_users"].copy()
    if df.empty or "day_offset" not in df.columns or "odds" not in df.columns:
        return pd.Series(dtype=float)
    # closing_date: use .date() if Timestamp
    if hasattr(closing_date, "date"):
        close_d = closing_date.date()
    else:
        close_d = pd.Timestamp(closing_date).date()
    # Map day_offset to date then to period
    df["date"] = df["day_offset"].apply(lambda x: close_d + timedelta(days=int(x)))
    df["period"] = df["date"].apply(lambda d: _date_to_period(d, time_col))
    # For weekly/monthly take last odds per period (end-of-period)
    by_period = df.sort_values("day_offset").groupby("period")["odds"].last().reset_index()
    return by_period.set_index("period")["odds"]


def _get_democrat_outcome_column(pm_agg: pd.DataFrame, slug: str) -> str | None:
    """Return the column name in pm_agg that corresponds to Democrat (for prediction non-cumulative)."""
    non_no = [c for c in pm_agg.columns if (c or "").strip().lower() != "no"]
    if not non_no:
        return None
    # 1) Prefer column literally "Democrat" (case-insensitive)
    for c in non_no:
        if (c or "").strip().lower() == "democrat":
            return c
    # 2) Prefer column matching Democrat candidate from event_slugs.json (e.g. "Ruben Gallego")
    json_path = PARENT / "event_slugs.json"
    if json_path.exists():
        try:
            with open(json_path) as f:
                data = json.load(f)
            for item in data:
                if not isinstance(item, dict):
                    continue
                s = (item.get("slug") or item.get("event_slug") or "").strip()
                if s != slug:
                    continue
                dem = (item.get("democrat") or "").strip()
                if not dem:
                    break
                # "GALLEGO, RUBEN" -> last name "GALLEGO"
                dem_last = dem.split(",")[0].strip().lower() if "," in dem else dem.lower()
                for c in non_no:
                    if dem_last in (c or "").lower():
                        return c
                break
        except Exception:
            pass
    # 3) Fallback: first non-No (prefer "Democratic" if present)
    for c in non_no:
        if "democratic" in (c or "").lower():
            return c
    return non_no[0]


def load_prediction_non_cumulative(slug_dir: Path, slug: str, freq: str, time_col: str) -> pd.Series:
    """Load Polymarket price per period (last price in period). Always use Democrat outcome."""
    path = slug_dir / "polymarket_prices.csv"
    if not path.exists():
        return pd.Series(dtype=float)
    df = pd.read_csv(path)
    if df.empty or "timestamp" not in df.columns or "outcome_label" not in df.columns:
        return pd.Series(dtype=float)
    pm_agg = aggregate_prices_to_period(df, time_col)
    if pm_agg.empty:
        return pd.Series(dtype=float)
    col = _get_democrat_outcome_column(pm_agg, slug)
    if col is None:
        return pd.Series(dtype=float)
    return pm_agg[col]


def plot_summary_one_frequency(
    slug_dir: Path,
    slug: str,
    freq: str,
    trades_plot_base: Path,
    output_path: Path,
) -> None:
    """
    Build one 4-line graph for the given slug and frequency. Save to output_path.
    """
    time_col = TIME_COLS[freq]

    # 1. Donation cumulative (defines x-axis)
    don_cum = load_donation_cumulative(slug_dir, freq)
    if don_cum.empty:
        print(f"  Skip {slug} {freq}: no donation cumulative data")
        return
    periods = don_cum[time_col].dropna().tolist()
    n = len(periods)
    if n == 0:
        return

    # 2. Donation non-cumulative
    don_ncum = load_donation_non_cumulative(slug_dir, freq)

    # 3. Prediction cumulative (need closing_date)
    _, closing_date = get_polymarket_date_range(slug_dir)
    if closing_date is None:
        # Fallback: max date from polymarket_prices
        prices_file = slug_dir / "polymarket_prices.csv"
        if prices_file.exists():
            try:
                p = pd.read_csv(prices_file)
                if not p.empty and "timestamp" in p.columns:
                    closing_date = pd.to_datetime(p["timestamp"], unit="s").max()
                    closing_date = pd.Timestamp(year=closing_date.year, month=closing_date.month, day=closing_date.day)
            except Exception:
                pass
    pred_cum = load_prediction_cumulative(trades_plot_base, slug, slug_dir, freq, time_col, closing_date) if closing_date is not None else pd.Series(dtype=float)

    # 4. Prediction non-cumulative (always Democrat)
    pred_ncum = load_prediction_non_cumulative(slug_dir, slug, freq, time_col)

    # Align all to periods (donation cumulative x-axis)
    x_pos = range(n)
    don_cum_vals = don_cum.set_index(time_col).reindex(periods)["Dem_Ratio"].tolist()
    don_ncum_vals = don_ncum.set_index(time_col).reindex(periods)["Dem_Ratio"].tolist() if not don_ncum.empty else [float("nan")] * n
    pred_cum_vals = pred_cum.reindex(periods).ffill().tolist() if not pred_cum.empty else [float("nan")] * n
    pred_ncum_vals = pred_ncum.reindex(periods).tolist() if not pred_ncum.empty else [float("nan")] * n

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(x_pos, don_cum_vals, color=LINE_COLORS["donation_cumulative"], linewidth=2, marker="o", markersize=3, alpha=0.8, label="Donation cumulative (All)")
    ax.plot(x_pos, pred_cum_vals, color=LINE_COLORS["prediction_cumulative"], linewidth=2, marker="s", markersize=3, alpha=0.8, label="Prediction cumulative (all users)")
    ax.plot(x_pos, don_ncum_vals, color=LINE_COLORS["donation_non_cumulative"], linewidth=2, marker="^", markersize=3, alpha=0.8, label="Donation non-cumulative (All)")
    ax.plot(x_pos, pred_ncum_vals, color=LINE_COLORS["prediction_non_cumulative"], linewidth=2, linestyle="--", marker="d", markersize=3, alpha=0.8, label="Prediction non-cumulative (Polymarket)")
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
    ax.set_xlabel(f"{freq.capitalize()} Period", fontsize=12, fontweight="bold")
    ax.set_ylabel("Ratio / Odds (0-1)", fontsize=12, fontweight="bold")
    ax.set_title(f"{slug} — Summary ({freq}): Donation cum, Prediction cum, Donation non-cum, Prediction non-cum", fontsize=14, fontweight="bold", pad=20)
    step = max(1, n // 15) if freq != "daily" else max(1, n // 30)
    ax.set_xticks(range(0, n, step))
    ax.set_xticklabels(periods[::step], rotation=45, ha="right")
    ax.set_ylim([0, 1])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.2f}"))
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path.name}")
