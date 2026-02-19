"""Data loading utilities for the Streamlit UI."""

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from .constants import TIME_COLS


def get_base_path() -> Path:
    """Get the per_market_analysis base directory."""
    return Path(__file__).resolve().parent.parent.parent


@st.cache_data
def load_event_slugs() -> list[str]:
    """Load event slugs from event_slugs.json or event_slugs.txt."""
    base = get_base_path()
    json_path = base / "event_slugs.json"
    txt_path = base / "event_slugs.txt"
    
    slugs = []
    if json_path.exists():
        try:
            with open(json_path) as f:
                data = json.load(f)
            for item in data:
                if isinstance(item, str) and item.strip():
                    slugs.append(item.strip())
                elif isinstance(item, dict):
                    slug = item.get("slug") or item.get("event_slug")
                    if isinstance(slug, str) and slug.strip():
                        slugs.append(slug.strip())
        except Exception:
            pass
    
    if not slugs and txt_path.exists():
        try:
            with open(txt_path) as f:
                slugs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except Exception:
            pass
    
    return slugs


@st.cache_data
def load_cumulative_aggregations(slug_dir: Path, frequency: str, segment: str = None) -> pd.DataFrame:
    """Load cumulative aggregations CSV. If segment specified, filter to that segment."""
    time_col = TIME_COLS[frequency]
    path = slug_dir / "output" / f"{frequency}_cumulative_aggregations.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        if segment:
            df = df[df["Segment"] == segment].copy()
        if df.empty:
            return pd.DataFrame()
        return df[[time_col, "Dem_Ratio"]].dropna() if time_col in df.columns else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data
def load_all_cumulative_segments(slug_dir: Path, frequency: str) -> pd.DataFrame:
    """Load all segments from cumulative aggregations CSV."""
    path = slug_dir / "output" / f"{frequency}_cumulative_aggregations.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


@st.cache_data
def load_non_cumulative_aggregations(slug_dir: Path, frequency: str, segment: str = None) -> pd.DataFrame:
    """Load non-cumulative aggregations CSV. If segment specified, filter to that segment."""
    time_col = TIME_COLS[frequency]
    path = slug_dir / "non_cumulative_donations" / "output" / f"{frequency}_non_cumulative_aggregations.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        if segment:
            df = df[df["Segment"] == segment].copy()
        if df.empty:
            return pd.DataFrame()
        return df[[time_col, "Dem_Ratio"]].dropna() if time_col in df.columns else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data
def load_all_non_cumulative_segments(slug_dir: Path, frequency: str) -> pd.DataFrame:
    """Load all segments from non-cumulative aggregations CSV."""
    path = slug_dir / "non_cumulative_donations" / "output" / f"{frequency}_non_cumulative_aggregations.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


@st.cache_data
def load_polymarket_prices(slug_dir: Path) -> pd.DataFrame:
    """Load polymarket_prices.csv."""
    path = slug_dir / "polymarket_prices.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def aggregate_prices_to_period(prices_df: pd.DataFrame, period_col: str) -> pd.DataFrame:
    """Aggregate polymarket prices by period (same logic as plot_donation_and_polymarket)."""
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


def get_available_segments(slug_dir: Path, frequency: str, cumulative: bool = True) -> list[str]:
    """Get list of available segments for a given frequency."""
    if cumulative:
        df = load_all_cumulative_segments(slug_dir, frequency)
    else:
        df = load_all_non_cumulative_segments(slug_dir, frequency)
    if df.empty or "Segment" not in df.columns:
        return []
    return sorted(df["Segment"].unique().tolist())


def get_available_frequencies(slug_dir: Path, cumulative: bool = True) -> list[str]:
    """Get list of available frequencies for a slug."""
    available = []
    for freq in ["daily", "weekly", "monthly"]:
        if cumulative:
            path = slug_dir / "output" / f"{freq}_cumulative_aggregations.csv"
        else:
            path = slug_dir / "non_cumulative_donations" / "output" / f"{freq}_non_cumulative_aggregations.csv"
        if path.exists():
            available.append(freq)
    return available


def get_polymarket_outcomes(slug_dir: Path) -> list[str]:
    """Get list of available Polymarket outcome labels (excluding 'No')."""
    prices_df = load_polymarket_prices(slug_dir)
    if prices_df.empty or "outcome_label" not in prices_df.columns:
        return []
    outcomes = prices_df["outcome_label"].unique().tolist()
    return [o for o in outcomes if (o or "").strip().lower() != "no"]


def get_democrat_outcome_column(pm_agg: pd.DataFrame, slug: str) -> str | None:
    """Return the column name in pm_agg that corresponds to Democrat."""
    base = get_base_path()
    non_no = [c for c in pm_agg.columns if (c or "").strip().lower() != "no"]
    if not non_no:
        return None
    # 1) Prefer column literally "Democrat" (case-insensitive)
    for c in non_no:
        if (c or "").strip().lower() == "democrat":
            return c
    # 2) Prefer column matching Democrat candidate from event_slugs.json
    json_path = base / "event_slugs.json"
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
    return non_no[0] if non_no else None


