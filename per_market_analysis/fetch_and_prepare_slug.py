#!/usr/bin/env python3
"""
For a given event slug: fetch Polymarket event, infer candidates, filter donations
by candidate (chunked), save donations_filtered.csv; fetch price history and save
polymarket_metadata.json and polymarket_prices.csv.
"""

from pathlib import Path
from typing import Any
import json
import pandas as pd

from .candidate_matching import infer_candidates_for_event
from .polymarket_client import (
    fetch_all_price_histories,
    fetch_event_by_slug,
    save_event_metadata,
)


SCRIPT_DIR = Path(__file__).resolve().parent


def parse_date(date_str):
    """Parse date from MMDDYYYY format (same as cumulative_ratio_analysis)."""
    if pd.isna(date_str):
        return pd.NaT
    try:
        date_str = str(int(date_str))
    except (ValueError, TypeError):
        return pd.NaT
    if len(date_str) < 7:
        return pd.NaT
    try:
        if len(date_str) == 8:
            month = int(date_str[:2])
            day = int(date_str[2:4])
            year = int(date_str[4:])
        elif len(date_str) == 7:
            month = int(date_str[0])
            day = int(date_str[1:3])
            year = int(date_str[3:])
        else:
            return pd.NaT
        return pd.Timestamp(year=year, month=month, day=day)
    except Exception:
        return pd.NaT


def _reference_name_tokens(name: str) -> list[str]:
    """
    Tokenize a reference name for flexible matching. Case-insensitive.
    - Split on whitespace and punctuation.
    - Split 'McX' / 'MacX' into prefix + rest so 'McDermott' -> ['mc', 'dermott']
      and matches CSV 'MC DERMOTT' or 'MCDERMOTT'.
    """
    if not name or not isinstance(name, str):
        return []
    raw = name.strip().lower()
    tokens: list[str] = []
    for word in raw.replace(",", " ").split():
        word = "".join(c for c in word if c.isalnum() or c in ("-", "'"))
        if not word:
            continue
        # Mc / Mac prefix: "mcdermott" -> ["mc", "dermott"], "macarthur" -> ["mac", "arthur"]
        if word.startswith("mac") and len(word) > 3:
            tokens.extend([word[:3], word[3:]])
        elif word.startswith("mc") and len(word) > 2:
            tokens.extend([word[:2], word[2:]])
        else:
            tokens.append(word)
    return tokens


def _candidate_string_matches(csv_candidate: str, reference_name: str) -> bool:
    """
    Case-insensitive, order-independent match: True if every token from
    reference_name appears in csv_candidate. Handles Mc/Mac (e.g. 'Bob McDermott'
    matches 'MC DERMOTT, BOB' or 'MCDERMOTT, BOB').
    """
    if not csv_candidate or not reference_name:
        return False
    csv_lower = str(csv_candidate).strip().lower()
    tokens = _reference_name_tokens(reference_name)
    if not tokens:
        return False
    return all(t in csv_lower for t in tokens)


def filter_donations_by_candidates_chunked(
    donation_csv_path: Path,
    candidate_set: set[str],
    slug_dir: Path,
    chunk_size: int = 1_000_000,
) -> int:
    """
    Read US_Election_Donation.csv in chunks; keep rows where Candidate matches any
    name in candidate_set (case-insensitive, order-independent: e.g. "Ruben Gallego"
    matches "GALLEGO, RUBEN") and Party in DEM/REP. Write to slug_dir/donations_filtered.csv.
    Returns row count. If candidate_set is empty, writes empty CSV with header only.
    """
    slug_dir.mkdir(parents=True, exist_ok=True)
    out_file = slug_dir / "donations_filtered.csv"
    if not candidate_set:
        pd.DataFrame(columns=["Party", "Candidate", "Candidate_ID", "Donator", "Received",
                              "Donation_Amount_Original", "Donation_Amount_USD", "Election_Events", "Notes"]).to_csv(out_file, index=False)
        return 0
    total = 0
    first_chunk = True
    chunk_iter = pd.read_csv(donation_csv_path, chunksize=chunk_size, low_memory=False)
    for chunk in chunk_iter:
        chunk = chunk[chunk["Party"].isin(["DEM", "REP"])].copy()
        # Case-insensitive, order-independent match: "Ruben Gallego" matches "GALLEGO, RUBEN"
        def row_matches(val: str) -> bool:
            return any(_candidate_string_matches(val, c) for c in candidate_set)
        mask = chunk["Candidate"].astype(str).str.strip().apply(row_matches)
        chunk = chunk[mask].copy()
        if len(chunk) == 0:
            continue
        chunk.to_csv(
            out_file,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False,
        )
        total += len(chunk)
        first_chunk = False
    return total


