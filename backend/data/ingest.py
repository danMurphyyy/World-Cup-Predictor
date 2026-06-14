"""Ingest raw football data into the local cache.

Historical international results come from the martj42/international_results
dataset (CC0), served raw from GitHub: no API key and no rate limit, so it is
the dependable backbone for ratings, strengths and head-to-head edges.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

from backend.config import CACHE_DIR, HISTORICAL_RESULTS_URL

RESULTS_CACHE = CACHE_DIR / "results.csv"

EXPECTED_COLUMNS = {
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "tournament",
    "city",
    "country",
    "neutral",
}


def download_results(force: bool = False) -> Path:
    """Download the historical results CSV to the cache, returning its path.

    Skips the network call if a cached copy already exists, unless ``force``.
    """
    if RESULTS_CACHE.exists() and not force:
        return RESULTS_CACHE

    resp = requests.get(HISTORICAL_RESULTS_URL, timeout=60)
    resp.raise_for_status()
    RESULTS_CACHE.write_bytes(resp.content)
    return RESULTS_CACHE


def load_results(force_download: bool = False) -> pd.DataFrame:
    """Load and clean the historical results into a typed DataFrame."""
    path = download_results(force=force_download)
    df = pd.read_csv(path, parse_dates=["date"])

    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Results CSV missing expected columns: {sorted(missing)}")

    # Drop rows without a final score (future/abandoned fixtures in the source).
    df = df.dropna(subset=["home_score", "away_score"]).copy()
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    df["neutral"] = df["neutral"].astype(bool)

    # Outcome from the home team's perspective: 'H', 'D', or 'A'.
    df["result"] = "D"
    df.loc[df["home_score"] > df["away_score"], "result"] = "H"
    df.loc[df["home_score"] < df["away_score"], "result"] = "A"

    return df.sort_values("date").reset_index(drop=True)


if __name__ == "__main__":  # pragma: no cover - manual smoke check
    frame = load_results()
    print(f"Loaded {len(frame):,} matches "
          f"({frame['date'].min().date()} to {frame['date'].max().date()})")
    print(f"Distinct teams: {pd.concat([frame['home_team'], frame['away_team']]).nunique()}")
