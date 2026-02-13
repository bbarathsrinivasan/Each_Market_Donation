#!/usr/bin/env python3
"""
Master orchestration for per-market donation + Polymarket analysis.
Loads event slugs from event_slugs.txt or event_slugs.json; for each slug:
  1. Fetch Polymarket event, infer candidates, filter donations, save metadata and prices
  2. Compute weekly/monthly cumulative donation ratio (All donors)
  3. Plot donation ratio + Polymarket price(s) on same 0-1 axis

Run from repo root: python -m per_market_analysis.run_per_market_analysis
Or from per_market_analysis/: python run_per_market_analysis.py (repo root must be on PYTHONPATH)
"""

import json
import sys
from pathlib import Path

# Allow running from repo root or from per_market_analysis/
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_event_slugs() -> list[str]:
    """Load event slugs from event_slugs.txt or event_slugs.json in script dir."""
    txt_path = SCRIPT_DIR / "event_slugs.txt"
    json_path = SCRIPT_DIR / "event_slugs.json"
    if json_path.exists():
        with open(json_path) as f:
            data = json.load(f)
        slugs: list[str] = []
        # Support both simple ["slug1", "slug2"] and
        # [{"slug": "slug1", "democrat": "...", "republican": "..."}, ...]
        for item in data:
            if isinstance(item, str) and item.strip():
                slugs.append(item.strip())
            elif isinstance(item, dict):
                slug = item.get("slug") or item.get("event_slug")
                if isinstance(slug, str) and slug.strip():
                    slugs.append(slug.strip())
        return slugs
    if txt_path.exists():
        slugs = []
        with open(txt_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    slugs.append(line)
        return slugs
    return []


def main() -> None:
    donation_csv = REPO_ROOT / "US_Election_Donation.csv"
    if not donation_csv.exists():
        print(f"✗ Not found: {donation_csv}")
        sys.exit(1)

    slugs = load_event_slugs()
    if not slugs:
        print("✗ No event slugs found. Add slugs to event_slugs.txt or event_slugs.json")
        sys.exit(1)

    print("=" * 80)
    print("PER-MARKET DONATION + POLYMARKET ANALYSIS")
    print("=" * 80)
    print(f"\nEvent slugs: {slugs}")
    print(f"Donation CSV: {donation_csv}")
    print("=" * 80)

    try:
        from per_market_analysis.fetch_and_prepare_slug import run_fetch_and_prepare_for_slug
        from per_market_analysis.prepare_cumulative_per_slug import run_prepare_cumulative_for_slug
        from per_market_analysis.plot_donation_and_polymarket import run_plots_for_slug
        from per_market_analysis.donation_analysis.segment_donors import segment_donors_for_slug
        from per_market_analysis.donation_analysis.prepare_cumulative_segments import prepare_cumulative_segments_for_slug
        from per_market_analysis.donation_analysis.plot_segments import plot_segments_for_slug
        from per_market_analysis.non_cumulative_donations.prepare_non_cumulative_segments import prepare_non_cumulative_segments_for_slug
        from per_market_analysis.non_cumulative_donations.plot_non_cumulative_segments import plot_non_cumulative_segments_for_slug
    except ImportError:
        from .fetch_and_prepare_slug import run_fetch_and_prepare_for_slug
        from .prepare_cumulative_per_slug import run_prepare_cumulative_for_slug
        from .plot_donation_and_polymarket import run_plots_for_slug
        from .donation_analysis.segment_donors import segment_donors_for_slug
        from .donation_analysis.prepare_cumulative_segments import prepare_cumulative_segments_for_slug
        from .donation_analysis.plot_segments import plot_segments_for_slug
        from .non_cumulative_donations.prepare_non_cumulative_segments import prepare_non_cumulative_segments_for_slug
        from .non_cumulative_donations.plot_non_cumulative_segments import plot_non_cumulative_segments_for_slug

    for i, slug in enumerate(slugs, 1):
        slug_dir = SCRIPT_DIR / slug
        print(f"\n[{i}/{len(slugs)}] Processing: {slug}")
        print("-" * 40)
        event, count = run_fetch_and_prepare_for_slug(slug, slug_dir, donation_csv)
        if event is None:
            print(f"  Skipping (event fetch failed).")
            continue
        if not run_prepare_cumulative_for_slug(slug_dir):
            print(f"  Skipping cumulative step.")
        segment_donors_for_slug(slug_dir)
        prepare_cumulative_segments_for_slug(slug_dir)
        run_plots_for_slug(slug, slug_dir)
        plot_segments_for_slug(slug_dir, slug)
        prepare_non_cumulative_segments_for_slug(slug_dir)
        plot_non_cumulative_segments_for_slug(slug_dir, slug)
    print("\n" + "=" * 80)
    print("✓ Per-market analysis complete.")
    print("=" * 80)


if __name__ == "__main__":
    main()
