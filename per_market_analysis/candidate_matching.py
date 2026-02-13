#!/usr/bin/env python3
"""
Infer candidate names from Polymarket event (markets/outcomes) and match to
US_Election_Donation.csv Candidate column (format "LAST, FIRST").
"""

import re
from pathlib import Path
from typing import Any

import pandas as pd


def normalize_name(s: str) -> str:
    """Lowercase, strip punctuation and extra spaces."""
    if not s or not isinstance(s, str):
        return ""
    s = re.sub(r"[^\w\s]", "", s.lower()).strip()
    return " ".join(s.split())


def extract_last_name_from_csv_candidate(csv_candidate: str) -> str:
    """From 'LAST, FIRST' or 'LAST, FIRST MIDDLE' return normalized last name."""
    s = (csv_candidate or "").strip()
    if "," in s:
        part = s.split(",")[0].strip()
    else:
        part = s.split()[0] if s else ""
    return normalize_name(part)


def extract_candidate_tokens_from_group_item_titles(event: dict[str, Any]) -> list[str]:
    """
    Extract candidate names from each market's groupItemTitle (e.g. "Kari Lake", "Ruben Gallego").
    Returns list of normalized last-name tokens for matching to CSV "LAST, FIRST".
    Skips empty, "Other", and generic values.
    """
    skip = {"other", "others", "unknown", "none"}
    tokens = []
    seen = set()
    for m in event.get("markets") or []:
        title = (m.get("groupItemTitle") or "").strip()
        if not title or normalize_name(title) in skip:
            continue
        # "Kari Lake" -> last name "Lake" -> "lake"; "Ruben Gallego" -> "gallego"
        parts = title.split()
        if parts:
            last_name = normalize_name(parts[-1])
            if last_name and last_name not in seen and len(last_name) >= 2:
                seen.add(last_name)
                tokens.append(last_name)
    return tokens


def extract_candidate_tokens_from_event(event: dict[str, Any]) -> list[str]:
    """
    Extract candidate-like tokens from event title, market questions, and outcomes.
    Returns list of normalized tokens (e.g. 'trump', 'harris') for matching.
    """
    tokens = set()
    title = (event.get("title") or "").strip()
    if title:
        # Common pattern: "Presidential Election Winner 2024" or "Trump vs Harris"
        words = re.findall(r"\b[A-Za-z]{2,}\b", title)
        for w in words:
            w_lower = w.lower()
            if w_lower not in {"presidential", "election", "winner", "president", "will", "win", "the", "who", "2024", "2020"}:
                tokens.add(w_lower)
    markets = event.get("markets") or []
    for m in markets:
        question = (m.get("question") or "").strip()
        outcomes = m.get("outcomes")
        if isinstance(outcomes, str):
            outcomes = [o.strip() for o in outcomes.split(",")] if outcomes else []
        elif not isinstance(outcomes, list):
            outcomes = []
        # Outcome names like "Trump", "Harris"
        for o in outcomes:
            if o and isinstance(o, str) and len(o) > 1:
                tokens.add(normalize_name(o))
        # From question: "Will Trump win?" -> Trump
        if question:
            words = re.findall(r"\b[A-Za-z]{2,}\b", question)
            for w in words:
                w_lower = w.lower()
                if w_lower not in {"will", "win", "president", "election", "the", "who", "be", "become"}:
                    tokens.add(w_lower)
    return list(tokens)


def get_unique_candidates_from_csv(donation_csv_path: Path) -> pd.Series:
    """Read first chunk or sample to get unique Candidate values for matching."""
    # We need to match against all unique candidates; CSV is huge so sample or read in chunks and collect unique
    chunk_iter = pd.read_csv(donation_csv_path, chunksize=500_000, usecols=["Candidate"], low_memory=False)
    seen = set()
    for chunk in chunk_iter:
        for v in chunk["Candidate"].dropna().astype(str).unique():
            v = (v or "").strip()
            if v and v not in seen:
                seen.add(v)
        if len(seen) > 5000:  # cap to avoid huge set
            break
    return pd.Series(list(seen))


def match_tokens_to_csv_candidates(
    tokens: list[str], csv_candidates: pd.Series
) -> list[str]:
    """
    Match inferred tokens (e.g. 'trump', 'harris') to CSV Candidate values like 'TRUMP, DONALD'.
    Uses exact last-name match only (no substring/partial matches).
    Returns list of CSV Candidate strings to filter on.
    """
    if not tokens:
        return []
    csv_list = csv_candidates.dropna().astype(str).tolist()
    matched = []
    for cand in csv_list:
        cand = cand.strip()
        if not cand:
            continue
        last_norm = extract_last_name_from_csv_candidate(cand)
        if not last_norm:
            continue
        for t in tokens:
            if last_norm == t:
                matched.append(cand)
                break
    return list(dict.fromkeys(matched))  # preserve order, no dupes


def infer_candidates_for_event(
    event: dict[str, Any], donation_csv_path: Path
) -> list[str]:
    """
    Infer candidate names from Polymarket event and return list of CSV Candidate
    values to use for filtering US_Election_Donation.csv.
    Prefers groupItemTitle from each market (e.g. "Kari Lake"); falls back to
    event title, questions, and outcomes if no groupItemTitle candidates are found.
    """
    # Prefer groupItemTitle from metadata (canonical candidate names per market)
    tokens = extract_candidate_tokens_from_group_item_titles(event)
    if not tokens:
        tokens = extract_candidate_tokens_from_event(event)
    if not tokens:
        return []
    unique_candidates = get_unique_candidates_from_csv(donation_csv_path)
    return match_tokens_to_csv_candidates(tokens, unique_candidates)
