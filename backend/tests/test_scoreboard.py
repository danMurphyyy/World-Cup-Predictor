"""Tests for prediction scoring (log-loss, Brier, pick accuracy)."""
import math

import pytest

from backend.model.scoreboard import (
    brier_one,
    correct_pick,
    log_loss_one,
    outcome_from_score,
)


def test_outcome_from_score():
    assert outcome_from_score(2, 0) == "H"
    assert outcome_from_score(1, 1) == "D"
    assert outcome_from_score(0, 3) == "A"


def test_log_loss_perfect_is_zero():
    assert log_loss_one((1.0, 0.0, 0.0), "H") == pytest.approx(0.0, abs=1e-9)


def test_log_loss_of_half():
    assert log_loss_one((0.5, 0.3, 0.2), "H") == pytest.approx(-math.log(0.5))


def test_brier_perfect_is_zero():
    assert brier_one((1.0, 0.0, 0.0), "H") == pytest.approx(0.0)


def test_brier_uniform():
    # (1/3,1/3,1/3) vs actual H: (1-1/3)^2 + (1/3)^2 + (1/3)^2
    expected = (2 / 3) ** 2 + (1 / 3) ** 2 + (1 / 3) ** 2
    assert brier_one((1 / 3, 1 / 3, 1 / 3), "H") == pytest.approx(expected)


def test_correct_pick():
    assert correct_pick((0.5, 0.3, 0.2), "H") is True
    assert correct_pick((0.5, 0.3, 0.2), "A") is False
