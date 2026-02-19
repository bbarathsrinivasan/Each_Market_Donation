"""Plot generation utilities using Plotly for interactive charts."""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .constants import (
    DONATION_COLOR,
    LINE_COLORS,
    POLYMARKET_COLORS,
    SEGMENT_COLORS,
    TIME_COLS,
)
from .data_loader import (
    aggregate_prices_to_period,
    get_democrat_outcome_column,
    get_polymarket_date_range,
    load_all_cumulative_segments,
    load_all_non_cumulative_segments,
    load_cumulative_aggregations,
    load_non_cumulative_aggregations,
    load_polymarket_prices,
    load_prediction_cumulative,
    load_price_based_odds,
    load_trades_data,
)


def smooth_series(values: list[float], window: int = 3) -> list[float]:
    """Apply moving average smoothing to a series. Handles None/NaN values."""
    if window <= 1 or not values:
        return values
    smoothed = []
    n = len(values)
    for i in range(n):
        start = max(0, i - window // 2)
        end = min(n, i + window // 2 + 1)
        window_vals = [v for v in values[start:end] if v is not None and not (isinstance(v, float) and np.isnan(v))]
        if window_vals:
            smoothed.append(sum(window_vals) / len(window_vals))
        else:
            smoothed.append(values[i] if i < len(values) else None)
    return smoothed


def plot_basic_donation_polymarket(
    slug_dir: Path,
    frequency: str,
    show_polymarket: bool = True,
    selected_outcomes: list[str] = None,
) -> go.Figure:
    """Generate basic donation + Polymarket plot."""
    time_col = TIME_COLS[frequency]
    
    # Load donation data
    don_df = load_all_cumulative_segments(slug_dir, frequency)
    if don_df.empty:
        return go.Figure()
    
    all_data = don_df[don_df["Segment"] == "All"].copy()
    if all_data.empty:
        return go.Figure()
    
    periods = all_data[time_col].dropna().tolist()
    don_ratios = all_data.set_index(time_col).reindex(periods)["Dem_Ratio"].tolist()
    
    fig = go.Figure()
    
    # Donation line
    fig.add_trace(go.Scatter(
        x=periods,
        y=don_ratios,
        mode="lines+markers",
        name="Donation Dem/(Dem+Rep)",
        line=dict(color=DONATION_COLOR, width=2),
        marker=dict(size=4),
        hovertemplate="<b>%{x}</b><br>Ratio: %{y:.3f}<extra></extra>",
    ))
    
    # 0.5 reference line
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="0.5")
    
    # Polymarket lines
    if show_polymarket:
        prices_df = load_polymarket_prices(slug_dir)
        if not prices_df.empty:
            pm_agg = aggregate_prices_to_period(prices_df, time_col)
            if not pm_agg.empty:
                outcomes_to_plot = [c for c in pm_agg.columns if c != "No"]
                if selected_outcomes:
                    outcomes_to_plot = [o for o in outcomes_to_plot if o in selected_outcomes]
                
                for i, outcome in enumerate(outcomes_to_plot):
                    color = POLYMARKET_COLORS[i % len(POLYMARKET_COLORS)]
                    series = []
                    for p in periods:
                        if p in pm_agg.index:
                            series.append(pm_agg.loc[p, outcome])
                        else:
                            series.append(None)
                    
                    fig.add_trace(go.Scatter(
                        x=periods,
                        y=series,
                        mode="lines+markers",
                        name=f"Polymarket: {outcome}",
                        line=dict(color=color, width=1.5, dash="dash"),
                        marker=dict(size=3, symbol="square"),
                        hovertemplate="<b>%{x}</b><br>Price: %{y:.3f}<extra></extra>",
                    ))
    
    fig.update_layout(
        title=f"{slug_dir.name} — Donation cumulative ratio + Polymarket ({frequency})",
        xaxis_title=f"{frequency.capitalize()} Period",
        yaxis_title="Ratio / Price (0-1)",
        yaxis=dict(range=[0, 1]),
        hovermode="x unified",
        height=500,
        showlegend=True,
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=45)
    
    return fig


def plot_cumulative_segments(
    slug_dir: Path,
    frequency: str,
    segments: list[str],
    include_polymarket: bool = True,
    smoothing_window: int = 1,
) -> go.Figure:
    """Generate cumulative segment comparison plot."""
    time_col = TIME_COLS[frequency]
    
    df = load_all_cumulative_segments(slug_dir, frequency)
    if df.empty:
        return go.Figure()
    
    all_data = df[df["Segment"] == "All"]
    if all_data.empty:
        return go.Figure()
    
    periods = all_data[time_col].dropna().tolist()
    
    fig = go.Figure()
    
    # Segment lines
    for seg in segments:
        if seg not in df["Segment"].values:
            continue
        seg_data = df[df["Segment"] == seg]
        ratios = seg_data.set_index(time_col).reindex(periods)["Dem_Ratio"].tolist()
        if smoothing_window > 1:
            ratios = smooth_series(ratios, smoothing_window)
        color = SEGMENT_COLORS.get(seg, DONATION_COLOR)
        
        fig.add_trace(go.Scatter(
            x=periods,
            y=ratios,
            mode="lines+markers",
            name=seg,
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>{seg}</b><br>%{{x}}<br>Ratio: %{{y:.3f}}<extra></extra>",
        ))
    
    # Polymarket overlay
    if include_polymarket:
        prices_df = load_polymarket_prices(slug_dir)
        if not prices_df.empty:
            pm_agg = aggregate_prices_to_period(prices_df, time_col)
            if not pm_agg.empty:
                outcomes_to_plot = [c for c in pm_agg.columns if c != "No"]
                for i, outcome in enumerate(outcomes_to_plot):
                    color = POLYMARKET_COLORS[i % len(POLYMARKET_COLORS)]
                    series = []
                    for p in periods:
                        if p in pm_agg.index:
                            series.append(pm_agg.loc[p, outcome])
                        else:
                            series.append(None)
                    if smoothing_window > 1:
                        series = smooth_series(series, smoothing_window)
                    
                    fig.add_trace(go.Scatter(
                        x=periods,
                        y=series,
                        mode="lines+markers",
                        name=f"Polymarket: {outcome}",
                        line=dict(color=color, width=1.5, dash="dash"),
                        marker=dict(size=3, symbol="square"),
                        hovertemplate=f"<b>Polymarket: {outcome}</b><br>%{{x}}<br>Price: %{{y:.3f}}<extra></extra>",
                    ))
    
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="0.5")
    
    fig.update_layout(
        title=f"{slug_dir.name} — Donation cumulative ratio (all segments) + Polymarket ({frequency})",
        xaxis_title=f"{frequency.capitalize()} Period",
        yaxis_title="Ratio / Price (0-1)",
        yaxis=dict(range=[0, 1]),
        hovermode="x unified",
        height=500,
        showlegend=True,
    )
    
    fig.update_xaxes(tickangle=45)
    
    return fig


