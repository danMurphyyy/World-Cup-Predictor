"""Fit Elo + Dixon-Coles on the historical results and cache the parameters.

Elo runs over the full match history (cheap, chronological). Dixon-Coles is fit
on recent matches with exponential recency weights, since old form is noise for
predicting today's teams. Fitted parameters are pickled so the API loads them
instantly instead of refitting per request.
"""
from __future__ import annotations

import pickle
from datetime import datetime

import pandas as pd

from backend.config import CACHE_DIR, TIME_DECAY_HALFLIFE_DAYS
from backend.data.store import results
from backend.model.dixon_coles import DixonColesModel
from backend.model.elo import EloModel

# Dixon-Coles is fit on matches from this date onward (recent form only).
DC_CUTOFF = pd.Timestamp("2011-01-01")
CACHE_FILE = CACHE_DIR / "models.pkl"

_CACHED: tuple[EloModel, DixonColesModel] | None = None


def recency_weight(age_days, halflife_days: float = TIME_DECAY_HALFLIFE_DAYS):
    """Exponential decay weight: 1.0 at age 0, 0.5 at one half-life."""
    return 0.5 ** (age_days / halflife_days)


def build_models() -> tuple[EloModel, DixonColesModel]:
    """Fit both models from the historical dataset (no caching)."""
    df = results()

    elo_rows = df[
        ["home_team", "away_team", "home_score", "away_score", "neutral", "tournament"]
    ].to_dict("records")
    elo = EloModel.fit(elo_rows)

    recent = df[df["date"] >= DC_CUTOFF].copy()
    now = df["date"].max()
    recent["weight"] = recency_weight((now - recent["date"]).dt.days.to_numpy())
    dc_rows = recent[
        ["home_team", "away_team", "home_score", "away_score", "neutral", "weight"]
    ].to_dict("records")
    dc = DixonColesModel.fit(dc_rows)
    return elo, dc


def save_models(elo: EloModel, dc: DixonColesModel) -> None:
    payload = {
        "elo": elo.ratings,
        "dc": {"attack": dc.attack, "defence": dc.defence,
               "home_adv": dc.home_adv, "rho": dc.rho},
        "built_at": datetime.utcnow().isoformat(),
    }
    CACHE_FILE.write_bytes(pickle.dumps(payload))


def get_models(rebuild: bool = False) -> tuple[EloModel, DixonColesModel]:
    """Return cached (Elo, Dixon-Coles), building + caching on first use."""
    global _CACHED
    if _CACHED is not None and not rebuild:
        return _CACHED
    if CACHE_FILE.exists() and not rebuild:
        p = pickle.loads(CACHE_FILE.read_bytes())
        elo = EloModel(ratings=p["elo"])
        dc = DixonColesModel(**p["dc"])
    else:
        elo, dc = build_models()
        save_models(elo, dc)
    _CACHED = (elo, dc)
    return _CACHED


if __name__ == "__main__":  # pragma: no cover - manual sanity check
    import time
    t0 = time.time()
    elo, dc = build_models()
    save_models(elo, dc)
    print(f"Fit in {time.time() - t0:.1f}s")
    top = sorted(elo.ratings.items(), key=lambda kv: -kv[1])[:10]
    print("Top 10 by Elo:")
    for team, r in top:
        print(f"  {team:20s} {r:7.1f}  (DC attack {dc.attack.get(team, 0):+.2f})")
    print("\nBrazil vs Argentina (neutral):")
    pred = dc.predict("Brazil", "Argentina", neutral=True)
    print(f"  xG {pred['xg_home']:.2f}-{pred['xg_away']:.2f}  "
          f"W/D/L {pred['prob_home']:.0%}/{pred['prob_draw']:.0%}/{pred['prob_away']:.0%}")
