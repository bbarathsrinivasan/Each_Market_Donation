#!/usr/bin/env python3
"""
Run Summary analysis for all events: produce 4-line combined graphs (daily, weekly, monthly)
per slug. Loads event slugs from event_slugs.json; requires donation cumulative/non-cumulative
outputs and optionally trades_Plot all_users segment.

Run from repo root: python -m per_market_analysis.Summary_analysis.run_summary_analysis
Or: cd per_market_analysis/Summary_analysis && python run_summary_analysis.py (repo root on PYTHONPATH)
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PER_MARKET = SCRIPT_DIR.parent
REPO_ROOT = PER_MARKET.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_event_slugs() -> list[str]:
    """Load event slugs from event_slugs.json (or event_slugs.txt) in per_market_analysis."""
    txt_path = PER_MARKET / "event_slugs.txt"
    json_path = PER_MARKET / "event_slugs.json"
    if json_path.exists():
        with open(json_path) as f:
            data = json.load(f)
        slugs: list[str] = []
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
    slugs = load_event_slugs()
    if not slugs:
        print("No event slugs found. Add slugs to event_slugs.json or event_slugs.txt")
        sys.exit(1)

    try:
        from per_market_analysis.Summary_analysis.build_summary_plots import plot_summary_one_frequency
    except ImportError:
        from build_summary_plots import plot_summary_one_frequency

    trades_plot_base = PER_MARKET / "trades_Plot"
    output_base = SCRIPT_DIR / "output"

    print("=" * 80)
    print("SUMMARY ANALYSIS — 4-line graphs (daily, weekly, monthly) per event")
    print("=" * 80)
    print(f"Events: {slugs}")
    print("=" * 80)

    for i, slug in enumerate(slugs, 1):
        slug_dir = PER_MARKET / slug
        print(f"\n[{i}/{len(slugs)}] {slug}")
        if not slug_dir.is_dir():
            print(f"  Skip: {slug_dir} not found")
            continue
        for freq in ["daily", "weekly", "monthly"]:
            out_path = output_base / slug / f"summary_{freq}.png"
            try:
                plot_summary_one_frequency(
                    slug_dir=slug_dir,
                    slug=slug,
                    freq=freq,
                    trades_plot_base=trades_plot_base,
                    output_path=out_path,
                )
            except Exception as e:
                print(f"  Error {freq}: {e}")

    print("\n" + "=" * 80)
    print("Summary analysis complete.")
    print("=" * 80)


if __name__ == "__main__":
    main()
