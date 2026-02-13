#!/usr/bin/env python3
"""
Master orchestration script for cumulative donation ratio analysis.
Runs both data preparation and visualization in sequence.
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name, description):
    """Run a Python script and handle errors."""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print(f"\n✗ Error running {script_name}")
        return False
    
    print(f"\n✓ {description} completed successfully")
    return True

def main():
    """Main orchestration function."""
    print("="*80)
    print("CUMULATIVE DONATION RATIO ANALYSIS - MASTER ORCHESTRATION")
    print("="*80)
    print("\nThis will:")
    print("  1. Process ~70M donation records")
    print("  2. Create weekly/monthly cumulative aggregations")
    print("  3. Generate 32 cumulative ratio plots (16 normal + 16 log scale)")
    print("\n⏱ Estimated time: 15-25 minutes depending on system performance")
    print("="*80)
    
    # Step 1: Data preparation
    if not run_script('prepare_cumulative_donations.py', 'Data Preparation'):
        return
    
    # Step 2: Visualization
    if not run_script('plot_cumulative_donations.py', 'Visualization Generation'):
        return
    
    print("\n" + "="*80)
    print("✓ ALL TASKS COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\nGenerated files:")
    print("  • output/ - Processed data and aggregations")
    print("  • plots_normal/ - 16 normal scale plots")
    print("  • plots_log/ - 16 log scale plots")
    print("\nTotal plots: 32 (16 normal + 16 log scale)")
    print("Total scenarios: 4 (Dem/Rep × All/Small/Medium/Large)")
    print("Total time periods: 2 (Weekly + Monthly)")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
