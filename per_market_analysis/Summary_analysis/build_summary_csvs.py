#!/usr/bin/env python3
"""
Build two weekly CSVs from Summary-analysis data:

1. summary_odds_weekly.csv
   Primary key: election_name, week
   Variables: winning_side_dem (1=Dem, 0=Rep), cumulative_prediction_odds,
   non_cumulative_prediction_odds, cumulative_donation_odds, non_cumulative_donation_odds.

2. summary_segment_odds_weekly.csv
   Primary key: election_name, week
   Variables: cumulative and non-cumulative donation odds for Small, Medium, Large segments.

Uses the same data sources as build_summary_plots (donation cumulative/non-cumulative,
prediction cumulative from trades_Plot, prediction non-cumulative from Polymarket).
"""

import json
from datetime import timedelta
from pathlib import Path

import pandas as pd

import sys
SCRIPT_DIR = Path(__file__).resolve().parent
PARENT = SCRIPT_DIR.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
from prepare_cumulative_per_slug import get_polymarket_date_range
from plot_donation_and_polymarket import aggregate_prices_to_period

try:
    from .build_summary_plots import (
        TIME_COLS,
        load_donation_cumulative,
        load_donation_non_cumulative,
        load_prediction_cumulative,
        load_prediction_non_cumulative,
        _date_to_period,
    )
except ImportError:
    from build_summary_plots import (
        TIME_COLS,
        load_donation_cumulative,
        load_donation_non_cumulative,
        load_prediction_cumulative,
        load_prediction_non_cumulative,
        _date_to_period,
    )


def _winning_side_dem_from_metadata(slug_dir: Path) -> int | None:
    """
    Infer winning_side_dem (1 = Democrat won, 0 = Republican won) from polymarket_metadata.json.
    Looks for first market 'Will a Democrat win...'; outcomePrices ['1','0'] -> 1, else 0.
    Returns None if not found or not resolved.
    """
    path = slug_dir / "polymarket_metadata.json"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return None
    for m in data.get("markets") or []:
        q = (m.get("question") or "").strip().lower()
        if "democrat" not in q or "win" not in q:
            continue
        prices = m.get("outcomePrices")
        if prices is None:
            continue
        if isinstance(prices, str):
            prices = json.loads(prices) if prices.startswith("[") else None
        if not isinstance(prices, list) or len(prices) < 2:
            continue
        # Yes = first outcome; if Yes paid 1, Democrat won
        yes_price = str(prices[0]).strip()
        return 1 if yes_price == "1" else 0
    return None


def _load_donation_cumulative_by_segment(slug_dir: Path, freq: str) -> pd.DataFrame:
    """Load donation cumulative for all segments. Columns: time_col, Segment, Dem_Ratio."""
    time_col = TIME_COLS[freq]
    path = slug_dir / "output" / f"{freq}_cumulative_aggregations.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty or "Segment" not in df.columns:
        return pd.DataFrame()
    return df[[time_col, "Segment", "Dem_Ratio"]].dropna(subset=[time_col, "Dem_Ratio"])


def _load_donation_non_cumulative_by_segment(slug_dir: Path, freq: str) -> pd.DataFrame:
    """Load donation non-cumulative for all segments. Columns: time_col, Segment, Dem_Ratio."""
    time_col = TIME_COLS[freq]
    path = slug_dir / "non_cumulative_donations" / "output" / f"{freq}_non_cumulative_aggregations.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty or "Segment" not in df.columns:
        return pd.DataFrame()
    return df[[time_col, "Segment", "Dem_Ratio"]].dropna(subset=[time_col, "Dem_Ratio"])


