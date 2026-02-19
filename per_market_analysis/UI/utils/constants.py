"""Constants for the Streamlit UI application."""

# Time column mappings
TIME_COLS = {"daily": "Year_Date", "weekly": "Year_Week", "monthly": "Year_Month"}

# Segment colors (matching existing plot code)
SEGMENT_COLORS = {
    "All": "#2E86AB",
    "Small": "#44AF69",
    "Medium": "#F4A261",
    "Large": "#9B59B6"
}

# Donation color
DONATION_COLOR = "#2E86AB"

# Polymarket colors
POLYMARKET_COLORS = ["#E94F37", "#3F88C5", "#44AF69", "#F4A261", "#9B59B6", "#F39C12"]

# Summary plot line colors
LINE_COLORS = {
    "donation_cumulative": "#2E86AB",
    "prediction_cumulative": "#E94F37",
    "donation_non_cumulative": "#44AF69",
    "prediction_non_cumulative": "#9B59B6",
}

# Available frequencies
FREQUENCIES = ["daily", "weekly", "monthly"]

# Available segments
SEGMENTS = ["All", "Small", "Medium", "Large"]

# User analysis segments
USER_SEGMENTS = ["all_users", "small", "medium", "large"]
