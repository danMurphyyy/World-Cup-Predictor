"""Blend Elo cross-confederation calibration into Dixon-Coles goal expectations.

Dixon-Coles attack/defence ratings are biased by who a team plays (CONMEBOL sides
look stronger than they are because of high-scoring intra-confederation
qualifiers). Elo, being zero-sum and updated on actual results, calibrates better
across confederations. We keep DC's match goal *total* but blend the goal
*supremacy* (home minus away) with the Elo-implied supremacy.
"""
from __future__ import annotations

from backend.model.dixon_coles import DixonColesModel, outcome_probabilities, scoreline_matrix
from backend.model.elo import EloModel

# Calibrated on a temporal back-test (fit <2023, scored 2023-2026): w=0.5,
# goal_scale=200 minimised log-loss (0.8640 vs 0.8712 DC-only). See backtest.py.
BLEND_W = 0.5         # weight on the Elo-implied supremacy vs DC's
GOAL_SCALE = 200.0    # Elo points per goal of supremacy
MIN_LAMBDA = 0.05


def blend_expected_goals(lam_home: float, lam_away: float, elo_diff: float,
                         w: float = BLEND_W, goal_scale: float = GOAL_SCALE) -> tuple[float, float]:
    """Blend DC goal supremacy with the Elo-implied supremacy, keeping the total."""
    total = lam_home + lam_away
    dc_gd = lam_home - lam_away
    elo_gd = elo_diff / goal_scale
    gd = (1 - w) * dc_gd + w * elo_gd
    lam_h = max(MIN_LAMBDA, (total + gd) / 2)
    lam_a = max(MIN_LAMBDA, (total - gd) / 2)
    return lam_h, lam_a


def predict_blended(elo: EloModel, dc: DixonColesModel, home: str, away: str,
                    neutral: bool = True, w: float = BLEND_W,
                    goal_scale: float = GOAL_SCALE, max_goals: int = 10) -> dict:
    """Match prediction using the Elo-blended expected goals."""
    lam_h0, lam_a0 = dc.expected_goals(home, away, neutral=neutral)
    elo_diff = elo.rating(home) - elo.rating(away)
    if not neutral:
        from backend.model.elo import HOME_ADVANTAGE
        elo_diff += HOME_ADVANTAGE
    lam_h, lam_a = blend_expected_goals(lam_h0, lam_a0, elo_diff, w, goal_scale)
    matrix = scoreline_matrix(lam_h, lam_a, dc.rho, max_goals)
    p_home, p_draw, p_away = outcome_probabilities(matrix)
    return {
        "home": home, "away": away, "neutral": neutral,
        "xg_home": lam_h, "xg_away": lam_a,
        "prob_home": p_home, "prob_draw": p_draw, "prob_away": p_away,
    }
