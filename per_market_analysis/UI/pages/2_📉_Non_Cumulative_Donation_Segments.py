"""Page 3: Non-Cumulative Segments visualization."""

import sys
from pathlib import Path

import streamlit as st

# Add UI directory to path for imports
UI_DIR = Path(__file__).resolve().parent.parent
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

from components.info_panels import show_calculation_panel, show_data_source_panel, show_interpretation_guide
from utils.constants import SEGMENTS
from utils.data_loader import (
    get_available_frequencies,
    get_available_segments,
    get_base_path,
    load_event_slugs,
)
from utils.plot_generators import plot_non_cumulative_segments

st.set_page_config(page_title="Non-Cumulative Donation Segments", page_icon="📉", layout="wide")

st.title("📉 Non-Cumulative Donation Segments")
st.markdown("Period-specific donation ratios (no carry-forward) broken down by donor segment.")

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
available_freqs = get_available_frequencies(slug_dir, cumulative=False)
if not available_freqs:
    st.warning(f"No non-cumulative aggregation data found for {selected_slug}.")
    st.stop()

selected_frequency = st.sidebar.selectbox("Frequency", available_freqs)

# Segment selector
available_segs = get_available_segments(slug_dir, selected_frequency, cumulative=False)
if not available_segs:
    st.warning(f"No segment data found for {selected_slug}.")
    st.stop()

selected_segments = st.sidebar.multiselect(
    "Select Segments",
    available_segs,
    default=available_segs if len(available_segs) <= 4 else available_segs[:4],
)

if not selected_segments:
    st.warning("Please select at least one segment.")
    st.stop()

# Polymarket overlay
include_polymarket = st.sidebar.checkbox("Include Polymarket overlay", value=True)

# Smoothing
smoothing_window = st.sidebar.slider("Smoothing window", min_value=1, max_value=7, value=1, step=1,
                                     help="Moving average window size. 1 = no smoothing, higher values = smoother lines.")

# Info panels
show_interpretation_guide()

# Generate plot
try:
    fig = plot_non_cumulative_segments(
        slug_dir,
        selected_frequency,
        selected_segments,
        include_polymarket=include_polymarket,
        smoothing_window=smoothing_window,
    )
    
    if fig.data:
        st.plotly_chart(fig, use_container_width=True)
        
        # Show calculation panel
        show_calculation_panel("non_cumulative_segments", selected_slug, selected_frequency)
        
        # Show data sources
        show_data_source_panel([
            f"{selected_slug}/non_cumulative_donations/output/{selected_frequency}_non_cumulative_aggregations.csv",
            f"{selected_slug}/polymarket_prices.csv" if include_polymarket else None,
        ])
    else:
        st.warning("No data available for this event and frequency combination.")
except Exception as e:
    st.error(f"Error generating plot: {e}")
    st.exception(e)
