"""Tests for the Dixon-Coles scoreline math and model fitting."""
import numpy as np
import pytest

from backend.model.dixon_coles import (
    DixonColesModel,
    outcome_probabilities,
    scoreline_matrix,
)


def test_scoreline_matrix_sums_to_one():
    m = scoreline_matrix(1.5, 1.2, rho=0.0, max_goals=15)
    assert m.sum() == pytest.approx(1.0, abs=1e-6)


def test_equal_lambdas_give_symmetric_outcomes():
    m = scoreline_matrix(1.4, 1.4, rho=0.0)
    p_home, p_draw, p_away = outcome_probabilities(m)
    assert p_home == pytest.approx(p_away, abs=1e-9)
    assert p_home + p_draw + p_away == pytest.approx(1.0, abs=1e-6)


def test_higher_home_lambda_raises_home_win_prob():
    weak = outcome_probabilities(scoreline_matrix(1.2, 1.2))[0]
    strong = outcome_probabilities(scoreline_matrix(2.5, 1.2))[0]
    assert strong > weak


def test_fit_recovers_strength_ordering():
    """On synthetic data where A >> B >> C in attack, fitted attack ranks match."""
    rng = np.random.default_rng(42)
    true_attack = {"A": 0.6, "B": 0.0, "C": -0.6}
    true_defence = {"A": -0.3, "B": 0.0, "C": 0.3}
    teams = list(true_attack)
    rows = []
    for _ in range(4000):
        h, a = rng.choice(teams, size=2, replace=False)
        lam_h = np.exp(true_attack[h] + true_defence[a] + 0.25)
        lam_a = np.exp(true_attack[a] + true_defence[h])
        rows.append(
            {
                "home_team": h,
                "away_team": a,
                "home_score": rng.poisson(lam_h),
                "away_score": rng.poisson(lam_a),
                "weight": 1.0,
            }
        )

    model = DixonColesModel.fit(rows)
    assert model.attack["A"] > model.attack["B"] > model.attack["C"]


def test_predict_returns_normalised_probabilities():
    rng = np.random.default_rng(0)
    rows = []
    for _ in range(500):
        rows.append(
            {
                "home_team": "X",
                "away_team": "Y",
                "home_score": rng.poisson(1.5),
                "away_score": rng.poisson(1.1),
                "weight": 1.0,
            }
        )
    model = DixonColesModel.fit(rows)
    pred = model.predict("X", "Y")
    assert pred["prob_home"] + pred["prob_draw"] + pred["prob_away"] == pytest.approx(1.0, abs=1e-6)
    assert pred["xg_home"] > 0 and pred["xg_away"] > 0