def get_polymarket_date_range(slug_dir: Path) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Get earliest and closing date from polymarket data."""
    prices_file = slug_dir / "polymarket_prices.csv"
    metadata_file = slug_dir / "polymarket_metadata.json"
    
    earliest_date = None
    closing_date = None
    
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                data = json.load(f)
            if "endDate" in data:
                closing_date = pd.to_datetime(data["endDate"]).normalize()
                if closing_date.tz is not None:
                    closing_date = closing_date.tz_localize(None)
            if "markets" in data:
                for m in data["markets"]:
                    if "endDate" in m:
                        cd = pd.to_datetime(m["endDate"]).normalize()
                        if cd.tz is not None:
                            cd = cd.tz_localize(None)
                        if closing_date is None or cd < closing_date:
                            closing_date = cd
        except Exception:
            pass
    
    if prices_file.exists():
        try:
            p = pd.read_csv(prices_file)
            if not p.empty and "timestamp" in p.columns:
                dates = pd.to_datetime(p["timestamp"], unit="s")
                if earliest_date is None:
                    earliest_date = dates.min()
                elif dates.min() < earliest_date:
                    earliest_date = dates.min()
                if closing_date is None:
                    closing_date = dates.max()
                elif dates.max() > closing_date:
                    closing_date = dates.max()
        except Exception:
            pass
    
    if earliest_date is not None:
        earliest_date = pd.Timestamp(year=earliest_date.year, month=earliest_date.month, day=earliest_date.day)
    if closing_date is not None:
        closing_date = pd.Timestamp(year=closing_date.year, month=closing_date.month, day=closing_date.day)
    
    return earliest_date, closing_date


def _date_to_period(date_val, time_col: str) -> str:
    """Convert a date to period string."""
    if hasattr(date_val, "strftime"):
        d = date_val
    else:
        d = pd.Timestamp(date_val)
    if time_col == "Year_Date":
        return d.strftime("%Y-%m-%d")
    if time_col == "Year_Week":
        y, w, _ = d.isocalendar()
        return f"{y}-W{w:02d}"
    return str(pd.Timestamp(d).to_period("M"))


@st.cache_data
def load_prediction_cumulative(trades_plot_base: Path, slug: str, slug_dir: Path, freq: str, time_col: str, closing_date) -> pd.Series:
    """Load prediction cumulative (all_users) from trades_Plot."""
    event_dir = trades_plot_base / slug
    if not event_dir.exists():
        return pd.Series(dtype=float)
    candidates = sorted(event_dir.glob("*_all_users_segment.csv"))
    if not candidates:
        return pd.Series(dtype=float)
    path = candidates[0]
    try:
        df = pd.read_csv(path)
        df = df[df["segment"] == "all_users"].copy()
        if df.empty or "day_offset" not in df.columns or "odds" not in df.columns:
            return pd.Series(dtype=float)
        if closing_date is None:
            return pd.Series(dtype=float)
        if hasattr(closing_date, "date"):
            close_d = closing_date.date()
        else:
            close_d = pd.Timestamp(closing_date).date()
        df["date"] = df["day_offset"].apply(lambda x: close_d + timedelta(days=int(x)))
        df["period"] = df["date"].apply(lambda d: _date_to_period(d, time_col))
        by_period = df.sort_values("day_offset").groupby("period")["odds"].last().reset_index()
        return by_period.set_index("period")["odds"]
    except Exception:
        return pd.Series(dtype=float)


def get_trades_markets(slug_dir: Path, trades_plot_base: Path) -> list[str]:
    """Get list of available market IDs for trades data."""
    event_dir = trades_plot_base / slug_dir.name
    if not event_dir.exists():
        return []
    markets = []
    for f in event_dir.glob("*_all_users_segment.csv"):
        market_id = f.stem.replace("_all_users_segment", "")
        if market_id not in markets:
            markets.append(market_id)
    return sorted(markets)


@st.cache_data
def load_trades_data(slug_dir: Path, trades_plot_base: Path, market_id: str, segment: str = "all_users") -> pd.DataFrame:
    """Load trades data for a specific market and segment."""
    event_dir = trades_plot_base / slug_dir.name
    path = event_dir / f"{market_id}_{segment}_segment.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


@st.cache_data
def load_price_based_odds(slug_dir: Path, closing_date) -> pd.DataFrame:
    """Load price-based odds from polymarket_prices.csv."""
    prices_df = load_polymarket_prices(slug_dir)
    if prices_df.empty or closing_date is None:
        return pd.DataFrame()
    try:
        df = prices_df.copy()
        df["date"] = pd.to_datetime(df["timestamp"], unit="s").dt.date
        close_d = closing_date.date() if hasattr(closing_date, "date") else pd.Timestamp(closing_date).date()
        df["day_offset"] = (df["date"] - close_d).apply(lambda x: x.days)
        df = df[df["day_offset"] <= 0].copy()  # Only historical prices
        # Get last price per day
        df = df.sort_values("timestamp").groupby(["day_offset", "outcome_label"])["price"].last().reset_index()
        # Filter for YES outcomes (assuming first outcome is YES)
        yes_outcomes = df[df["outcome_label"] != "No"]["outcome_label"].unique()
        if len(yes_outcomes) > 0:
            df = df[df["outcome_label"] == yes_outcomes[0]].copy()
            return df[["day_offset", "price"]].rename(columns={"price": "price_odds"})
    except Exception:
        pass
    return pd.DataFrame()
