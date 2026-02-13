#!/usr/bin/env python3
"""
Calculate investment-weighted odds from blockchain trades data.

Processes trades CSV files, calculates cumulative positions per user,
computes individual YES/NO exposures, aggregates by user segments,
and compares with Polymarket closing prices.

Run from repo root: python per_market_analysis/User-analysis/calculate_trades_odds.py
Or: cd per_market_analysis/User-analysis && python calculate_trades_odds.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Allow running from repo root or from User-analysis/
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Set style (use non-interactive backend to avoid display issues)
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)


def normalize_trades_and_compute_day_offset(trades_df: pd.DataFrame, market_id: str) -> pd.DataFrame:
    """
    Parse trades, extract user_id, side, quantity, dates, and compute day_offset.
    
    Args:
        trades_df: DataFrame with columns: timestamp, maker, taker, nonusdc_side,
                   maker_direction, taker_direction, token_amount
        market_id: Market ID for logging
    
    Returns:
        DataFrame with: user_id, side, quantity, unix_timestamp, date, token_type, day_offset
    """
    # Parse timestamp
    trades_df["datetime"] = pd.to_datetime(trades_df["timestamp"])
    trades_df["date"] = trades_df["datetime"].dt.date
    trades_df["unix_timestamp"] = trades_df["datetime"].astype("int64") // 10**9
    
    # Map token1 -> YES, token2 -> NO
    trades_df["token_type"] = trades_df["nonusdc_side"].map({"token1": "YES", "token2": "NO"})
    
    # Create rows for both maker and taker
    maker_rows = trades_df.copy()
    maker_rows["user_id"] = maker_rows["maker"]
    maker_rows["side"] = maker_rows["maker_direction"]
    
    taker_rows = trades_df.copy()
    taker_rows["user_id"] = taker_rows["taker"]
    taker_rows["side"] = taker_rows["taker_direction"]
    
    # Combine
    normalized = pd.concat([maker_rows, taker_rows], ignore_index=True)
    
    # Select columns
    result = normalized[["user_id", "side", "token_amount", "unix_timestamp", "date", "token_type"]].copy()
    result.rename(columns={"token_amount": "quantity"}, inplace=True)
    
    # Compute closing_date and day_offset
    closing_date = result["date"].max()
    result["day_offset"] = (result["date"] - closing_date).apply(lambda x: x.days)
    
    return result


def build_per_user_daily_token_series(trades_normalized_df: pd.DataFrame) -> pd.DataFrame:
    """
    Group by (user_id, token_type, day_offset) and compute daily buys/sells.
    
    Args:
        trades_normalized_df: DataFrame from normalize_trades_and_compute_day_offset
    
    Returns:
        DataFrame with: user_id, token_type, day_offset, daily_buy, daily_sell, net_tokens, end_of_day_timestamp
    """
    # Group by user, token, day
    grouped = trades_normalized_df.groupby(["user_id", "token_type", "day_offset"])
    
    # Compute daily_buy and daily_sell
    daily_buy = (
        trades_normalized_df[trades_normalized_df["side"] == "BUY"]
        .groupby(["user_id", "token_type", "day_offset"])["quantity"]
        .sum()
        .reset_index(name="daily_buy")
    )
    
    daily_sell = (
        trades_normalized_df[trades_normalized_df["side"] == "SELL"]
        .groupby(["user_id", "token_type", "day_offset"])["quantity"]
        .sum()
        .reset_index(name="daily_sell")
    )
    
    # Get all unique combinations
    all_combos = trades_normalized_df[["user_id", "token_type", "day_offset"]].drop_duplicates()
    
    # Merge
    daily_series = all_combos.merge(daily_buy, on=["user_id", "token_type", "day_offset"], how="left")
    daily_series = daily_series.merge(daily_sell, on=["user_id", "token_type", "day_offset"], how="left")
    daily_series = daily_series.fillna(0)
    
    # Compute net_tokens
    daily_series["net_tokens"] = daily_series["daily_buy"] - daily_series["daily_sell"]
    
    # Get end_of_day_timestamp
    end_timestamps = grouped["unix_timestamp"].max().reset_index(name="end_of_day_timestamp")
    daily_series = daily_series.merge(end_timestamps, on=["user_id", "token_type", "day_offset"], how="left")
    
    return daily_series


def accumulate_positions_over_time(daily_series_df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort by day_offset and compute cumulative positions per user/token.
    
    Args:
        daily_series_df: DataFrame from build_per_user_daily_token_series
    
    Returns:
        DataFrame with: user_id, day_offset, yes_cumulative_position, no_cumulative_position
    """
    # Sort by user, token, day_offset (ascending)
    sorted_df = daily_series_df.sort_values(["user_id", "token_type", "day_offset"]).copy()
    
    # Compute cumulative sum per (user_id, token_type)
    sorted_df["cumulative_position"] = sorted_df.groupby(["user_id", "token_type"])["net_tokens"].cumsum()
    
    # Separate YES and NO positions
    yes_df = sorted_df[sorted_df["token_type"] == "YES"][["user_id", "day_offset", "cumulative_position"]].copy()
    yes_df.rename(columns={"cumulative_position": "yes_cumulative_position"}, inplace=True)
    
    no_df = sorted_df[sorted_df["token_type"] == "NO"][["user_id", "day_offset", "cumulative_position"]].copy()
    no_df.rename(columns={"cumulative_position": "no_cumulative_position"}, inplace=True)
    
    # Get all unique (user_id, day_offset) combinations
    all_user_days = sorted_df[["user_id", "day_offset"]].drop_duplicates()
    
    # Merge YES and NO positions
    result = all_user_days.merge(yes_df, on=["user_id", "day_offset"], how="left")
    result = result.merge(no_df, on=["user_id", "day_offset"], how="left")
    result = result.fillna(0)
    
    # Forward fill cumulative positions per user (to handle days where user didn't trade)
    result = result.sort_values(["user_id", "day_offset"])
    result["yes_cumulative_position"] = (
        result.groupby("user_id")["yes_cumulative_position"]
        .transform(lambda x: x.replace(0, pd.NA).ffill().fillna(0))
    )
    result["no_cumulative_position"] = (
        result.groupby("user_id")["no_cumulative_position"]
        .transform(lambda x: x.replace(0, pd.NA).ffill().fillna(0))
    )
    
    return result[["user_id", "day_offset", "yes_cumulative_position", "no_cumulative_position"]]