def plot_non_cumulative_segments(
    slug_dir: Path,
    frequency: str,
    segments: list[str],
    include_polymarket: bool = True,
    smoothing_window: int = 1,
) -> go.Figure:
    """Generate non-cumulative segment comparison plot."""
    time_col = TIME_COLS[frequency]
    
    df = load_all_non_cumulative_segments(slug_dir, frequency)
    if df.empty:
        return go.Figure()
    
    all_data = df[df["Segment"] == "All"]
    if all_data.empty:
        return go.Figure()
    
    periods = all_data[time_col].dropna().tolist()
    
    fig = go.Figure()
    
    # Segment lines
    for seg in segments:
        if seg not in df["Segment"].values:
            continue
        seg_data = df[df["Segment"] == seg]
        ratios = seg_data.set_index(time_col).reindex(periods)["Dem_Ratio"].tolist()
        if smoothing_window > 1:
            ratios = smooth_series(ratios, smoothing_window)
        color = SEGMENT_COLORS.get(seg, DONATION_COLOR)
        
        fig.add_trace(go.Scatter(
            x=periods,
            y=ratios,
            mode="lines+markers",
            name=seg,
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>{seg}</b><br>%{{x}}<br>Ratio: %{{y:.3f}}<extra></extra>",
        ))
    
    # Polymarket overlay
    if include_polymarket:
        prices_df = load_polymarket_prices(slug_dir)
        if not prices_df.empty:
            pm_agg = aggregate_prices_to_period(prices_df, time_col)
            if not pm_agg.empty:
                outcomes_to_plot = [c for c in pm_agg.columns if c != "No"]
                for i, outcome in enumerate(outcomes_to_plot):
                    color = POLYMARKET_COLORS[i % len(POLYMARKET_COLORS)]
                    series = []
                    for p in periods:
                        if p in pm_agg.index:
                            series.append(pm_agg.loc[p, outcome])
                        else:
                            series.append(None)
                    if smoothing_window > 1:
                        series = smooth_series(series, smoothing_window)
                    
                    fig.add_trace(go.Scatter(
                        x=periods,
                        y=series,
                        mode="lines+markers",
                        name=f"Polymarket: {outcome}",
                        line=dict(color=color, width=1.5, dash="dash"),
                        marker=dict(size=3, symbol="square"),
                        hovertemplate=f"<b>Polymarket: {outcome}</b><br>%{{x}}<br>Price: %{{y:.3f}}<extra></extra>",
                    ))
    
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="0.5")
    
    fig.update_layout(
        title=f"{slug_dir.name} — Donation period ratio (all segments) + Polymarket ({frequency})",
        xaxis_title=f"{frequency.capitalize()} Period",
        yaxis_title="Ratio / Price (0-1)",
        yaxis=dict(range=[0, 1]),
        hovermode="x unified",
        height=500,
        showlegend=True,
    )
    
    fig.update_xaxes(tickangle=45)
    
    return fig