def build_summary_odds_weekly(
    slugs: list[str],
    per_market_base: Path,
    trades_plot_base: Path,
    output_dir: Path,
) -> Path:
    """
    Build summary_odds_weekly.csv: (election_name, week) + winning_side_dem,
    cumulative_prediction_odds, non_cumulative_prediction_odds,
    cumulative_donation_odds, non_cumulative_donation_odds.
    """
    freq = "weekly"
    time_col = TIME_COLS[freq]
    rows = []

    for slug in slugs:
        slug_dir = per_market_base / slug
        if not slug_dir.is_dir():
            continue

        winning_side_dem = _winning_side_dem_from_metadata(slug_dir)

        don_cum = load_donation_cumulative(slug_dir, freq)
        if don_cum.empty:
            continue
        periods = don_cum[time_col].dropna().tolist()

        don_ncum = load_donation_non_cumulative(slug_dir, freq)
        _, closing_date = get_polymarket_date_range(slug_dir)
        if closing_date is None and (slug_dir / "polymarket_prices.csv").exists():
            try:
                p = pd.read_csv(slug_dir / "polymarket_prices.csv")
                if not p.empty and "timestamp" in p.columns:
                    closing_date = pd.to_datetime(p["timestamp"], unit="s").max()
                    closing_date = pd.Timestamp(closing_date.year, closing_date.month, closing_date.day)
            except Exception:
                pass
        pred_cum = (
            load_prediction_cumulative(trades_plot_base, slug, slug_dir, freq, time_col, closing_date)
            if closing_date is not None
            else pd.Series(dtype=float)
        )
        pred_ncum = load_prediction_non_cumulative(slug_dir, slug, freq, time_col)

        don_cum_vals = don_cum.set_index(time_col).reindex(periods)["Dem_Ratio"]
        don_ncum_vals = don_ncum.set_index(time_col).reindex(periods)["Dem_Ratio"] if not don_ncum.empty else pd.Series(index=periods, dtype=float)
        pred_cum_vals = pred_cum.reindex(periods).ffill() if not pred_cum.empty else pd.Series(index=periods, dtype=float)
        pred_ncum_vals = pred_ncum.reindex(periods) if not pred_ncum.empty else pd.Series(index=periods, dtype=float)

        for p in periods:
            rows.append({
                "election_name": slug,
                "week": p,
                "winning_side_dem": winning_side_dem,
                "cumulative_prediction_odds": pred_cum_vals.get(p, float("nan")),
                "non_cumulative_prediction_odds": pred_ncum_vals.get(p, float("nan")),
                "cumulative_donation_odds": don_cum_vals.get(p, float("nan")),
                "non_cumulative_donation_odds": don_ncum_vals.get(p, float("nan")),
            })

    if not rows:
        df = pd.DataFrame(columns=[
            "election_name", "week", "winning_side_dem",
            "cumulative_prediction_odds", "non_cumulative_prediction_odds",
            "cumulative_donation_odds", "non_cumulative_donation_odds",
        ])
    else:
        df = pd.DataFrame(rows)
    out_path = output_dir / "summary_odds_weekly.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


def build_segment_odds_weekly(
    slugs: list[str],
    per_market_base: Path,
    output_dir: Path,
) -> Path:
    """
    Build summary_segment_odds_weekly.csv: (election_name, week) +
    cumulative_donation_odds_small/medium/large, non_cumulative_donation_odds_small/medium/large.
    """
    freq = "weekly"
    time_col = TIME_COLS[freq]
    segments = ["Small", "Medium", "Large"]
    rows = []

    for slug in slugs:
        slug_dir = per_market_base / slug
        if not slug_dir.is_dir():
            continue

        don_cum_all = load_donation_cumulative(slug_dir, freq)
        if don_cum_all.empty:
            continue
        periods = don_cum_all[time_col].dropna().tolist()

        cum_seg = _load_donation_cumulative_by_segment(slug_dir, freq)
        ncum_seg = _load_donation_non_cumulative_by_segment(slug_dir, freq)

        for p in periods:
            row = {"election_name": slug, "week": p}
            for seg in segments:
                c = cum_seg[(cum_seg[time_col] == p) & (cum_seg["Segment"] == seg)] if not cum_seg.empty else pd.DataFrame()
                row[f"cumulative_donation_odds_{seg.lower()}"] = c["Dem_Ratio"].iloc[0] if len(c) else float("nan")
                n = ncum_seg[(ncum_seg[time_col] == p) & (ncum_seg["Segment"] == seg)] if not ncum_seg.empty else pd.DataFrame()
                row[f"non_cumulative_donation_odds_{seg.lower()}"] = n["Dem_Ratio"].iloc[0] if len(n) else float("nan")
            rows.append(row)

    if not rows:
        df = pd.DataFrame(columns=[
            "election_name", "week",
            "cumulative_donation_odds_small", "cumulative_donation_odds_medium", "cumulative_donation_odds_large",
            "non_cumulative_donation_odds_small", "non_cumulative_donation_odds_medium", "non_cumulative_donation_odds_large",
        ])
    else:
        df = pd.DataFrame(rows)
    out_path = output_dir / "summary_segment_odds_weekly.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


def main() -> None:
    """Load slugs and build both CSVs into Summary_analysis/output/."""
    json_path = PARENT / "event_slugs.json"
    slugs = []
    if json_path.exists():
        try:
            with open(json_path) as f:
                data = json.load(f)
            for item in data:
                if isinstance(item, str) and item.strip():
                    slugs.append(item.strip())
                elif isinstance(item, dict):
                    s = (item.get("slug") or item.get("event_slug") or "").strip()
                    if s:
                        slugs.append(s)
        except Exception:
            pass
    if not slugs:
        txt_path = PARENT / "event_slugs.txt"
        if txt_path.exists():
            with open(txt_path) as f:
                slugs = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not slugs:
        print("No event slugs found.")
        return

    per_market_base = PARENT
    trades_plot_base = PARENT / "trades_Plot"
    output_dir = SCRIPT_DIR / "output"

    p1 = build_summary_odds_weekly(slugs, per_market_base, trades_plot_base, output_dir)
    print(f"  ✓ {p1.name} -> {p1}")
    p2 = build_segment_odds_weekly(slugs, per_market_base, output_dir)
    print(f"  ✓ {p2.name} -> {p2}")


if __name__ == "__main__":
    main()
