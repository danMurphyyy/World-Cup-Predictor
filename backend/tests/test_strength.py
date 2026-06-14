"""Tests for recency weighting used in model fitting."""
import pytest

from backend.model.strength import recency_weight


def test_weight_is_one_at_zero_age():
    assert recency_weight(0.0, halflife_days=1000) == pytest.approx(1.0)


def test_weight_halves_at_halflife():
    assert recency_weight(1000.0, halflife_days=1000) == pytest.approx(0.5)


def test_weight_decreases_with_age():
    assert recency_weight(2000.0, halflife_days=1000) < recency_weight(500.0, halflife_days=1000)
