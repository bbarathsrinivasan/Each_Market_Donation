"""Page 4: Summary Analysis - 4-line combined plot."""

import sys
from pathlib import Path

import streamlit as st

# Add UI directory to path for imports
UI_DIR = Path(__file__).resolve().parent.parent
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

from components.info_panels import show_calculation_panel, show_data_source_panel, show_interpretation_guide
from utils.data_loader import (
    get_available_frequencies,
    get_base_path,
    load_event_slugs,
)
from utils.plot_generators import plot_summary_4line

st.set_page_config(page_title="Summary Analysis", page_icon="🔀", layout="wide")

st.title("🔀 Summary Analysis - Donation & Prediction")
st.markdown("Combined view of all four signals: donation-based and prediction-market-based (cumulative and non-cumulative).")

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

# Frequency selector
available_freqs = get_available_frequencies(slug_dir, cumulative=True)
if not available_freqs:
    st.warning(f"No cumulative aggregation data found for {selected_slug}.")
    st.stop()

selected_frequency = st.sidebar.selectbox("Frequency", available_freqs)

# Line toggles
st.sidebar.subheader("Show/Hide Lines")
show_lines = {
    "donation_cumulative": st.sidebar.checkbox("Donation cumulative (All)", value=True),
    "prediction_cumulative": st.sidebar.checkbox("Prediction cumulative (all users)", value=True),
    "donation_non_cumulative": st.sidebar.checkbox("Donation non-cumulative (All)", value=True),
    "prediction_non_cumulative": st.sidebar.checkbox("Prediction non-cumulative (Polymarket)", value=True),
}

if not any(show_lines.values()):
    st.warning("Please select at least one line to display.")
    st.stop()

# Smoothing
smoothing_window = st.sidebar.slider("Smoothing window", min_value=1, max_value=7, value=1, step=1,
                                     help="Moving average window size. 1 = no smoothing, higher values = smoother lines.")

# Trades plot base
trades_plot_base = base / "trades_Plot"

# Info panels
show_interpretation_guide()

# Generate plot
try:
    fig = plot_summary_4line(
        slug_dir,
        selected_frequency,
        trades_plot_base,
        show_lines=show_lines,
        smoothing_window=smoothing_window,
    )
    
    if fig.data:
        st.plotly_chart(fig, use_container_width=True)
        
        # Show calculation panel
        show_calculation_panel("summary", selected_slug, selected_frequency)
        
        # Show data sources
        data_sources = [
            f"{selected_slug}/output/{selected_frequency}_cumulative_aggregations.csv",
            f"{selected_slug}/non_cumulative_donations/output/{selected_frequency}_non_cumulative_aggregations.csv",
            f"{selected_slug}/polymarket_prices.csv",
        ]
        if trades_plot_base.exists():
            data_sources.append(f"trades_Plot/{selected_slug}/*_all_users_segment.csv")
        show_data_source_panel(data_sources)
    else:
        st.warning("No data available for this event and frequency combination.")
except Exception as e:
    st.error(f"Error generating plot: {e}")
    st.exception(e)