def plot_summary_4line(
    slug_dir: Path,
    frequency: str,
    trades_plot_base: Path,
    show_lines: dict[str, bool] = None,
    smoothing_window: int = 1,
) -> go.Figure:
    """Generate 4-line summary plot."""
    time_col = TIME_COLS[frequency]
    
    if show_lines is None:
        show_lines = {
            "donation_cumulative": True,
            "prediction_cumulative": True,
            "donation_non_cumulative": True,
            "prediction_non_cumulative": True,
        }
    
    # Load donation cumulative (defines x-axis)
    don_cum = load_cumulative_aggregations(slug_dir, frequency, "All")
    if don_cum.empty:
        return go.Figure()
    
    periods = don_cum[time_col].dropna().tolist()
    n = len(periods)
    
    # Load other series
    don_ncum = load_non_cumulative_aggregations(slug_dir, frequency, "All")
    
    _, closing_date = get_polymarket_date_range(slug_dir)
    if closing_date is None:
        prices_file = slug_dir / "polymarket_prices.csv"
        if prices_file.exists():
            try:
                p = pd.read_csv(prices_file)
                if not p.empty and "timestamp" in p.columns:
                    closing_date = pd.to_datetime(p["timestamp"], unit="s").max()
                    closing_date = pd.Timestamp(year=closing_date.year, month=closing_date.month, day=closing_date.day)
            except Exception:
                pass
    
    pred_cum = pd.Series(dtype=float)
    if closing_date is not None:
        pred_cum = load_prediction_cumulative(trades_plot_base, slug_dir.name, slug_dir, frequency, time_col, closing_date)
    
    # Prediction non-cumulative
    prices_df = load_polymarket_prices(slug_dir)
    pred_ncum_series = pd.Series(dtype=float)
    if not prices_df.empty:
        pm_agg = aggregate_prices_to_period(prices_df, time_col)
        if not pm_agg.empty:
            dem_col = get_democrat_outcome_column(pm_agg, slug_dir.name)
            if dem_col:
                pred_ncum_series = pm_agg[dem_col]
    
    # Align all to periods
    don_cum_vals = don_cum.set_index(time_col).reindex(periods)["Dem_Ratio"].tolist()
    don_ncum_vals = don_ncum.set_index(time_col).reindex(periods)["Dem_Ratio"].tolist() if not don_ncum.empty else [None] * n
    pred_cum_vals = pred_cum.reindex(periods).ffill().tolist() if not pred_cum.empty else [None] * n
    pred_ncum_vals = pred_ncum_series.reindex(periods).tolist() if not pred_ncum_series.empty else [None] * n
    
    # Apply smoothing if requested
    if smoothing_window > 1:
        don_cum_vals = smooth_series(don_cum_vals, smoothing_window)
        don_ncum_vals = smooth_series(don_ncum_vals, smoothing_window)
        pred_cum_vals = smooth_series(pred_cum_vals, smoothing_window)
        pred_ncum_vals = smooth_series(pred_ncum_vals, smoothing_window)
    
    fig = go.Figure()
    
    if show_lines.get("donation_cumulative", True):
        fig.add_trace(go.Scatter(
            x=periods,
            y=don_cum_vals,
            mode="lines+markers",
            name="Donation cumulative (All)",
            line=dict(color=LINE_COLORS["donation_cumulative"], width=2),
            marker=dict(size=4),
            hovertemplate="<b>Donation Cumulative</b><br>%{x}<br>Ratio: %{y:.3f}<extra></extra>",
        ))
    
    if show_lines.get("prediction_cumulative", True):
        fig.add_trace(go.Scatter(
            x=periods,
            y=pred_cum_vals,
            mode="lines+markers",
            name="Prediction cumulative (all users)",
            line=dict(color=LINE_COLORS["prediction_cumulative"], width=2),
            marker=dict(size=4, symbol="square"),
            hovertemplate="<b>Prediction Cumulative</b><br>%{x}<br>Odds: %{y:.3f}<extra></extra>",
        ))
    
    if show_lines.get("donation_non_cumulative", True):
        fig.add_trace(go.Scatter(
            x=periods,
            y=don_ncum_vals,
            mode="lines+markers",
            name="Donation non-cumulative (All)",
            line=dict(color=LINE_COLORS["donation_non_cumulative"], width=2),
            marker=dict(size=4, symbol="triangle-up"),
            hovertemplate="<b>Donation Non-Cumulative</b><br>%{x}<br>Ratio: %{y:.3f}<extra></extra>",
        ))
    
    if show_lines.get("prediction_non_cumulative", True):
        fig.add_trace(go.Scatter(
            x=periods,
            y=pred_ncum_vals,
            mode="lines+markers",
            name="Prediction non-cumulative (Polymarket)",
            line=dict(color=LINE_COLORS["prediction_non_cumulative"], width=2, dash="dash"),
            marker=dict(size=4, symbol="diamond"),
            hovertemplate="<b>Prediction Non-Cumulative</b><br>%{x}<br>Price: %{y:.3f}<extra></extra>",
        ))
    
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="0.5")
    
    fig.update_layout(
        title=f"{slug_dir.name} — Summary ({frequency}): Donation cum, Prediction cum, Donation non-cum, Prediction non-cum",
        xaxis_title=f"{frequency.capitalize()} Period",
        yaxis_title="Ratio / Odds (0-1)",
        yaxis=dict(range=[0, 1]),
        hovermode="x unified",
        height=500,
        showlegend=True,
    )
    
    fig.update_xaxes(tickangle=45)
    
    return fig


