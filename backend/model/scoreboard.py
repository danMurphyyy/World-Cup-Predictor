"""Live "Model vs Reality" scoreboard for the 2026 World Cup.

A pre-tournament model is locked by fitting Elo + Dixon-Coles strictly on data
*before* the first World Cup match (no leakage). Its predictions are then scored
against each real result as it arrives in the dataset — log-loss, Brier, and pick
accuracy, against a naive base-rate baseline. The data refreshes on a TTL, so the
board updates itself as matches are played.
"""
from __future__ import annotations

import math
import pickle

import pandas as pd

from backend.config import CACHE_DIR
from backend.data.ingest import load_results
from backend.model.backtest import fit_until
from backend.model.blend import predict_blended
from backend.model.dixon_coles import DixonColesModel
from backend.model.elo import EloModel

WC = "FIFA World Cup"
LOCKED_CACHE = CACHE_DIR / "locked_models.pkl"
REFRESH_HOURS = 6.0
EPS = 1e-15
_IDX = {"H": 0, "D": 1, "A": 2}


# --- Pure scoring helpers (unit-tested) ----------------------------------------

def outcome_from_score(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "H"
    if home_score < away_score:
        return "A"
    return "D"


def log_loss_one(probs: tuple[float, float, float], outcome: str) -> float:
    return -math.log(max(probs[_IDX[outcome]], EPS))


def brier_one(probs: tuple[float, float, float], outcome: str) -> float:
    y = {"H": (1, 0, 0), "D": (0, 1, 0), "A": (0, 0, 1)}[outcome]
    return sum((p - yi) ** 2 for p, yi in zip(probs, y))


def correct_pick(probs: tuple[float, float, float], outcome: str) -> bool:
    pick = max(range(3), key=lambda i: probs[i])
    return ["H", "D", "A"][pick] == outcome


# --- Locked pre-tournament model -----------------------------------------------

def _tournament_start(df: pd.DataFrame) -> pd.Timestamp:
    wc26 = df[(df["tournament"] == WC) & (df["date"] >= pd.Timestamp("2026-01-01"))]
    return wc26["date"].min()


def get_locked_models(df: pd.DataFrame) -> tuple[EloModel, DixonColesModel, pd.Timestamp]:
    """Elo + DC fit only on pre-tournament data (cached; cutoff never moves)."""
    if LOCKED_CACHE.exists():
        p = pickle.loads(LOCKED_CACHE.read_bytes())
        return EloModel(p["elo"]), DixonColesModel(**p["dc"]), pd.Timestamp(p["start"])
    start = _tournament_start(df)
    elo, dc = fit_until(df, start)
    LOCKED_CACHE.write_bytes(pickle.dumps({
        "elo": elo.ratings,
        "dc": {"attack": dc.attack, "defence": dc.defence, "home_adv": dc.home_adv, "rho": dc.rho},
        "start": start.isoformat(),
    }))
    return elo, dc, start


def _base_rates(hist: pd.DataFrame) -> tuple[float, float, float]:
    """Naive baseline: historical World Cup outcome frequencies (home/draw/away)."""
    if hist.empty:
        return (1 / 3, 1 / 3, 1 / 3)
    n = len(hist)
    h = (hist["result"] == "H").sum() / n
    d = (hist["result"] == "D").sum() / n
    return (h, d, 1 - h - d)


# --- Build the scoreboard ------------------------------------------------------

def build_scoreboard() -> dict:
    df = load_results(max_age_hours=REFRESH_HOURS)
    elo, dc, start = get_locked_models(df)
    played = df[(df["tournament"] == WC) & (df["date"] >= start)].sort_values("date")
    baseline = _base_rates(df[(df["tournament"] == WC) & (df["date"] < start)])

    matches = []
    m_ll = m_br = b_ll = b_br = 0.0
    correct = 0
    for r in played.itertuples():
        outcome = outcome_from_score(r.home_score, r.away_score)
        pred = predict_blended(elo, dc, r.home_team, r.away_team, neutral=bool(r.neutral))
        probs = (pred["prob_home"], pred["prob_draw"], pred["prob_away"])
        m_ll += log_loss_one(probs, outcome)
        m_br += brier_one(probs, outcome)
        b_ll += log_loss_one(baseline, outcome)
        b_br += brier_one(baseline, outcome)
        hit = correct_pick(probs, outcome)
        correct += hit
        matches.append({
            "date": r.date.date().isoformat(),
            "home": r.home_team, "away": r.away_team,
            "home_score": int(r.home_score), "away_score": int(r.away_score),
            "outcome": outcome,
            "prob_home": probs[0], "prob_draw": probs[1], "prob_away": probs[2],
            "xg_home": pred["xg_home"], "xg_away": pred["xg_away"],
            "prob_actual": probs[_IDX[outcome]],
            "hit": hit,
        })

    n = len(played)
    return {
        "n": n,
        "tournament_start": start.date().isoformat() if n or pd.notna(start) else None,
        "model_log_loss": m_ll / n if n else None,
        "baseline_log_loss": b_ll / n if n else None,
        "model_brier": m_br / n if n else None,
        "baseline_brier": b_br / n if n else None,
        "pick_accuracy": correct / n if n else None,
        "matches": list(reversed(matches)),  # newest first
    }


if __name__ == "__main__":  # pragma: no cover
    sb = build_scoreboard()
    print(f"Scored {sb['n']} WC matches since {sb['tournament_start']}")
    print(f"  model log-loss {sb['model_log_loss']:.3f} vs baseline {sb['baseline_log_loss']:.3f}")
    print(f"  pick accuracy  {sb['pick_accuracy']:.0%}")
    for m in sb["matches"][:6]:
        mark = "OK " if m["hit"] else " X "
        print(f"  [{mark}] {m['home']} {m['home_score']}-{m['away_score']} {m['away']}"
              f"  (model gave {m['prob_actual']:.0%} to result)")
