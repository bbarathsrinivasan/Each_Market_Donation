"""Root-level app entry point for Streamlit Cloud deployment."""

import sys
from pathlib import Path

# Add per_market_analysis/UI to path so imports work
UI_DIR = Path(__file__).resolve().parent / "per_market_analysis" / "UI"
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

# Import and run the UI app
from app import *
