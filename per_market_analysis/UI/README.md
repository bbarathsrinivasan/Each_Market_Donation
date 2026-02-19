# Per-Market Analysis Streamlit UI

Interactive web application for visualizing donation and prediction market data from the per_market_analysis pipeline.

## Installation

Install required dependencies:

```bash
pip install streamlit plotly pandas
```

## Running the Application

From the `UI/` directory:

```bash
streamlit run app.py
```

Or from the repository root:

```bash
cd per_market_analysis/UI
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## Navigation

The application uses Streamlit's multi-page feature. Navigate between pages using the sidebar menu:

1. **📊 Basic Donation + Polymarket** - Cumulative donation ratio with Polymarket overlay
2. **📈 Cumulative Segments** - Segment breakdown (cumulative)
3. **📉 Non-Cumulative Segments** - Segment breakdown (period-specific)
4. **🔀 Summary Analysis** - All four signals combined
5. **👥 User Analysis** - Trade-based odds comparison

## Data Requirements

### Required Files

For each event slug (e.g., `arizona-us-senate-election-winner`):

- **Cumulative aggregations:** `{slug}/output/{freq}_cumulative_aggregations.csv`
  - Must contain columns: `Year_Date`/`Year_Week`/`Year_Month`, `Dem_Ratio`, `Segment`
  - Segments: All, Small, Medium, Large

- **Non-cumulative aggregations:** `{slug}/non_cumulative_donations/output/{freq}_non_cumulative_aggregations.csv`
  - Same structure as cumulative

- **Polymarket prices:** `{slug}/polymarket_prices.csv`
  - Columns: `timestamp`, `outcome_label`, `price`

### Optional Files

- **Trade data:** `trades_Plot/{slug}/{market_id}_*_segment.csv`
  - Required for Summary Analysis (prediction cumulative) and User Analysis pages
  - Columns: `day_offset`, `segment`, `odds`

### Configuration

- **Event slugs:** `per_market_analysis/event_slugs.json`
  - JSON array of event slugs or objects with `slug`, `democrat`, `republican` fields

## Usage

1. **Select an event** from the sidebar dropdown (or use Quick Event Selector on home page)
2. **Choose visualization page** from the sidebar menu
3. **Adjust controls** in the sidebar:
   - Frequency (daily/weekly/monthly)
   - Segments to display
   - Polymarket outcomes to show
   - Line toggles (for Summary Analysis)
4. **View explanations** by expanding the info panels below each plot
5. **Interact with plots** using Plotly controls (zoom, pan, hover, download)

## Features

- **Interactive Charts:** All plots use Plotly for zoom, pan, hover tooltips, and export
- **Dynamic Data Loading:** Only loads data when needed, with caching for performance
- **Error Handling:** Gracefully handles missing data with informative messages
- **Explanations:** Each page includes expandable panels explaining:
  - What the visualization shows
  - How calculations are performed
  - Data sources used
  - How to interpret the results

## Troubleshooting

### "No event slugs found"
- Ensure `per_market_analysis/event_slugs.json` exists and contains valid slugs
- Check file permissions

### "No data available"
- Verify that the event directory exists: `per_market_analysis/{slug}/`
- Check that required CSV files exist in the expected locations
- Ensure CSV files have the correct column names

### "No trades data found"
- User Analysis and Summary Analysis (prediction cumulative) require `trades_Plot/` directory
- Run User-analysis pipeline first: `python -m per_market_analysis.User-analysis.calculate_trades_odds`

### Plot not displaying
- Check browser console for JavaScript errors
- Verify Plotly is installed: `pip install plotly`
- Try refreshing the page

### Path resolution issues
- Ensure you're running from the `UI/` directory or have the correct working directory
- The app uses `Path(__file__).resolve().parent.parent.parent` to find `per_market_analysis/`

## File Structure

```
per_market_analysis/UI/
├── app.py                          # Main application
├── utils/
│   ├── constants.py                # Constants (colors, time columns, etc.)
│   ├── data_loader.py              # Data loading functions
│   └── plot_generators.py          # Plotly plot generation functions
├── pages/
│   ├── 1_📊_Basic_Donation_Polymarket.py
│   ├── 2_📈_Cumulative_Segments.py
│   ├── 3_📉_Non_Cumulative_Segments.py
│   ├── 4_🔀_Summary_Analysis.py
│   └── 5_👥_User_Analysis.py
├── components/
│   ├── explanations.py             # Explanation text dictionaries
│   └── info_panels.py              # Reusable info panel components
└── README.md                       # This file
```

## Development

To modify the application:

1. **Add new plots:** Extend `utils/plot_generators.py` with new Plotly functions
2. **Add new pages:** Create new files in `pages/` following the naming convention `N_📊_Page_Name.py`
3. **Modify explanations:** Edit `components/explanations.py`
4. **Change styling:** Modify constants in `utils/constants.py` or update Plotly layout in plot generators

## Performance Tips

- Data is cached using `@st.cache_data` decorators
- Large datasets are loaded lazily (only when needed)
- Consider running on a server for shared access
- For very large datasets, consider pre-aggregating or sampling

## Support

For issues or questions:
1. Check that all required data files exist
2. Verify event slugs are correctly configured
3. Review error messages in the Streamlit console
4. Check browser console for JavaScript errors