def _point_to_row(point: Any, label: str) -> dict[str, Any] | None:
    """Extract (timestamp, price) from point: dict {t, p} or list [t, p]. Price in 0-1."""
    t, p = None, None
    if isinstance(point, dict):
        t, p = point.get("t"), point.get("p")
    elif isinstance(point, (list, tuple)) and len(point) >= 2:
        t, p = point[0], point[1]
    if t is None or p is None:
        return None
    if isinstance(p, (int, float)) and p > 1:
        p = float(p) / 10000.0  # basis points -> 0-1
    return {"timestamp": int(t), "outcome_label": label, "price": float(p)}


def save_polymarket_prices_csv(price_series: list[dict[str, Any]], out_path: Path) -> None:
    """
    Save list of {outcome_label, token_id, history: [{t, p}]} to CSV with columns
    timestamp, outcome_label, price. One row per (timestamp, outcome_label).
    Handles history items as object {t, p} or array [t, p]; normalizes price to 0-1.
    """
    rows = []
    for series in price_series:
        label = series.get("outcome_label", "unknown")
        if label == "No":
            continue
        for point in series.get("history") or []:
            row = _point_to_row(point, label)
            if row:
                rows.append(row)
    if not rows:
        pd.DataFrame(columns=["timestamp", "outcome_label", "price"]).to_csv(out_path, index=False)
        return
    df = pd.DataFrame(rows)
    df = df.sort_values(["outcome_label", "timestamp"])
    df.to_csv(out_path, index=False)


def load_explicit_candidates_for_slug(slug: str) -> list[str]:
    """
    Optional override: read event_slugs.json and, for the given slug, return
    explicit Democrat/Republican candidate names to use for donation filtering.

    Expected JSON shape:
    [
      {"slug": "arizona-us-senate-election-winner",
       "democrat": "GALLEGO, RUBEN",
       "republican": "LAKE, KARI"},
      ...
    ]
    """
    json_path = SCRIPT_DIR / "event_slugs.json"
    if not json_path.exists():
        return []
    try:
        with open(json_path) as f:
            data = json.load(f)
    except Exception:
        return []

    candidates: list[str] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        slug_value = item.get("slug") or item.get("event_slug")
        if not isinstance(slug_value, str) or slug_value.strip() != slug:
            continue
        dem = item.get("democrat")
        rep = item.get("republican")
        if isinstance(dem, str) and dem.strip():
            candidates.append(dem.strip())
        if isinstance(rep, str) and rep.strip():
            candidates.append(rep.strip())
        break
    return candidates


def run_fetch_and_prepare_for_slug(
    slug: str,
    slug_dir: Path,
    donation_csv_path: Path,
) -> tuple[dict[str, Any] | None, int]:
    """
    For one slug: fetch event, infer candidates, filter donations, fetch prices, save all.
    Returns (event_dict or None, count of filtered donation rows).
    """
    event = fetch_event_by_slug(slug)
    if event is None:
        return None, 0

    slug_dir.mkdir(parents=True, exist_ok=True)
    save_event_metadata(event, slug_dir / "polymarket_metadata.json")

    # Prefer explicit candidate names configured in event_slugs.json, if present.
    explicit_candidates = load_explicit_candidates_for_slug(slug)
    if explicit_candidates:
        candidates = explicit_candidates
        print(f"  Using explicit candidates from event_slugs.json for '{slug}': {candidates}")
    else:
        candidates = infer_candidates_for_event(event, donation_csv_path)
        if not candidates:
            print(f"  Warning: No candidates inferred for event '{slug}'; skipping donation filter.")
            candidate_set = set()
        else:
            candidate_set = set(c.strip() for c in candidates)
            print(f"  Matched candidates: {list(candidate_set)}")

    # If we set candidate_set inside the explicit branch, do it here in common code.
    if explicit_candidates:
        candidate_set = set(c.strip() for c in explicit_candidates)

    count = filter_donations_by_candidates_chunked(donation_csv_path, candidate_set, slug_dir)
    print(f"  Filtered donations: {count:,} rows -> {slug_dir / 'donations_filtered.csv'}")

    price_series = fetch_all_price_histories(event)
    save_polymarket_prices_csv(price_series, slug_dir / "polymarket_prices.csv")
    print(f"  Saved price series for {len(price_series)} outcome(s) -> polymarket_prices.csv")

    return event, count
