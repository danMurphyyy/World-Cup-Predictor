"""Tests for blending Elo into the Dixon-Coles goal expectation."""
import pytest

from backend.model.blend import blend_expected_goals


def test_zero_weight_recovers_dixon_coles():
    lh, la = blend_expected_goals(1.6, 1.0, elo_diff=300, w=0.0, goal_scale=150)
    assert lh == pytest.approx(1.6)
    assert la == pytest.approx(1.0)


def test_total_goals_preserved():
    lh, la = blend_expected_goals(1.6, 1.0, elo_diff=200, w=0.5, goal_scale=150)
    assert lh + la == pytest.approx(2.6)


def test_elo_favourite_gains_expected_goals():
    # Even DC expectation, but home is much stronger on Elo -> home favoured.
    lh, la = blend_expected_goals(1.3, 1.3, elo_diff=400, w=0.5, goal_scale=150)
    assert lh > la


def test_clamps_to_positive():
    lh, la = blend_expected_goals(1.2, 1.1, elo_diff=-5000, w=1.0, goal_scale=150)
    assert lh > 0 and la > 0
