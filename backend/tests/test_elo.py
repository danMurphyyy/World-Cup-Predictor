"""Tests for the international-football Elo rating system."""
import pytest

from backend.model.elo import EloModel, expected_score, update_ratings


def test_expected_score_symmetric_at_equal_ratings():
    assert expected_score(1500, 1500) == pytest.approx(0.5)


def test_higher_rating_expects_more():
    assert expected_score(1700, 1500) > 0.5


def test_home_win_increases_winner_and_is_zero_sum():
    new_home, new_away = update_ratings(
        1500, 1500, home_goals=2, away_goals=0, neutral=True, tournament="Friendly"
    )
    assert new_home > 1500
    assert new_away < 1500
    assert (new_home - 1500) == pytest.approx(-(new_away - 1500))


def test_bigger_margin_moves_rating_more():
    small = update_ratings(1500, 1500, 1, 0, neutral=True, tournament="Friendly")[0]
    big = update_ratings(1500, 1500, 5, 0, neutral=True, tournament="Friendly")[0]
    assert big > small


def test_fit_ranks_dominant_team_highest():
    teams = ["A", "B", "C", "D"]
    matches = []
    # A always wins; D always loses.
    for _ in range(30):
        for opp in ["B", "C", "D"]:
            matches.append(
                {"home_team": "A", "away_team": opp, "home_score": 3,
                 "away_score": 0, "neutral": True, "tournament": "Friendly"}
            )
        matches.append(
            {"home_team": "B", "away_team": "D", "home_score": 2,
             "away_score": 0, "neutral": True, "tournament": "Friendly"}
        )
    model = EloModel.fit(matches)
    ratings = model.ratings
    assert ratings["A"] == max(ratings.values())
    assert ratings["D"] == min(ratings.values())
