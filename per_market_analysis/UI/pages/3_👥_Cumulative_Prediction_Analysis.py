"""Page 5: User Analysis - Trade-based odds comparison."""

import sys
from pathlib import Path

import streamlit as st

# Add UI directory to path for imports
UI_DIR = Path(__file__).resolve().parent.parent
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

from components.info_panels import show_calculation_panel, show_data_source_panel, show_interpretation_guide
from utils.constants import USER_SEGMENTS
from utils.data_loader import (
    get_base_path,
    get_trades_markets,
    load_event_slugs,
)
from utils.plot_generators import plot_user_analysis_odds

st.set_page_config(page_title="Cumulative Prediction Analysis", page_icon="👥", layout="wide")

st.title("👥 Cumulative Prediction Analysis")
st.markdown("Investment-weighted cumulative prediction odds from blockchain trades, compared to Polymarket price-based odds.")

# Sidebar controls
st.sidebar.header("Controls")

base = get_base_path()
slugs = load_event_slugs()

if not slugs:
    st.error("No event slugs found. Please ensure `event_slugs.json` exists in `per_market_analysis/`.")
    st.stop()

selected_slug = st.sidebar.selectbox("Select Event", slugs)
slug_dir = base / selected_slug

if not slug_dir.exists():
    st.error(f"Event directory not found: {slug_dir}")
    st.stop()

# Trades plot base
trades_plot_base = base / "trades_Plot"

# Market selector
markets = get_trades_markets(slug_dir, trades_plot_base)
if not markets:
    st.warning(f"No trades data found for {selected_slug}. Ensure `trades_Plot/{selected_slug}/` exists with market segment CSVs.")
    st.stop()

selected_market = st.sidebar.selectbox("Select Market", markets)

# Comparison mode
comparison_mode = st.sidebar.radio(
    "Comparison Mode",
    ["all_segments", "price_vs_segment"],
    format_func=lambda x: "All segments together" if x == "all_segments" else "Price vs selected segment",
)

# Segment selector
if comparison_mode == "all_segments":
    available_segments = USER_SEGMENTS
    selected_segments = st.sidebar.multiselect(
        "Select Segments",
        available_segments,
        default=available_segments,
    )
else:
    available_segments = USER_SEGMENTS
    selected_segments = st.sidebar.multiselect(
        "Select Segment (for comparison with Price)",
        available_segments,
        default=["all_users"] if "all_users" in available_segments else [available_segments[0]] if available_segments else [],
        max_selections=1,
    )

if not selected_segments:
    st.warning("Please select at least one segment.")
    st.stop()

# Smoothing
smoothing_window = st.sidebar.slider("Smoothing window", min_value=1, max_value=7, value=1, step=1,
                                     help="Moving average window size. 1 = no smoothing, higher values = smoother lines.")

# Info panels
show_interpretation_guide()

# Generate plot
try:
    fig = plot_user_analysis_odds(
        slug_dir,
        trades_plot_base,
        selected_market,
        selected_segments,
        comparison_mode=comparison_mode,
        smoothing_window=smoothing_window,
    )
    
    if fig.data:
        st.plotly_chart(fig, use_container_width=True)
        
        # Show calculation panel
        show_calculation_panel("user_analysis", selected_slug)
        
        # Show data sources
        data_sources = [
            f"trades_Plot/{selected_slug}/{selected_market}_*_segment.csv",
            f"{selected_slug}/polymarket_prices.csv",
        ]
        show_data_source_panel(data_sources)
    else:
        st.warning("No data available for this market and segment combination.")
except Exception as e:
    st.error(f"Error generating plot: {e}")
    st.exception(e)
