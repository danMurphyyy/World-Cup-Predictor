"""Per-confederation strength offsets to correct cross-confederation bias.

The blended Elo/Dixon-Coles model over-rates some confederations and under-rates
others when they meet (measured in diagnose_confed.py). We fit one goal-supremacy
offset per confederation by maximum likelihood on historical cross-confederation
matches, then shift expected goals by (offset_home - offset_away) whenever two
teams from different confederations play. Same-confederation matches are
untouched (the bias is purely cross-confederation).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from backend.data.confederations import confederation_of
from backend.model.dixon_coles import outcome_probabilities, scoreline_matrix
from backend.model.elo import HOME_ADVANTAGE
from backend.model.strength import recency_weight
# NOTE: blend is imported lazily inside the fitter to avoid a circular import
# (blend.py imports confed_adjust from this module).

REF = "CONCACAF"            # reference confederation, offset fixed at 0
FREE = ["UEFA", "CONMEBOL", "CAF", "AFC", "OFC"]
MIN_LAMBDA = 0.05

# Fitted by MLE on cross-confederation matches since 2002 (see fit_offsets).
# Validated out-of-sample: improves 2023+ cross-confed log-loss 0.912 -> 0.898.
CONFED_OFFSET: dict[str, float] = {
    "CAF": 0.449, "UEFA": 0.376, "AFC": 0.070, "CONMEBOL": 0.059,
    "CONCACAF": 0.0, "OFC": -0.602,
}


def confed_adjust(lam_home: float, lam_away: float, home: str, away: str,
                  offsets: dict[str, float] | None = None) -> tuple[float, float]:
    """Shift expected goals by the confederation offset gap (cross-confed only)."""
    off = offsets if offsets is not None else CONFED_OFFSET
    ch, ca = confederation_of(home), confederation_of(away)
    if ch is None or ca is None or ch == ca:
        return lam_home, lam_away
    delta = off.get(ch, 0.0) - off.get(ca, 0.0)
    total = lam_home + lam_away
    gd = (lam_home - lam_away) + delta
    return max(MIN_LAMBDA, (total + gd) / 2), max(MIN_LAMBDA, (total - gd) / 2)


def _cross_confed_rows(elo, dc, df: pd.DataFrame) -> list[tuple]:
    """(lam_h0, lam_a0, confed_h, confed_a, outcome, weight) per usable match."""
    from backend.model.blend import blend_expected_goals  # lazy: avoid import cycle
    now = df["date"].max()
    rows = []
    for m in df.itertuples():
        ch, ca = confederation_of(m.home_team), confederation_of(m.away_team)
        if ch is None or ca is None or ch == ca:
            continue
        if m.home_team not in dc.attack or m.away_team not in dc.attack:
            continue
        lh0, la0 = dc.expected_goals(m.home_team, m.away_team, neutral=bool(m.neutral))
        ediff = elo.rating(m.home_team) - elo.rating(m.away_team)
        if not m.neutral:
            ediff += HOME_ADVANTAGE
        lh0, la0 = blend_expected_goals(lh0, la0, ediff)
        outcome = "H" if m.home_score > m.away_score else ("A" if m.home_score < m.away_score else "D")
        w = recency_weight((now - m.date).days)
        rows.append((lh0, la0, ch, ca, outcome, w))
    return rows


def fit_offsets(elo, dc, df: pd.DataFrame, since: str = "2002-01-01") -> dict[str, float]:
    rows = _cross_confed_rows(elo, dc, df[df["date"] >= pd.Timestamp(since)])
    rho = dc.rho

    def nll(x: np.ndarray) -> float:
        off = dict(zip(FREE, x)) | {REF: 0.0}
        total = 0.0
        for lh0, la0, ch, ca, outcome, w in rows:
            delta = off[ch] - off[ca]
            t = lh0 + la0
            gd = (lh0 - la0) + delta
            lh = max(MIN_LAMBDA, (t + gd) / 2)
            la = max(MIN_LAMBDA, (t - gd) / 2)
            ph, pd_, pa = outcome_probabilities(scoreline_matrix(lh, la, rho, 8))
            p = ph if outcome == "H" else (pd_ if outcome == "D" else pa)
            total += -w * math.log(max(p, 1e-12))
        return total

    res = minimize(nll, np.zeros(len(FREE)), method="L-BFGS-B",
                   bounds=[(-1.0, 1.0)] * len(FREE))
    fitted = dict(zip(FREE, res.x)) | {REF: 0.0}
    return {k: round(float(v), 3) for k, v in fitted.items()}


def _mean_log_loss(rows, offsets, rho) -> float:
    total, n = 0.0, 0
    for lh0, la0, ch, ca, outcome, _w in rows:
        delta = offsets.get(ch, 0.0) - offsets.get(ca, 0.0)
        t = lh0 + la0
        gd = (lh0 - la0) + delta
        lh = max(MIN_LAMBDA, (t + gd) / 2)
        la = max(MIN_LAMBDA, (t - gd) / 2)
        ph, pd_, pa = outcome_probabilities(scoreline_matrix(lh, la, rho, 8))
        p = ph if outcome == "H" else (pd_ if outcome == "D" else pa)
        total += -math.log(max(p, 1e-12))
        n += 1
    return total / n


if __name__ == "__main__":  # pragma: no cover
    from backend.data.store import results
    from backend.model.strength import get_models

    elo, dc = get_models()
    df = results()

    # Temporal validation: fit pre-2023, score 2023+ cross-confederation matches.
    cut = pd.Timestamp("2023-01-01")
    train_off = fit_offsets(elo, dc, df[df["date"] < cut])
    test_rows = _cross_confed_rows(elo, dc, df[df["date"] >= cut])
    zero = {k: 0.0 for k in train_off}
    print(f"Out-of-sample (2023+ cross-confed, n={len(test_rows)}):")
    print(f"  no offsets:     log-loss {_mean_log_loss(test_rows, zero, dc.rho):.4f}")
    print(f"  fitted offsets: log-loss {_mean_log_loss(test_rows, train_off, dc.rho):.4f}")

    offsets = fit_offsets(elo, dc, df)
    print("\nProduction offsets (fit on all history since 2002):")
    for k, v in sorted(offsets.items(), key=lambda kv: -kv[1]):
        print(f"  {k:10} {v:+.3f}")
