"""Reusable info panels for displaying explanations and calculations."""

import streamlit as st

from .explanations import (
    BASIC_DONATION_EXPLANATION,
    CUMULATIVE_SEGMENTS_EXPLANATION,
    NON_CUMULATIVE_SEGMENTS_EXPLANATION,
    SUMMARY_ANALYSIS_EXPLANATION,
    USER_ANALYSIS_EXPLANATION,
)


def show_calculation_panel(plot_type: str, slug: str = "", frequency: str = ""):
    """Show expandable calculation details panel."""
    explanations = {
        "basic": BASIC_DONATION_EXPLANATION,
        "cumulative_segments": CUMULATIVE_SEGMENTS_EXPLANATION,
        "non_cumulative_segments": NON_CUMULATIVE_SEGMENTS_EXPLANATION,
        "summary": SUMMARY_ANALYSIS_EXPLANATION,
        "user_analysis": USER_ANALYSIS_EXPLANATION,
    }
    
    exp = explanations.get(plot_type)
    if not exp:
        return
    
    with st.expander("📖 About this visualization", expanded=False):
        st.markdown(f"**What it shows:**\n\n{exp['what']}")
        
        # Handle calculation - either top-level or in lines
        if "calculation" in exp:
            st.markdown(f"**How it's calculated:**\n\n{exp['calculation']}")
        
        if "data_source" in exp:
            data_source = exp["data_source"]
            if slug and frequency:
                data_source = data_source.replace("{slug}", slug).replace("{freq}", frequency)
            st.markdown(f"**Data sources:**\n\n{data_source}")
        
        if "interpretation" in exp:
            st.markdown(f"**How to interpret:**\n\n{exp['interpretation']}")
        
        if "difference" in exp:
            st.markdown(f"**Difference from cumulative:**\n\n{exp['difference']}")
        
        if "lines" in exp:
            st.markdown("**Each line explained:**")
            for line_name, line_info in exp["lines"].items():
                st.markdown(f"**{line_name.replace('_', ' ').title()}:**")
                st.markdown(f"- {line_info['description']}")
                if "calculation" in line_info:
                    st.markdown(f"- Calculation: {line_info['calculation']}")
                if "data_source" in line_info:
                    ds = line_info["data_source"]
                    if slug and frequency:
                        ds = ds.replace("{slug}", slug).replace("{freq}", frequency)
                    st.markdown(f"- Data: {ds}")
        
        if "x_axis" in exp:
            st.markdown(f"**X-axis:** {exp['x_axis']}")


def show_data_source_panel(file_paths: list[str]):
    """Show data file locations panel."""
    with st.expander("📁 Data files used", expanded=False):
        st.markdown("**Files loaded:**")
        for path in file_paths:
            if path:  # Skip None values
                st.code(path, language=None)


def show_interpretation_guide():
    """Show general interpretation guide."""
    with st.expander("📚 How to read these plots", expanded=False):
        st.markdown("""
        **Y-axis (0-1 scale):**
        - **0.0** = 100% Republican donations or 0% probability of Democrat winning
        - **0.5** = Equal donations from both parties or 50% probability
        - **1.0** = 100% Democratic donations or 100% probability of Democrat winning
        
        **Cumulative vs Non-Cumulative:**
        - **Cumulative**: Running total from the start. Shows overall trend over time.
        - **Non-Cumulative**: Period-specific only. Shows sentiment in each period without carry-forward.
        
        **Segments:**
        - **All**: All donors combined
        - **Small**: Bottom 33.3% by cumulative donation amount
        - **Medium**: Middle 33.3-66.6% by cumulative donation amount
        - **Large**: Top 33.3% by cumulative donation amount
        
        **Donation vs Prediction:**
        - **Donation ratios**: Based on actual campaign donations (DEM vs REP)
        - **Prediction odds**: Based on Polymarket prices or blockchain trades (market predictions)
        """)
