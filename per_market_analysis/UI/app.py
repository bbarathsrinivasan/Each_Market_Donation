"""Main Streamlit application for Per-Market Analysis visualizations."""

import streamlit as st
from pathlib import Path

from utils.data_loader import get_available_frequencies, get_base_path, load_event_slugs

st.set_page_config(
    page_title="Per-Market Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar
st.sidebar.title("📊 Per-Market Analysis")
st.sidebar.markdown("---")

# Load event slugs
base = get_base_path()
slugs = load_event_slugs()

if slugs:
    st.sidebar.markdown(f"**{len(slugs)} events** available")
    st.sidebar.markdown("---")
    
    # Quick event selector
    selected_slug = st.sidebar.selectbox("Quick Event Selector", [""] + slugs)
    if selected_slug:
        slug_dir = base / selected_slug
        if slug_dir.exists():
            st.sidebar.markdown("**Available frequencies:**")
            cum_freqs = get_available_frequencies(slug_dir, cumulative=True)
            ncum_freqs = get_available_frequencies(slug_dir, cumulative=False)
            if cum_freqs:
                st.sidebar.markdown(f"- Cumulative: {', '.join(cum_freqs)}")
            if ncum_freqs:
                st.sidebar.markdown(f"- Non-cumulative: {', '.join(ncum_freqs)}")
else:
    st.sidebar.warning("No events found. Check `event_slugs.json`.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Navigation")
st.sidebar.markdown("Use the pages menu above to explore different visualizations:")

# Main content
st.title("📊 Per-Market Analysis Dashboard")
st.markdown("""
Welcome to the interactive visualization dashboard for per-market donation and prediction market analysis.

This application provides interactive access to all visualization categories from the per_market_analysis pipeline.
""")

st.markdown("---")

# Category overview
st.header("📚 Visualization Categories")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Cumulative Donation Segments")
    st.markdown("""
    Cumulative donation ratios broken down by donor segment (Small/Medium/Large).
    - **Segments:** All, Small, Medium, Large
    - **Shows:** How donation sentiment differs across donor segments over time
    - **Frequency:** Daily, Weekly, Monthly
    """)
    
    st.subheader("📉 Non-Cumulative Donation Segments")
    st.markdown("""
    Period-specific donation ratios (no carry-forward) by segment.
    - **Shows:** Donation sentiment per period without cumulative effect
    - **Useful for:** Identifying periods with high/low Democratic support
    - **Frequency:** Daily, Weekly, Monthly
    """)

with col2:
    st.subheader("👥 Cumulative Prediction Analysis")
    st.markdown("""
    Investment-weighted cumulative prediction odds from blockchain trades.
    - **Compares:** Trade-based cumulative odds vs Polymarket price-based odds
    - **Segments:** By user's cumulative donation amount
    - **X-axis:** Day offset (0 = closing day)
    """)
    
    st.subheader("🔀 Summary Analysis - Donation & Prediction")
    st.markdown("""
    Combined view of all four signals on one chart:
    1. Donation cumulative (All)
    2. Prediction cumulative (all users from trades)
    3. Donation non-cumulative (All)
    4. Prediction non-cumulative (Polymarket)
    """)

st.markdown("---")

# Quick links
st.header("🚀 Quick Start")
st.markdown("""
1. **Select an event** from the sidebar dropdown
2. **Navigate to a visualization page** using the menu on the left
3. **Adjust controls** in the sidebar to customize the view
4. **Expand info panels** below each plot for detailed explanations

### Available Pages:
- **📈 Cumulative Donation Segments** - Segment breakdown with cumulative donation calculations
- **📉 Non-Cumulative Donation Segments** - Segment breakdown with period-specific donation calculations
- **👥 Cumulative Prediction Analysis** - Trade-based cumulative prediction odds comparison
- **🔀 Summary Analysis** - All four signals (donation & prediction) combined
""")

st.markdown("---")

# Data requirements
with st.expander("📋 Data Requirements", expanded=False):
    st.markdown("""
    **Required files per event:**
    - `{slug}/output/{freq}_cumulative_aggregations.csv` - Cumulative donation aggregations
    - `{slug}/non_cumulative_donations/output/{freq}_non_cumulative_aggregations.csv` - Non-cumulative aggregations
    - `{slug}/polymarket_prices.csv` - Polymarket price history
    
    **Optional files:**
    - `trades_Plot/{slug}/{market_id}_*_segment.csv` - Trade-based odds (for Summary and User Analysis)
    
    **Configuration:**
    - `per_market_analysis/event_slugs.json` - List of event slugs to analyze
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>Per-Market Analysis Dashboard | Built with Streamlit</small>
</div>
""", unsafe_allow_html=True)
