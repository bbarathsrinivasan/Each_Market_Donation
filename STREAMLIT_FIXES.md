# Streamlit Cloud File Watcher Fix

## Problem
Streamlit Cloud was encountering "inotify instance limit reached" errors because it was trying to watch too many files in the repository, including large data files that aren't needed for the visualization.

## Solution

### 1. Streamlit Configuration (`.streamlit/config.toml`)
- Changed file watcher from `inotify` (default) to `poll` mode
- Polling mode is more resource-efficient for large repositories
- Set polling interval to 5 seconds

### 2. Gitignore Updates (`.gitignore`)
Excluded large unnecessary CSV files from being committed:
- `**/donations_filtered.csv` - Raw donation data (too large, not used by UI)
- `**/donor_segments.csv` - Intermediate file (not used by UI)
- `**/Summary_analysis/output/*.csv` - Summary outputs (not directly used by UI)

**Allowed CSV files** (needed for visualization):
- `**/output/*_cumulative_aggregations.csv` - Cumulative donation data
- `**/non_cumulative_donations/output/*_non_cumulative_aggregations.csv` - Non-cumulative data
- `**/polymarket_prices.csv` - Polymarket price data
- `**/trades_Plot/**/*.csv` - Trade-based odds data

### 3. Files Created/Modified
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `.gitignore` - Updated to exclude unnecessary large files
- ✅ `STREAMLIT_FIXES.md` - This documentation

## Next Steps

1. **Commit the changes:**
   ```bash
   git add .streamlit/config.toml .gitignore STREAMLIT_FIXES.md
   git commit -m "Fix Streamlit Cloud inotify limit error - use polling and exclude large data files"
   git push origin main
   ```

2. **Redeploy on Streamlit Cloud:**
   - The app should automatically redeploy when you push
   - The polling file watcher will prevent inotify limit errors
   - Fewer files will be watched, reducing resource usage

## Expected Results

- ✅ No more "inotify instance limit reached" errors
- ✅ Faster app startup (fewer files to watch)
- ✅ Reduced resource usage on Streamlit Cloud
- ✅ App functionality unchanged (only necessary files are included)

## Notes

- The `fileWatcherType = "poll"` setting tells Streamlit to use polling instead of inotify
- Polling checks for file changes at regular intervals instead of using system file watchers
- This is slightly less responsive but much more reliable for large repositories
- The excluded CSV files are not needed for the Streamlit visualization - they're raw/intermediate data
