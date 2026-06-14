"""Temporal back-test to calibrate the Elo blend.

Fit Elo + Dixon-Coles strictly on matches before a cutoff, then score W/D/L
predictions on matches after it by log-loss. Lower is better. Comparing blend
weights tells us, on held-out data, how much Elo correction actually helps.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backend.data.store import results
from backend.model.blend import blend_expected_goals
from backend.model.dixon_coles import DixonColesModel, outcome_probabilities, scoreline_matrix
from backend.model.elo import HOME_ADVANTAGE, EloModel
from backend.model.strength import DC_CUTOFF, recency_weight

EPS = 1e-15
_COLS = ["home_team", "away_team", "home_score", "away_score", "neutral", "tournament"]


def fit_until(df: pd.DataFrame, cutoff: pd.Timestamp) -> tuple[EloModel, DixonColesModel]:
    train = df[df["date"] < cutoff]
    elo = EloModel.fit(train[_COLS].to_dict("records"))
    dc_train = train[train["date"] >= DC_CUTOFF].copy()
    dc_train["weight"] = recency_weight((cutoff - dc_train["date"]).dt.days.to_numpy())
    dc = DixonColesModel.fit(
        dc_train[["home_team", "away_team", "home_score", "away_score", "neutral", "weight"]]
        .to_dict("records")
    )
    return elo, dc


def log_loss(elo: EloModel, dc: DixonColesModel, test: pd.DataFrame,
             w: float, goal_scale: float) -> tuple[float, int]:
    total, n = 0.0, 0
    for m in test.itertuples():
        if m.home_team not in dc.attack or m.away_team not in dc.attack:
            continue
        lh0, la0 = dc.expected_goals(m.home_team, m.away_team, neutral=m.neutral)
        elo_diff = elo.rating(m.home_team) - elo.rating(m.away_team)
        if not m.neutral:
            elo_diff += HOME_ADVANTAGE
        lh, la = blend_expected_goals(lh0, la0, elo_diff, w, goal_scale)
        ph, pdr, pa = outcome_probabilities(scoreline_matrix(lh, la, dc.rho))
        if m.home_score > m.away_score:
            p = ph
        elif m.home_score < m.away_score:
            p = pa
        else:
            p = pdr
        total += -np.log(max(p, EPS))
        n += 1
    return total / n, n


def run(cutoff: str = "2023-01-01") -> None:
    df = results()
    cut = pd.Timestamp(cutoff)
    elo, dc = fit_until(df, cut)
    test = df[df["date"] >= cut]
    print(f"Train < {cutoff}; test {test['date'].min().date()}..{test['date'].max().date()}")

    best = None
    for scale in (200.0, 250.0, 300.0, 400.0):
        for w in (0.0, 0.25, 0.5, 0.75, 1.0):
            ll, n = log_loss(elo, dc, test, w, scale)
            tag = " (DC-only)" if w == 0 else ""
            print(f"  w={w:.2f} scale={scale:.0f}  log-loss={ll:.4f}  (n={n}){tag}")
            if best is None or ll < best[0]:
                best = (ll, w, scale)
        print()
    print(f"BEST: log-loss={best[0]:.4f} at w={best[1]}, goal_scale={best[2]}")


if __name__ == "__main__":  # pragma: no cover
    run()