def compute_individual_positions(positions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute individual YES/NO exposures from cumulative positions.
    
    Formulas:
    - individual_yes_position = (Hy > 0) * Hy + (Hn < 0) * (-Hn)
    - individual_no_position = (Hn > 0) * Hn + (Hy < 0) * (-Hy)
    
    Args:
        positions_df: DataFrame from accumulate_positions_over_time
    
    Returns:
        DataFrame with: user_id, day_offset, individual_yes_position, individual_no_position,
                        yes_cumulative_position, no_cumulative_position
    """
    result = positions_df.copy()
    
    Hy = result["yes_cumulative_position"]
    Hn = result["no_cumulative_position"]
    
    # Individual YES exposure
    result["individual_yes_position"] = ((Hy > 0) * Hy + (Hn < 0) * (-Hn)).fillna(0)
    
    # Individual NO exposure
    result["individual_no_position"] = ((Hn > 0) * Hn + (Hy < 0) * (-Hy)).fillna(0)
    
    return result[["user_id", "day_offset", "individual_yes_position", "individual_no_position", 
                   "yes_cumulative_position", "no_cumulative_position"]]


def compute_segments_from_trades(trades_df: pd.DataFrame) -> dict[str, str]:
    """
    Compute user segments from trades data by summing USD amounts per user.
    
    Args:
        trades_df: DataFrame with columns: maker, taker, usd_amount
    
    Returns:
        Dict mapping user_id -> "Small"/"Medium"/"Large"
    """
    # Get all unique users (both maker and taker)
    all_users = pd.concat([
        trades_df[["maker", "usd_amount"]].rename(columns={"maker": "user_id"}),
        trades_df[["taker", "usd_amount"]].rename(columns={"taker": "user_id"})
    ])
    
    # Sum USD amounts per user
    user_totals = all_users.groupby("user_id")["usd_amount"].sum().reset_index()
    user_totals["user_id_lower"] = user_totals["user_id"].str.lower()
    
    segments = {}
    for _, row in user_totals.iterrows():
        user_id = row["user_id_lower"]
        value = float(row["usd_amount"])
        
        if value >= 1_000_000:
            segments[user_id] = "large"
        elif value >= 10_000:
            segments[user_id] = "medium"
        else:
            segments[user_id] = "small"
    
    return segments


def load_user_segments(segments_file_path: Path) -> dict[str, str]:
    """
    Load user segments from all_users_analysis.csv.
    
    Args:
        segments_file_path: Path to all_users_analysis.csv
    
    Returns:
        Dict mapping user_id -> "Small"/"Medium"/"Large"
    """
    if not segments_file_path.exists():
        return {}
    
    try:
        df = pd.read_csv(segments_file_path)
        
        # Check required columns
        if "user_id" not in df.columns or "cumulative_total_value_max" not in df.columns:
            print(f"Warning: {segments_file_path} missing required columns. Skipping segments.")
            return {}
        
        segments = {}
        for _, row in df.iterrows():
            user_id = str(row["user_id"]).lower()
            value = float(row["cumulative_total_value_max"])
            
            if value >= 1_000_000:
                segments[user_id] = "large"
            elif value >= 10_000:
                segments[user_id] = "medium"
            else:
                segments[user_id] = "small"
        
        return segments
    except Exception as e:
        print(f"Warning: Could not load segments from {segments_file_path}: {e}")
        return {}


def aggregate_by_day_offset_and_segment(
    individual_positions_df: pd.DataFrame,
    user_segments_dict: dict[str, str]
) -> pd.DataFrame:
    """
    Aggregate individual positions by day_offset and segment, compute odds.
    
    Args:
        individual_positions_df: DataFrame from compute_individual_positions
        user_segments_dict: Dict mapping user_id -> segment
    
    Returns:
        DataFrame with: day_offset, segment, agg_yes, agg_no, odds
    """
    # Map user_id to segment
    individual_positions_df = individual_positions_df.copy()
    individual_positions_df["user_id_lower"] = individual_positions_df["user_id"].str.lower()
    individual_positions_df["segment"] = individual_positions_df["user_id_lower"].map(
        lambda x: user_segments_dict.get(x, "all_users")
    )
    # Normalize segment names to lowercase for consistency
    individual_positions_df["segment"] = individual_positions_df["segment"].str.lower()
    
    # First compute "all_users" aggregate (across all users, regardless of segment)
    all_users_agg = []
    for day_offset in individual_positions_df["day_offset"].unique():
        day_data = individual_positions_df[individual_positions_df["day_offset"] == day_offset]
        yes_users = day_data[day_data["yes_cumulative_position"] != 0]
        no_users = day_data[day_data["no_cumulative_position"] != 0]
        agg_yes = yes_users["individual_yes_position"].sum()
        agg_no = no_users["individual_no_position"].sum()
        total = agg_yes + agg_no
        odds = agg_yes / total if total > 0 else 0.0
        all_users_agg.append({
            "day_offset": day_offset,
            "segment": "all_users",
            "agg_yes": agg_yes,
            "agg_no": agg_no,
            "odds": odds
        })
    
    result_list = all_users_agg.copy()
    
    # Then compute segment-specific aggregates (if segments available)
    if len(user_segments_dict) > 0:
        for (day_offset, segment), group in individual_positions_df.groupby(["day_offset", "segment"]):
            if segment == "all_users":
                continue  # Already computed above
            
            # Filter users with non-zero positions for this segment
            yes_users = group[group["yes_cumulative_position"] != 0]
            no_users = group[group["no_cumulative_position"] != 0]
            agg_yes = yes_users["individual_yes_position"].sum()
            agg_no = no_users["individual_no_position"].sum()
            total = agg_yes + agg_no
            odds = agg_yes / total if total > 0 else 0.0
            result_list.append({
                "day_offset": day_offset,
                "segment": segment.lower(),  # Ensure lowercase
                "agg_yes": agg_yes,
                "agg_no": agg_no,
                "odds": odds
            })
    
    result_df = pd.DataFrame(result_list)
    return result_df.sort_values(["day_offset", "segment"])


def load_price_based_market_odds(prices_csv_path: Path, closing_date: datetime.date) -> pd.DataFrame:
    """
    Load YES prices from polymarket_prices.csv and compute day_offset.
    
    Args:
        prices_csv_path: Path to polymarket_prices.csv
        closing_date: Closing date for the market
    
    Returns:
        DataFrame with: day_offset, price_odds
    """
    if not prices_csv_path.exists():
        return pd.DataFrame(columns=["day_offset", "price_odds"])
    
    try:
        df = pd.read_csv(prices_csv_path)
        
        # Filter for YES token (outcome_label like "Democrat" or check metadata)
        # For now, assume any non-empty outcome_label is YES token
        # In practice, might need to check market metadata
        df = df[df["outcome_label"].notna()].copy()
        
        if len(df) == 0:
            return pd.DataFrame(columns=["day_offset", "price_odds"])
        
        # Parse timestamp to date
        df["date"] = pd.to_datetime(df["timestamp"], unit="s").dt.date
        
        # Compute day_offset
        df["day_offset"] = (df["date"] - closing_date).apply(lambda x: x.days)
        
        # Drop rows where day_offset > 0 (only historical prices)
        df = df[df["day_offset"] <= 0].copy()
        
        # Get last price per day (end-of-day price)
        daily_prices = df.groupby("day_offset")["price"].last().reset_index()
        daily_prices.rename(columns={"price": "price_odds"}, inplace=True)
        
        return daily_prices.sort_values("day_offset")
    except Exception as e:
        print(f"Warning: Could not load prices from {prices_csv_path}: {e}")
        return pd.DataFrame(columns=["day_offset", "price_odds"])


def plot_odds_comparison(
    aggregated_df: pd.DataFrame,
    price_odds_df: pd.DataFrame,
    output_path: Path,
    market_id: str
) -> None:
    """
    Plot odds comparison: price_odds vs segment-based odds.
    Creates 5 different charts:
    1. All segments together (existing)
    2. Price odds vs all_users
    3. Price odds vs large
    4. Price odds vs medium
    5. Price odds vs small
    
    Args:
        aggregated_df: DataFrame from aggregate_by_day_offset_and_segment
        price_odds_df: DataFrame from load_price_based_market_odds
        output_path: Path to save plot (base path, will add suffixes)
        market_id: Market ID for title
    """
    segments_info = {
        "all_users": {"color": "green", "label": "All Users"},
        "small": {"color": "orange", "label": "Small Segment"},
        "medium": {"color": "red", "label": "Medium Segment"},
        "large": {"color": "purple", "label": "Large Segment"}
    }
    
    # Chart 1: All segments together
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot price odds (blue)
    if len(price_odds_df) > 0:
        ax.plot(
            price_odds_df["day_offset"],
            price_odds_df["price_odds"],
            color="blue",
            label="Price Odds (Polymarket)",
            linewidth=2,
            marker="o",
            markersize=3
        )
    
    # Plot all segment odds
    for segment, info in segments_info.items():
        segment_data = aggregated_df[aggregated_df["segment"] == segment]
        if len(segment_data) > 0:
            ax.plot(
                segment_data["day_offset"],
                segment_data["odds"],
                color=info["color"],
                label=info["label"],
                linewidth=2,
                marker="s",
                markersize=3
            )
    
    ax.set_xlabel("Day Offset (0 = closing day)", fontsize=12)
    ax.set_ylabel("Odds (0-1)", fontsize=12)
    ax.set_title(f"Odds Comparison - Market {market_id} (All Segments)", fontsize=14, fontweight="bold")
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)
    
    plt.tight_layout()
    all_segments_path = output_path.parent / f"{output_path.stem}_all_segments{output_path.suffix}"
    plt.savefig(all_segments_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    # Charts 2-5: Individual segment comparisons
    for segment, info in segments_info.items():
        segment_data = aggregated_df[aggregated_df["segment"] == segment]
        if len(segment_data) == 0:
            continue
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot price odds (blue)
        if len(price_odds_df) > 0:
            ax.plot(
                price_odds_df["day_offset"],
                price_odds_df["price_odds"],
                color="blue",
                label="Price Odds (Polymarket)",
                linewidth=2,
                marker="o",
                markersize=3
            )
        
        # Plot segment odds
        ax.plot(
            segment_data["day_offset"],
            segment_data["odds"],
            color=info["color"],
            label=info["label"],
            linewidth=2,
            marker="s",
            markersize=3
        )
        
        ax.set_xlabel("Day Offset (0 = closing day)", fontsize=12)
        ax.set_ylabel("Odds (0-1)", fontsize=12)
        ax.set_title(f"Odds Comparison - Market {market_id} ({info['label']})", fontsize=14, fontweight="bold")
        ax.legend(loc="best", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
        
        plt.tight_layout()
        segment_path = output_path.parent / f"{output_path.stem}_{segment}{output_path.suffix}"
        plt.savefig(segment_path, dpi=300, bbox_inches="tight")
        plt.close()


def process_market(
    trades_csv_path: Path,
    market_id: str,
    event_id: str,
    segments_dict: dict[str, str],
    prices_csv_path: Path,
    output_dir: Path
) -> None:
    """
    Process a single market: load trades, compute odds, save CSVs and plot.
    
    Args:
        trades_csv_path: Path to <market_id>_trades.csv
        market_id: Market ID
        event_id: Event ID (slug)
        segments_dict: User segments mapping (can be empty, will compute from trades)
        prices_csv_path: Path to polymarket_prices.csv
        output_dir: Directory to save outputs
    """
    print(f"Processing market {market_id} for event {event_id}...")
    
    # Load trades
    try:
        trades_df = pd.read_csv(trades_csv_path, low_memory=False)
        if len(trades_df) == 0:
            print(f"  Warning: Empty trades file for {market_id}")
            return
        print(f"  Loaded {len(trades_df)} trades")
    except Exception as e:
        print(f"  Error loading trades: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Compute segments from trades if not provided
    market_segments_dict = segments_dict.copy()
    if len(market_segments_dict) == 0:
        print(f"  Computing segments from trades data...")
        market_segments_dict = compute_segments_from_trades(trades_df)
        print(f"  Computed segments for {len(market_segments_dict)} users")
        # Count by segment (normalize to lowercase)
        segment_counts = {}
        for seg in market_segments_dict.values():
            seg_lower = seg.lower()
            segment_counts[seg_lower] = segment_counts.get(seg_lower, 0) + 1
        print(f"    Small: {segment_counts.get('small', 0)}, Medium: {segment_counts.get('medium', 0)}, Large: {segment_counts.get('large', 0)}")
    
    try:
        # Step 1: Normalize trades and compute day_offset
        print(f"  Step 1: Normalizing trades...")
        normalized = normalize_trades_and_compute_day_offset(trades_df, market_id)
        closing_date = normalized["date"].max()
        print(f"  Closing date: {closing_date}")
        
        # Step 2: Build per-user daily token series
        print(f"  Step 2: Building daily token series...")
        daily_series = build_per_user_daily_token_series(normalized)
        print(f"  Daily series: {len(daily_series)} rows")
        
        # Step 3: Accumulate positions over time
        print(f"  Step 3: Accumulating positions...")
        positions = accumulate_positions_over_time(daily_series)
        print(f"  Positions: {len(positions)} rows")
        
        # Step 4: Compute individual positions
        print(f"  Step 4: Computing individual positions...")
        individual_positions = compute_individual_positions(positions)
        print(f"  Individual positions: {len(individual_positions)} rows")
        
        # Step 5: Aggregate by day_offset and segment
        print(f"  Step 5: Aggregating by segment...")
        aggregated = aggregate_by_day_offset_and_segment(individual_positions, market_segments_dict)
        print(f"  Aggregated: {len(aggregated)} rows")
        # Show segment breakdown
        for seg in ["all_users", "small", "medium", "large"]:
            seg_data = aggregated[aggregated["segment"] == seg]
            if len(seg_data) > 0:
                print(f"    {seg}: {len(seg_data)} day_offset values")
        
        # Step 6: Load price-based market odds
        print(f"  Step 6: Loading price odds...")
        price_odds = load_price_based_market_odds(prices_csv_path, closing_date)
        print(f"  Price odds: {len(price_odds)} rows")
        
        # Step 7: Save CSVs
        print(f"  Step 7: Saving CSVs...")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for segment in ["all_users", "small", "medium", "large"]:
            segment_data = aggregated[aggregated["segment"] == segment]
            if len(segment_data) > 0:
                csv_path = output_dir / f"{market_id}_{segment}_segment.csv"
                segment_data.to_csv(csv_path, index=False)
                print(f"    Saved {segment}: {len(segment_data)} rows")
        
        # Step 8: Plot
        print(f"  Step 8: Creating plots...")
        plot_path = output_dir / f"{market_id}_odds_comparison.png"
        plot_odds_comparison(aggregated, price_odds, plot_path, market_id)
        print(f"    Saved plots: {plot_path.stem}_*.png")
        
        print(f"  Completed market {market_id}")
    except Exception as e:
        print(f"  Error processing market {market_id}: {e}")
        import traceback
        traceback.print_exc()
        return


def main():
    """Main entry point."""
    # Paths
    trades_base = SCRIPT_DIR.parent / "Trades"
    output_base = SCRIPT_DIR.parent / "trades_Plot"
    
    # Look for all_users_analysis.csv in repo root or per_market_analysis/
    segments_paths = [
        REPO_ROOT / "all_users_analysis.csv",
        SCRIPT_DIR.parent / "all_users_analysis.csv"
    ]
    segments_dict = {}
    for path in segments_paths:
        if path.exists():
            segments_dict = load_user_segments(path)
            print(f"Loaded {len(segments_dict)} user segments from {path}")
            break
    
    if len(segments_dict) == 0:
        print("Warning: No user segments file found. Will only compute 'all_users' aggregate.")
    
    # Iterate over event folders
    if not trades_base.exists():
        print(f"Error: Trades directory not found: {trades_base}")
        return
    
    for event_dir in sorted(trades_base.iterdir()):
        if not event_dir.is_dir():
            continue
        
        event_id = event_dir.name
        print(f"\nProcessing event: {event_id}")
        
        # Create output directory
        event_output_dir = output_base / event_id
        event_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load polymarket prices for this event
        prices_path = SCRIPT_DIR.parent / event_id / "polymarket_prices.csv"
        
        # Process each trades CSV
        for trades_file in sorted(event_dir.glob("*_trades.csv")):
            # Extract market_id from filename (e.g., "500614_trades.csv" -> "500614")
            market_id = trades_file.stem.replace("_trades", "")
            
            process_market(
                trades_csv_path=trades_file,
                market_id=market_id,
                event_id=event_id,
                segments_dict=segments_dict,
                prices_csv_path=prices_path,
                output_dir=event_output_dir
            )
    
    print("\nAll markets processed!")


if __name__ == "__main__":
    main()
