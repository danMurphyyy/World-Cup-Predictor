"""Tests for the cross-confederation expected-goals adjustment."""
import pytest

from backend.model.confed import confed_adjust

OFF = {"UEFA": 0.4, "CONMEBOL": 0.0, "CONCACAF": 0.0, "CAF": 0.0, "AFC": 0.0, "OFC": 0.0}


def test_same_confederation_unchanged():
    # Brazil and Argentina are both CONMEBOL -> no adjustment.
    lh, la = confed_adjust(1.5, 1.2, "Brazil", "Argentina", OFF)
    assert (lh, la) == (1.5, 1.2)


def test_unknown_team_unchanged():
    lh, la = confed_adjust(1.5, 1.2, "Brazil", "Atlantis", OFF)
    assert (lh, la) == (1.5, 1.2)


def test_higher_confederation_gains_goals():
    # Spain (UEFA, +0.4) vs Brazil (CONMEBOL, 0) -> Spain's expected goals rise.
    lh, la = confed_adjust(1.3, 1.3, "Spain", "Brazil", OFF)
    assert lh > 1.3 and la < 1.3
    assert lh + la == pytest.approx(2.6)  # total preserved
