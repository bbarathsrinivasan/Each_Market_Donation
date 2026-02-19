# Streamlit Cloud Deployment Guide

This guide explains how to deploy the Per-Market Analysis Dashboard to Streamlit Community Cloud.

## Files Created for Deployment

- `requirements.txt` - Python dependencies
- `app.py` - Root-level entry point (alternative option)
- `.gitignore` - Updated to allow `requirements.txt`

## Deployment Options

### Option 1: Use UI App Directly (Recommended)

Configure Streamlit Cloud to use the UI app directly:

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository: `bbarathsrinivasan/Each_Market_Donation`
5. Branch: `main`
6. **Main file path:** `per_market_analysis/UI/app.py`
7. Click "Deploy"

This is the recommended approach as it preserves the original app structure and multi-page navigation.

### Option 2: Use Root-Level App

If you prefer to use the root-level `app.py`:

1. Configure Streamlit Cloud with:
   - Repository: `bbarathsrinivasan/Each_Market_Donation`
   - Branch: `main`
   - **Main file path:** `app.py`

**Note:** This option requires that Streamlit can discover the pages. Since pages are in `per_market_analysis/UI/pages/`, you may need to create symbolic links or adjust the structure.

## Required Files in Repository

Ensure these files are committed to your repository:

- `per_market_analysis/event_slugs.json` - Event configuration
- `per_market_analysis/{slug}/output/*.csv` - Cumulative aggregation data
- `per_market_analysis/{slug}/non_cumulative_donations/output/*.csv` - Non-cumulative data
- `per_market_analysis/{slug}/polymarket_prices.csv` - Polymarket price data
- `trades_Plot/{slug}/*.csv` - Trade data (optional, for some visualizations)

## Dependencies

All required Python packages are listed in `requirements.txt`:
- streamlit>=1.28.0
- pandas>=2.0.0
- plotly>=5.17.0
- numpy>=1.24.0

## Troubleshooting

### Pages Not Showing

If pages don't appear in the sidebar:
- Ensure you're using Option 1 (UI app directly)
- Check that `per_market_analysis/UI/pages/` directory exists with all page files
- Verify file naming follows Streamlit's page naming convention: `{number}_{name}.py`

### Import Errors

If you see import errors:
- Verify `requirements.txt` is in the repository root
- Check that all data files are committed
- Ensure `per_market_analysis/UI/` directory structure is intact

### Data Not Loading

If data doesn't load:
- Verify data files are committed to the repository
- Check file paths match the expected structure
- Ensure `event_slugs.json` exists and is valid

## Next Steps

1. Commit and push all changes:
   ```bash
   git add requirements.txt app.py .gitignore STREAMLIT_CLOUD_DEPLOYMENT.md
   git commit -m "Add Streamlit Cloud deployment files"
   git push origin main
   ```

2. Deploy on Streamlit Cloud using Option 1 (recommended)

3. Monitor the deployment logs for any errors

4. Test all pages and visualizations after deployment
