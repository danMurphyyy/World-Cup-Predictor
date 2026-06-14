"""International-football Elo ratings (World Football Elo style).

Ratings update after every match by the gap between the actual and expected
result, scaled by a tournament-importance weight and a goal-difference
multiplier. Used as an explainable team-strength signal and as a feature/prior
alongside the Dixon-Coles model.
"""
from __future__ import annotations

from dataclasses import dataclass, field

INITIAL_RATING = 1500.0
HOME_ADVANTAGE = 65.0  # Elo points added to the home side on non-neutral grounds.

# Tournament-importance K weights (higher = ratings move more).
TOURNAMENT_K = {
    "FIFA World Cup": 60.0,
    "FIFA World Cup qualification": 40.0,
    "UEFA Euro": 50.0,
    "Copa América": 50.0,
    "African Cup of Nations": 40.0,
    "AFC Asian Cup": 40.0,
    "UEFA Nations League": 40.0,
    "Confederations Cup": 40.0,
    "Friendly": 20.0,
}
DEFAULT_K = 30.0


def expected_score(rating_home: float, rating_away: float, home_adv: float = 0.0) -> float:
    """Expected result for the home side in [0, 1]."""
    return 1.0 / (1.0 + 10.0 ** (-(rating_home + home_adv - rating_away) / 400.0))


def _goal_diff_multiplier(goal_diff: int) -> float:
    """World Football Elo margin-of-victory multiplier."""
    gd = abs(goal_diff)
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11.0 + gd) / 8.0


def update_ratings(
    rating_home: float,
    rating_away: float,
    home_goals: int,
    away_goals: int,
    neutral: bool = False,
    tournament: str = "Friendly",
) -> tuple[float, float]:
    """Return updated (home, away) ratings after a single match."""
    home_adv = 0.0 if neutral else HOME_ADVANTAGE
    we = expected_score(rating_home, rating_away, home_adv)
    if home_goals > away_goals:
        w = 1.0
    elif home_goals < away_goals:
        w = 0.0
    else:
        w = 0.5
    k = TOURNAMENT_K.get(tournament, DEFAULT_K) * _goal_diff_multiplier(home_goals - away_goals)
    delta = k * (w - we)
    return rating_home + delta, rating_away - delta


@dataclass
class EloModel:
    ratings: dict[str, float] = field(default_factory=dict)

    def rating(self, team: str) -> float:
        return self.ratings.get(team, INITIAL_RATING)

    @classmethod
    def fit(cls, matches: list[dict]) -> "EloModel":
        """Process matches in the given (chronological) order to final ratings.

        Rows need: home_team, away_team, home_score, away_score, and optional
        ``neutral`` (default False) and ``tournament`` (default "Friendly").
        """
        ratings: dict[str, float] = {}
        for m in matches:
            home, away = m["home_team"], m["away_team"]
            rh = ratings.get(home, INITIAL_RATING)
            ra = ratings.get(away, INITIAL_RATING)
            new_h, new_a = update_ratings(
                rh, ra, m["home_score"], m["away_score"],
                neutral=m.get("neutral", False),
                tournament=m.get("tournament", "Friendly"),
            )
            ratings[home] = new_h
            ratings[away] = new_a
        return cls(ratings=ratings)