def plot_user_analysis_odds(
    slug_dir: Path,
    trades_plot_base: Path,
    market_id: str,
    segments: list[str],
    comparison_mode: str = "all_segments",
    smoothing_window: int = 1,
) -> go.Figure:
    """Generate user analysis trade odds plot."""
    _, closing_date = get_polymarket_date_range(slug_dir)
    if closing_date is None:
        return go.Figure()
    
    # Load price-based odds
    price_odds_df = load_price_based_odds(slug_dir, closing_date)
    
    fig = go.Figure()
    
    # Price odds line
    if not price_odds_df.empty:
        price_odds_vals = price_odds_df["price_odds"].tolist()
        price_offsets = price_odds_df["day_offset"].tolist()
        if smoothing_window > 1:
            price_odds_vals = smooth_series(price_odds_vals, smoothing_window)
        fig.add_trace(go.Scatter(
            x=price_offsets,
            y=price_odds_vals,
            mode="lines+markers",
            name="Price Odds",
            line=dict(color="#3F88C5", width=2),
            marker=dict(size=4),
            hovertemplate="<b>Price Odds</b><br>Day: %{x}<br>Odds: %{y:.3f}<extra></extra>",
        ))
    
    # Trade-based odds lines
    segment_colors_map = {
        "all_users": "#44AF69",
        "small": "#F4A261",
        "medium": "#E94F37",
        "large": "#9B59B6",
    }
    
    if comparison_mode == "all_segments":
        for seg in segments:
            trades_df = load_trades_data(slug_dir, trades_plot_base, market_id, seg)
            if not trades_df.empty and "day_offset" in trades_df.columns and "odds" in trades_df.columns:
                odds_vals = trades_df["odds"].tolist()
                offsets = trades_df["day_offset"].tolist()
                if smoothing_window > 1:
                    odds_vals = smooth_series(odds_vals, smoothing_window)
                color = segment_colors_map.get(seg, "#000000")
                fig.add_trace(go.Scatter(
                    x=offsets,
                    y=odds_vals,
                    mode="lines+markers",
                    name=seg.replace("_", " ").title(),
                    line=dict(color=color, width=2),
                    marker=dict(size=4),
                    hovertemplate=f"<b>{seg.replace('_', ' ').title()}</b><br>Day: %{{x}}<br>Odds: %{{y:.3f}}<extra></extra>",
                ))
    else:
        # Price vs selected segment
        if len(segments) > 0:
            seg = segments[0]
            trades_df = load_trades_data(slug_dir, trades_plot_base, market_id, seg)
            if not trades_df.empty and "day_offset" in trades_df.columns and "odds" in trades_df.columns:
                odds_vals = trades_df["odds"].tolist()
                offsets = trades_df["day_offset"].tolist()
                if smoothing_window > 1:
                    odds_vals = smooth_series(odds_vals, smoothing_window)
                color = segment_colors_map.get(seg, "#000000")
                fig.add_trace(go.Scatter(
                    x=offsets,
                    y=odds_vals,
                    mode="lines+markers",
                    name=seg.replace("_", " ").title(),
                    line=dict(color=color, width=2),
                    marker=dict(size=4),
                    hovertemplate=f"<b>{seg.replace('_', ' ').title()}</b><br>Day: %{{x}}<br>Odds: %{{y:.3f}}<extra></extra>",
                ))
    
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="0.5")
    
    fig.update_layout(
        title=f"{slug_dir.name} — Trade Odds Comparison ({market_id})",
        xaxis_title="Day Offset (0 = closing day, negative = days before closing)",
        yaxis_title="Odds (0-1)",
        yaxis=dict(range=[0, 1]),
        hovermode="x unified",
        height=500,
        showlegend=True,
    )
    
    return fig
