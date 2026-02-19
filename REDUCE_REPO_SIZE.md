# Reduce Repository Size for Streamlit Cloud Deployment

## Problem
Repository is **5.9GB**, which exceeds Streamlit Cloud's limits. Large files are tracked in git history.

## Large Files Found
- `donations_filtered.csv` files: **~200MB total** (9 files, 12-75MB each)
- `donor_segments.csv` files: **~10MB total**
- `Trades/*.csv` files: **~30MB total**
- Git history pack file: **842MB** (contains old commits with large files)

## Solution: Remove Large Files from Git

### Step 1: Remove Files from Git Tracking

Run the cleanup script:
```bash
./cleanup_repo.sh
```

Or manually remove files:
```bash
# Remove donations_filtered.csv files (not needed for Streamlit UI)
git rm --cached per_market_analysis/*/donations_filtered.csv
git rm --cached per_market_analysis/*/*/donations_filtered.csv

# Remove donor_segments.csv files
git rm --cached per_market_analysis/*/donor_segments.csv

# Remove Trades CSV files (if not needed)
git rm --cached per_market_analysis/Trades/**/*.csv

# Remove Summary_analysis output CSVs
git rm --cached per_market_analysis/Summary_analysis/output/*.csv
```

### Step 2: Commit Changes
```bash
git add .gitignore
git commit -m "Remove large data files from git tracking - reduce repo size for Streamlit Cloud"
```

### Step 3: Clean Up Git History (Optional but Recommended)

To completely remove large files from git history and reduce the `.git` folder size:

**Option A: Use git-filter-repo (Recommended)**
```bash
# Install git-filter-repo first: pip install git-filter-repo

# Remove donations_filtered.csv from entire history
git filter-repo --path-glob '**/donations_filtered.csv' --invert-paths

# Remove donor_segments.csv from entire history
git filter-repo --path-glob '**/donor_segments.csv' --invert-paths

# Remove Trades CSV files
git filter-repo --path-glob 'per_market_analysis/Trades/**/*.csv' --invert-paths
```

**Option B: Use BFG Repo-Cleaner**
```bash
# Download BFG from https://rtyley.github.io/bfg-repo-cleaner/

# Remove large CSV files
java -jar bfg.jar --delete-files donations_filtered.csv
java -jar bfg.jar --delete-files donor_segments.csv

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

**Option C: Simple Git GC (Less Effective)**
```bash
# Clean up and compress git history
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Step 4: Force Push (After History Cleanup)
```bash
# ⚠️ WARNING: This rewrites history. Coordinate with team members!
git push origin main --force-with-lease
```

## Files That Will Remain (Needed for Streamlit)

These files are **kept** because they're needed for the Streamlit visualization:
- ✅ `**/output/*_cumulative_aggregations.csv` - Cumulative donation data
- ✅ `**/non_cumulative_donations/output/*_non_cumulative_aggregations.csv` - Non-cumulative data
- ✅ `**/polymarket_prices.csv` - Polymarket prices
- ✅ `**/trades_Plot/**/*.csv` - Trade data (if needed)
- ✅ `per_market_analysis/event_slugs.json` - Configuration

## Files That Will Be Removed (Not Needed)

These files are **removed** because they're not used by Streamlit UI:
- ❌ `donations_filtered.csv` - Raw donation data (large, not used by UI)
- ❌ `donor_segments.csv` - Intermediate file (not used by UI)
- ❌ `Summary_analysis/output/*.csv` - Summary outputs (not directly used)
- ❌ `Trades/*.csv` - Raw trade data (if not needed)
- ❌ `.venv/` - Virtual environment (should never be in git)

## Expected Results

After cleanup:
- **Repository size**: Should reduce from 5.9GB to <100MB
- **Git history**: Cleaner, smaller pack files
- **Streamlit deployment**: Should work without size issues
- **Local files**: All files remain on your local machine (only removed from git)

## Verification

Check repository size after cleanup:
```bash
du -sh .git
du -sh .
```

Check what files are tracked:
```bash
git ls-files | wc -l
git ls-files | grep -E "\.csv$" | wc -l
```

## Alternative: Use Git LFS (If You Need Large Files)

If you need to keep large files but reduce repo size:
```bash
# Install Git LFS
git lfs install

# Track large CSV files with LFS
git lfs track "*.csv"
git lfs track "**/donations_filtered.csv"

# Add and commit
git add .gitattributes
git commit -m "Use Git LFS for large CSV files"
```

However, for Streamlit Cloud, it's better to exclude unnecessary files entirely.

## Troubleshooting

### "File is too large" error on GitHub
- GitHub has a 100MB file size limit
- Use Git LFS or remove the file

### "Repository size limit" on Streamlit Cloud
- Streamlit Cloud has size limits
- Remove unnecessary files as described above

### "Force push rejected"
- Someone else may have pushed changes
- Pull first: `git pull --rebase origin main`
- Then try force push again

## Next Steps

1. ✅ Run cleanup script: `./cleanup_repo.sh`
2. ✅ Review changes: `git status`
3. ✅ Commit: `git commit -m "Remove large files"`
4. ✅ Clean history (optional): Use git-filter-repo or BFG
5. ✅ Force push: `git push origin main --force-with-lease`
6. ✅ Verify size: `du -sh .git`
7. ✅ Deploy on Streamlit Cloud
