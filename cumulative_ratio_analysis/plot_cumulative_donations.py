#!/usr/bin/env python3
"""
Generate cumulative donation ratio visualizations.
Ratios are calculated on 0-1 scale: Party / (Dem + Rep)
Creates plots for both normal and log scales.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 10

def load_aggregations():
    """Load weekly and monthly cumulative aggregation data."""
    data_dir = Path('output')
    
    weekly_file = data_dir / 'weekly_cumulative_aggregations.csv'
    monthly_file = data_dir / 'monthly_cumulative_aggregations.csv'
    
    if not weekly_file.exists() or not monthly_file.exists():
        print("✗ Error: Aggregation files not found")
        print("  Run prepare_cumulative_donations.py first")
        return None, None
    
    weekly_df = pd.read_csv(weekly_file)
    monthly_df = pd.read_csv(monthly_file)
    
    return weekly_df, monthly_df

def plot_ratio(data, time_col, ratio_col, party_name, frequency, segment_name, output_dir, log_scale=False):
    """Plot cumulative ratio over time (0-1 scale)."""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Remove NaN values for plotting
    plot_data = data[[time_col, ratio_col]].dropna()
    
    if len(plot_data) == 0:
        print(f"  Warning: No valid data for {party_name} ratio ({frequency}, {segment_name})")
        plt.close()
        return
    
    # Plot
    color = '#2E86AB' if party_name == 'Democratic' else '#A23B72'
    ax.plot(range(len(plot_data)), plot_data[ratio_col], 
            linewidth=2, color=color,
            marker='o', markersize=3, alpha=0.7)
    
    # Add horizontal reference line at 0.5 (equal donations)
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='Equal Donations (0.5)')
    
    # Formatting
    ax.set_xlabel(f'{frequency.capitalize()} Period', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'Cumulative Ratio\n{party_name[:3]} / (Dem + Rep)', fontsize=12, fontweight='bold')
    
    title = f'{party_name} Cumulative Ratio - {frequency.capitalize()}'
    if segment_name != 'All':
        title += f' ({segment_name} Donors)'
    if log_scale:
        title += ' [Log Scale]'
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Set x-axis labels (show every nth label to avoid crowding)
    step = max(1, len(plot_data) // 15)
    x_positions = range(0, len(plot_data), step)
    x_labels = plot_data[time_col].iloc[::step].tolist()
    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    
    # Set y-axis limits to 0-1 for better visibility
    if not log_scale:
        ax.set_ylim([0, 1])
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
    
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save
    party_short = 'dem' if party_name == 'Democratic' else 'rep'
    segment_short = segment_name.lower()
    log_suffix = '_log' if log_scale else ''
    filename = f'cumulative_ratio_{frequency}_{segment_short}_{party_short}{log_suffix}.png'
    filepath = output_dir / filename
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {filename}")

def main():
    """Main function to generate all cumulative ratio plots."""
    print("="*80)
    print("GENERATE CUMULATIVE DONATION RATIO PLOTS")
    print("="*80)
    
    # Create output directories
    normal_dir = Path('plots_normal')
    log_dir = Path('plots_log')
    normal_dir.mkdir(exist_ok=True)
    log_dir.mkdir(exist_ok=True)
    print(f"\nNormal scale output: {normal_dir}/")
    print(f"Log-scale output: {log_dir}/")
    
    # Load data
    print(f"\n[1/3] Loading cumulative aggregation data...")
    weekly_df, monthly_df = load_aggregations()
    
    if weekly_df is None or monthly_df is None:
        return
    
    print(f"  ✓ Loaded weekly data: {len(weekly_df):,} records")
    print(f"  ✓ Loaded monthly data: {len(monthly_df):,} records")
    
    segments = weekly_df['Segment'].unique().tolist()
    frequencies = [('weekly', 'Year_Week', weekly_df), ('monthly', 'Year_Month', monthly_df)]
    
    # Generate Democratic cumulative ratio plots
    print(f"\n[2/3] Generating cumulative ratio plots...")
    
    plot_count = 0
    
    for freq_name, time_col, df in frequencies:
        for segment in segments:
            segment_data = df[df['Segment'] == segment].copy()
            
            # Democratic ratio - normal scale
            plot_ratio(segment_data, time_col, 'Dem_Ratio', 'Democratic', 
                      freq_name, segment, normal_dir)
            plot_count += 1
            
            # Democratic ratio - log scale
            plot_ratio(segment_data, time_col, 'Dem_Ratio', 'Democratic', 
                      freq_name, segment, log_dir, log_scale=True)
            plot_count += 1
            
            # Republican ratio - normal scale
            plot_ratio(segment_data, time_col, 'Rep_Ratio', 'Republican', 
                      freq_name, segment, normal_dir)
            plot_count += 1
            
            # Republican ratio - log scale
            plot_ratio(segment_data, time_col, 'Rep_Ratio', 'Republican', 
                      freq_name, segment, log_dir, log_scale=True)
            plot_count += 1
    
    # Generate summary statistics
    print(f"\n[3/3] Generating summary statistics...")
    
    summary_data = []
    
    for freq_name, time_col, df in frequencies:
        for segment in segments:
            segment_data = df[df['Segment'] == segment].copy()
            
            if len(segment_data) > 0:
                summary_data.append({
                    'Frequency': freq_name.capitalize(),
                    'Segment': segment,
                    'Metric': 'Dem Ratio Mean',
                    'Value': segment_data['Dem_Ratio'].mean()
                })
                summary_data.append({
                    'Frequency': freq_name.capitalize(),
                    'Segment': segment,
                    'Metric': 'Dem Ratio Median',
                    'Value': segment_data['Dem_Ratio'].median()
                })
                summary_data.append({
                    'Frequency': freq_name.capitalize(),
                    'Segment': segment,
                    'Metric': 'Rep Ratio Mean',
                    'Value': segment_data['Rep_Ratio'].mean()
                })
                summary_data.append({
                    'Frequency': freq_name.capitalize(),
                    'Segment': segment,
                    'Metric': 'Rep Ratio Median',
                    'Value': segment_data['Rep_Ratio'].median()
                })
                summary_data.append({
                    'Frequency': freq_name.capitalize(),
                    'Segment': segment,
                    'Metric': 'Total Cumulative Dem',
                    'Value': segment_data['Cumulative_DEM'].iloc[-1]
                })
                summary_data.append({
                    'Frequency': freq_name.capitalize(),
                    'Segment': segment,
                    'Metric': 'Total Cumulative Rep',
                    'Value': segment_data['Cumulative_REP'].iloc[-1]
                })
    
    summary_df = pd.DataFrame(summary_data)
    summary_file = Path('output') / 'cumulative_ratio_summary.csv'
    summary_df.to_csv(summary_file, index=False)
    print(f"  ✓ Saved summary statistics to {summary_file}")
    
    print(f"\n{'='*80}")
    print(f"✓ Generated all plots successfully!")
    print(f"✓ Total plots created: {plot_count}")
    print(f"✓ Normal scale location: {normal_dir}/")
    print(f"✓ Log-scale location: {log_dir}/")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
