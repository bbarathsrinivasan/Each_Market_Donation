#!/usr/bin/env python3
"""
Update the cumulative_prediction_odds column in summary_odds_weekly.csv using
current trades_Plot data. Use this when better trade data becomes available.

Reads summary_odds_weekly.csv, recomputes cumulative prediction odds per (election_name, week)
from trades_Plot/{slug}/*_all_users_segment.csv (same logic as build_summary_plots),
then writes back the CSV with only cumulative_prediction_odds changed.
"""

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PARENT = SCRIPT_DIR.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
from prepare_cumulative_per_slug import get_polymarket_date_range
try:
    from Summary_analysis.build_summary_plots import (
        TIME_COLS,
        load_prediction_cumulative,
    )
except ImportError:
    from build_summary_plots import (
        TIME_COLS,
        load_prediction_cumulative,
    )


def update_cumulative_prediction_odds(
    csv_path: Path,
    per_market_base: Path,
    trades_plot_base: Path,
    out_path: Path | None = None,
) -> Path:
    """
    Read csv_path (summary_odds_weekly.csv), recompute cumulative_prediction_odds
    from trades_Plot for each (election_name, week), write to out_path (default: overwrite csv_path).
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Not found: {csv_path}")
    df = pd.read_csv(csv_path)
    if "election_name" not in df.columns or "week" not in df.columns:
        raise ValueError(f"CSV must have columns election_name, week. Got: {list(df.columns)}")

    freq = "weekly"
    time_col = TIME_COLS[freq]
    slug_weeks: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        slug = row["election_name"]
        w = row["week"]
        if slug not in slug_weeks:
            slug_weeks[slug] = []
        if w not in slug_weeks[slug]:
            slug_weeks[slug].append(w)

    # Build mapping (election_name, week) -> cumulative_prediction_odds
    new_odds: dict[tuple[str, str], float] = {}
    for slug, weeks in slug_weeks.items():
        slug_dir = per_market_base / slug
        if not slug_dir.is_dir():
            continue
        _, closing_date = get_polymarket_date_range(slug_dir)
        if closing_date is None:
            if (slug_dir / "polymarket_prices.csv").exists():
                try:
                    p = pd.read_csv(slug_dir / "polymarket_prices.csv")
                    if not p.empty and "timestamp" in p.columns:
                        closing_date = pd.to_datetime(p["timestamp"], unit="s").max()
                        closing_date = pd.Timestamp(closing_date.year, closing_date.month, closing_date.day)
                except Exception:
                    pass
        if closing_date is None:
            continue
        pred_cum = load_prediction_cumulative(trades_plot_base, slug, slug_dir, freq, time_col, closing_date)
        if pred_cum.empty:
            continue
        # Align to these weeks and forward-fill (same as in build_summary_plots)
        weeks_sorted = sorted(weeks)
        filled = pred_cum.reindex(weeks_sorted).ffill()
        for w in weeks:
            new_odds[(slug, w)] = filled.get(w, float("nan"))

    # Update column
    def get_odds(row: pd.Series) -> float:
        key = (row["election_name"], row["week"])
        return new_odds.get(key, row.get("cumulative_prediction_odds", float("nan")))

    df["cumulative_prediction_odds"] = df.apply(get_odds, axis=1)
    dest = out_path or csv_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    return dest


def main() -> None:
    output_dir = SCRIPT_DIR / "output"
    csv_path = output_dir / "summary_odds_weekly.csv"
    per_market_base = PARENT
    trades_plot_base = PARENT / "trades_Plot"

    if not csv_path.exists():
        print(f"Not found: {csv_path}")
        print("Run build_summary_csvs.py first to create summary_odds_weekly.csv")
        sys.exit(1)

    update_cumulative_prediction_odds(csv_path, per_market_base, trades_plot_base)
    print(f"Updated cumulative_prediction_odds in {csv_path}")


if __name__ == "__main__":
    main()
