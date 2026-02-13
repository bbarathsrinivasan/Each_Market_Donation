#!/usr/bin/env python3
"""
Polymarket API client: fetch event by slug and price history per token.
Uses Gamma API for event metadata and CLOB API for price history.
Price history uses market startDate as startTs, interval=max, fidelity=60 (no endTs).
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

GAMMA_EVENTS_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"
RATE_LIMIT_SLEEP = 0.5  # seconds between price-history calls


def iso_to_unix(iso: str | None) -> int | None:
    """Parse ISO8601 timestamp to Unix seconds. Handles Z and variable fractional seconds."""
    if not iso or not isinstance(iso, str):
        return None
    s = iso.strip().replace("Z", "+00:00")
    m = re.match(r"^(.*T\d{2}:\d{2}:\d{2})(?:\.(\d+))?(.*)$", s)
    if m:
        head, frac, tail = m.groups()
        if frac is not None:
            frac = frac[:6].ljust(6, "0") if len(frac) > 6 else frac.ljust(6, "0")
            s = f"{head}.{frac}{tail}"
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except (ValueError, TypeError):
        return None


def fetch_event_by_slug(slug: str) -> dict[str, Any] | None:
    """Fetch event metadata by slug from Gamma API."""
    url = f"{GAMMA_EVENTS_BASE}/events/slug/{slug}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"  ✗ Failed to fetch event '{slug}': {e}")
        return None


def _parse_clob_token_ids(clob_token_ids: Any) -> list[str]:
    """Parse clobTokenIds (JSON array string like '[\"id1\", \"id2\"]', or list) into list of token IDs."""
    if clob_token_ids is None:
        return []
    if isinstance(clob_token_ids, list):
        return [str(t).strip() for t in clob_token_ids if t]
    s = str(clob_token_ids).strip()
    if not s:
        return []
    # Gamma API often returns clobTokenIds as a JSON-encoded array string
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return [str(t).strip() for t in parsed if t]
    except (json.JSONDecodeError, TypeError):
        pass
    # Fallback: split by comma and strip quotes/brackets from each part
    ids = []
    for t in s.split(","):
        t = t.strip().strip('[]"').strip()
        if t:
            ids.append(t)
    return ids


def _normalize_history_point(point: Any) -> dict[str, float] | None:
    """Normalize API point to {t, p} with p in 0-1. Handles object {t,p} or array [t,p]."""
    t, p = None, None
    if isinstance(point, dict):
        t, p = point.get("t"), point.get("p")
    elif isinstance(point, (list, tuple)) and len(point) >= 2:
        t, p = point[0], point[1]
    if t is None or p is None:
        return None
    # CLOB API may return price in basis points (0-10000) -> convert to 0-1
    if p > 1:
        p = float(p) / 10000.0
    return {"t": int(t), "p": float(p)}


def fetch_price_history(
    token_id: str,
    start_ts: int | None = None,
    interval: str = "max",
    fidelity: int = 60,
) -> list[dict[str, float]] | None:
    """
    Fetch price history for a CLOB token. Returns list of {t: unix_ts, p: price in 0-1}.
    Use market startDate as start_ts (with interval=max, fidelity=60) per Polymarket CLOB behavior.
    """
    url = f"{CLOB_BASE}/prices-history"
    params = {"market": token_id, "interval": interval, "fidelity": fidelity}
    if start_ts is not None:
        params["startTs"] = start_ts
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        raw = data.get("history") or []
        out = []
        for point in raw:
            norm = _normalize_history_point(point)
            if norm:
                out.append(norm)
        return out
    except requests.RequestException as e:
        print(f"  ✗ Failed to fetch price history for token {token_id[:20]}...: {e}")
        return None


def get_markets_with_tokens(event: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract markets with parsed token IDs, outcome labels, and start_ts from market dates.
    Each item: {question, outcomes, token_ids, outcome_labels, start_ts}.
    outcome_labels: prefer groupItemTitle for binary markets; else outcomes or Yes/No.
    """
    markets = event.get("markets") or []
    result = []
    for m in markets:
        token_ids = _parse_clob_token_ids(m.get("clobTokenIds"))
        if not token_ids:
            continue
        # Market time window: startTs from startDate/createdAt (required by CLOB for price-history)
        start_iso = m.get("startDate") or m.get("createdAt")
        start_ts = iso_to_unix(start_iso) if start_iso else None
        outcomes = m.get("outcomes")
        if isinstance(outcomes, str):
            outcomes = [o.strip() for o in outcomes.split(",")] if outcomes else []
        elif not isinstance(outcomes, list):
            outcomes = []
        # Prefer groupItemTitle for binary (e.g. "Kari Lake", "Ruben Gallego"); else outcomes/Yes-No
        group_title = (m.get("groupItemTitle") or "").strip()
        if group_title and len(token_ids) == 2:
            outcome_labels = [group_title, "No"][:2]  # Yes/No -> groupItemTitle, No
        elif len(outcomes) >= len(token_ids):
            outcome_labels = outcomes[: len(token_ids)]
        elif len(token_ids) == 2:
            question = (m.get("question") or "").strip()
            outcome_labels = [question or "Yes", "No"][:2]
        else:
            outcome_labels = [f"Outcome_{i}" for i in range(len(token_ids))]
        result.append(
            {
                "question": m.get("question") or "",
                "outcomes": outcomes,
                "outcome_prices": m.get("outcomePrices"),
                "token_ids": token_ids,
                "outcome_labels": outcome_labels,
                "start_ts": start_ts,
            }
        )
    return result


def fetch_all_price_histories(event: dict[str, Any]) -> list[dict[str, Any]]:
    """
    For each market token, fetch price history. Return list of
    {outcome_label, token_id, history: [{t, p}, ...]}.
    Uses market startDate as startTs with interval=max and fidelity=60 (per Polymarket CLOB).
    """
    markets_with_tokens = get_markets_with_tokens(event)
    all_series = []
    for m in markets_with_tokens:
        start_ts = m.get("start_ts")
        for token_id, label in zip(m["token_ids"], m["outcome_labels"]):
            if label == "No":
                continue
            time.sleep(RATE_LIMIT_SLEEP)
            history = fetch_price_history(token_id, start_ts=start_ts, interval="max", fidelity=60)
            if history is not None:
                all_series.append({"outcome_label": label, "token_id": token_id, "history": history})
    return all_series


def save_event_metadata(event: dict[str, Any], out_path: Path) -> None:
    """Save event JSON to file (full or trimmed)."""
    # Save full event for reference; can be large
    with open(out_path, "w") as f:
        json.dump(event, f, indent=2)


def load_event_metadata(path: Path) -> dict[str, Any] | None:
    """Load event JSON from file."""
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)
