"""Shared paths and configuration for the World Cup Predictor backend."""
from __future__ import annotations

from pathlib import Path

# backend/config.py -> backend/ -> project root
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
SEED_DIR = ROOT / "backend" / "data" / "seed"
DB_PATH = DATA_DIR / "store.db"

# Ensure regenerable dirs exist on import (cheap, idempotent).
for _d in (DATA_DIR, CACHE_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Historical international results — canonical community dataset (no auth, no rate limit).
HISTORICAL_RESULTS_URL = (
    "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
)

# Recency half-life (days) for Dixon-Coles time weighting. ~4 years.
TIME_DECAY_HALFLIFE_DAYS = 365 * 4

# Hosts of the 2026 World Cup (slight home advantage in the model).
HOST_NATIONS = {"United States", "Canada", "Mexico"}
