"""Tests for tournament simulation: standings, third-place ranking, full sim."""
import pytest

from backend.model.simulate import (
    compute_standings,
    rank_third_placed,
    run_simulations,
)


def test_standings_order_and_points():
    teams = ["W", "X", "Y", "Z"]
    # W beats everyone; X beats Y,Z; Y beats Z; Z loses all.
    matches = [
        ("W", "X", 1, 0), ("W", "Y", 2, 0), ("W", "Z", 3, 0),
        ("X", "Y", 1, 0), ("X", "Z", 2, 0),
        ("Y", "Z", 1, 0),
    ]
    table = compute_standings(teams, matches)
    assert [row["team"] for row in table] == ["W", "X", "Y", "Z"]
    assert table[0]["points"] == 9
    assert table[0]["played"] == 3
    assert table[-1]["points"] == 0


def test_goal_difference_breaks_points_tie():
    teams = ["A", "B", "C", "D"]
    # A and B both beat C and D, draw with each other -> tie on points, A has better GD.
    matches = [
        ("A", "B", 0, 0),
        ("A", "C", 5, 0), ("A", "D", 5, 0),
        ("B", "C", 1, 0), ("B", "D", 1, 0),
        ("C", "D", 0, 0),
    ]
    table = compute_standings(teams, matches)
    assert table[0]["team"] == "A"  # same points as B, superior goal difference
    assert table[1]["team"] == "B"


def test_rank_third_placed_takes_best_eight():
    thirds = [
        {"team": f"T{i}", "points": i, "gd": 0, "gf": 0} for i in range(12)
    ]
    best = rank_third_placed(thirds)
    assert len(best) == 8
    qualified = {row["team"] for row in best}
    # Highest points (T11..T4) qualify; lowest four (T0..T3) do not.
    assert "T11" in qualified and "T4" in qualified
    assert qualified.isdisjoint({"T0", "T1", "T2", "T3"})


def test_knockout_meetings_sum_to_31_matches():
    """Every tournament plays 31 knockout matches, so meeting probs sum to 31."""
    result = run_simulations(n=150, seed=3)
    meetings = result["knockout_meetings"]
    assert len(meetings) > 0
    for m in meetings:
        assert 0 < m["prob"] <= 1
        assert m["a"] < m["b"]  # stored as an ordered unique pair
    assert sum(m["prob"] for m in meetings) == pytest.approx(31.0, abs=1e-6)


def test_full_simulation_probabilities_are_coherent():
    result = run_simulations(n=200, seed=7)
    odds = result["title_odds"]
    # Every one of the 48 teams has an entry.
    assert len(odds) == 48
    # Champion probabilities form a distribution.
    assert sum(odds.values()) == pytest.approx(1.0, abs=1e-9)
    # A strong side should out-rank a minnow over 200 sims.
    assert odds["Spain"] > odds["Curaçao"]
