"""Dixon-Coles bivariate-Poisson model for football scorelines.

Each team has an attack and defence strength. Expected goals for a match are
``exp(attack_home + defence_away + home_adv)`` and ``exp(attack_away +
defence_home)``. A low-score correction term (rho) fixes the independent-Poisson
model's known bias on 0-0/1-0/0-1/1-1 results. Parameters are fit by weighted
maximum likelihood, with weights supplied per match (used for recency decay).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson


def _tau(home_goals, away_goals, lam_home, lam_away, rho):
    """Dixon-Coles low-score dependency correction (vectorised)."""
    hg = np.asarray(home_goals)
    ag = np.asarray(away_goals)
    tau = np.ones(np.broadcast(hg, ag).shape, dtype=float)
    tau = np.where((hg == 0) & (ag == 0), 1.0 - lam_home * lam_away * rho, tau)
    tau = np.where((hg == 0) & (ag == 1), 1.0 + lam_home * rho, tau)
    tau = np.where((hg == 1) & (ag == 0), 1.0 + lam_away * rho, tau)
    tau = np.where((hg == 1) & (ag == 1), 1.0 - rho, tau)
    return tau


def scoreline_matrix(lam_home: float, lam_away: float, rho: float = 0.0,
                     max_goals: int = 10) -> np.ndarray:
    """P(home=i, away=j) matrix for goals 0..max_goals, with DC correction."""
    goals = np.arange(max_goals + 1)
    ph = poisson.pmf(goals, lam_home)
    pa = poisson.pmf(goals, lam_away)
    matrix = np.outer(ph, pa)
    i = goals[:, None]
    j = goals[None, :]
    matrix = matrix * _tau(i, j, lam_home, lam_away, rho)
    return matrix


def outcome_probabilities(matrix: np.ndarray) -> tuple[float, float, float]:
    """(P(home win), P(draw), P(away win)) from a scoreline matrix."""
    total = matrix.sum()
    p_home = np.tril(matrix, -1).sum() / total
    p_away = np.triu(matrix, 1).sum() / total
    p_draw = np.trace(matrix) / total
    return float(p_home), float(p_draw), float(p_away)


@dataclass
class DixonColesModel:
    attack: dict[str, float]
    defence: dict[str, float]
    home_adv: float
    rho: float

    def expected_goals(self, home: str, away: str, neutral: bool = False) -> tuple[float, float]:
        gamma = 0.0 if neutral else self.home_adv
        lam_home = np.exp(self.attack[home] + self.defence[away] + gamma)
        lam_away = np.exp(self.attack[away] + self.defence[home])
        return float(lam_home), float(lam_away)

    def predict(self, home: str, away: str, neutral: bool = False, max_goals: int = 10) -> dict:
        lam_home, lam_away = self.expected_goals(home, away, neutral)
        matrix = scoreline_matrix(lam_home, lam_away, self.rho, max_goals)
        p_home, p_draw, p_away = outcome_probabilities(matrix)
        return {
            "home": home,
            "away": away,
            "neutral": neutral,
            "xg_home": lam_home,
            "xg_away": lam_away,
            "prob_home": p_home,
            "prob_draw": p_draw,
            "prob_away": p_away,
        }

    @classmethod
    def fit(cls, matches: list[dict]) -> "DixonColesModel":
        """Fit attack/defence/home_adv/rho by weighted MLE.

        ``matches`` rows need: home_team, away_team, home_score, away_score,
        and optional ``weight`` (default 1.0) and ``neutral`` (default False).
        """
        teams = sorted({m["home_team"] for m in matches} | {m["away_team"] for m in matches})
        idx = {t: k for k, t in enumerate(teams)}
        n = len(teams)

        home_i = np.array([idx[m["home_team"]] for m in matches])
        away_i = np.array([idx[m["away_team"]] for m in matches])
        hs = np.array([m["home_score"] for m in matches], dtype=float)
        as_ = np.array([m["away_score"] for m in matches], dtype=float)
        w = np.array([m.get("weight", 1.0) for m in matches], dtype=float)
        home_on = np.array([0.0 if m.get("neutral", False) else 1.0 for m in matches])

        def neg_log_lik(x: np.ndarray) -> float:
            att = x[:n]
            dfc = x[n:2 * n]
            gamma = x[2 * n]
            rho = x[2 * n + 1]
            lam_h = np.exp(att[home_i] + dfc[away_i] + gamma * home_on)
            lam_a = np.exp(att[away_i] + dfc[home_i])
            tau = _tau(hs, as_, lam_h, lam_a, rho)
            tau = np.clip(tau, 1e-10, None)
            ll = hs * np.log(lam_h) - lam_h + as_ * np.log(lam_a) - lam_a + np.log(tau)
            return -float(np.sum(w * ll))

        x0 = np.concatenate([np.zeros(n), np.zeros(n), [0.25], [0.0]])
        bounds = [(-3, 3)] * n + [(-3, 3)] * n + [(-1, 1), (-0.2, 0.2)]
        res = minimize(neg_log_lik, x0, method="L-BFGS-B", bounds=bounds)

        att = res.x[:n]
        dfc = res.x[n:2 * n]
        # Recenter attack to mean 0 (shift the constant into defence; lambdas unchanged).
        m = att.mean()
        att = att - m
        dfc = dfc + m
        return cls(
            attack={t: float(att[idx[t]]) for t in teams},
            defence={t: float(dfc[idx[t]]) for t in teams},
            home_adv=float(res.x[2 * n]),
            rho=float(res.x[2 * n + 1]),
        )
