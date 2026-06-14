"""In-memory feature store over the historical results.

49k rows fit comfortably in memory, so we cache a single cleaned DataFrame and
expose typed query helpers. The model and API consume these rather than touching
the CSV directly. Filters here back the app's temporal/competitiveness controls.
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Optional

import pandas as pd

from backend.data.ingest import load_results

# Tournaments treated as non-competitive (down-weighted / filterable in the app).
FRIENDLY_TOURNAMENTS = {"Friendly"}


@lru_cache(maxsize=1)
def results() -> pd.DataFrame:
    """Cached, cleaned historical results (loaded once per process)."""
    return load_results()


def list_teams() -> list[str]:
    """All distinct national teams appearing in the dataset, sorted."""
    df = results()
    teams = pd.concat([df["home_team"], df["away_team"]]).dropna().unique()
    return sorted(teams.tolist())


def filter_matches(
    *,
    since: Optional[datetime] = None,
    competitive_only: bool = False,
    teams: Optional[set[str]] = None,
) -> pd.DataFrame:
    """Return matches narrowed by the app's temporal/competitiveness filters.

    ``teams`` restricts to matches where *both* sides are in the set (useful for
    confederation- or group-scoped views).
    """
    df = results()
    if since is not None:
        df = df[df["date"] >= pd.Timestamp(since)]
    if competitive_only:
        df = df[~df["tournament"].isin(FRIENDLY_TOURNAMENTS)]
    if teams is not None:
        df = df[df["home_team"].isin(teams) & df["away_team"].isin(teams)]
    return df


def head_to_head(team_a: str, team_b: str) -> pd.DataFrame:
    """All historical meetings between two teams, chronologically."""
    df = results()
    mask = (
        ((df["home_team"] == team_a) & (df["away_team"] == team_b))
        | ((df["home_team"] == team_b) & (df["away_team"] == team_a))
    )
    return df[mask].sort_values("date").reset_index(drop=True)


def head_to_head_summary(team_a: str, team_b: str) -> dict:
    """Win/draw/loss record and goals between two teams, from a's perspective."""
    h2h = head_to_head(team_a, team_b)
    a_wins = draws = b_wins = a_goals = b_goals = 0
    for _, m in h2h.iterrows():
        if m["home_team"] == team_a:
            ag, bg = m["home_score"], m["away_score"]
        else:
            ag, bg = m["away_score"], m["home_score"]
        a_goals += ag
        b_goals += bg
        if ag > bg:
            a_wins += 1
        elif ag < bg:
            b_wins += 1
        else:
            draws += 1
    return {
        "team_a": team_a,
        "team_b": team_b,
        "played": len(h2h),
        "a_wins": a_wins,
        "draws": draws,
        "b_wins": b_wins,
        "a_goals": a_goals,
        "b_goals": b_goals,
    }


if __name__ == "__main__":  # pragma: no cover - manual smoke check
    print(f"Teams: {len(list_teams())}")
    print("Brazil vs Argentina:", head_to_head_summary("Brazil", "Argentina"))
