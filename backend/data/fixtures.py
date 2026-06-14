"""2026 World Cup tournament structure: groups, fixtures, and name mapping.

The group draw is seeded from ``seed/groups_2026.json``. Team names are mapped to
the historical dataset's spelling so the model finds each side's match history.
Group fixtures are the round-robin within each group (everyone plays everyone).
"""
from __future__ import annotations

import json
from itertools import combinations

from backend.config import SEED_DIR
from backend.data.store import list_teams

# Map seed/display spelling -> historical dataset spelling, where they differ.
# Populated after validating against the dataset; left side is what we seed.
NAME_OVERRIDES: dict[str, str] = {
    "Curacao": "Curaçao",
    "Czechia": "Czech Republic",
}

CONFEDERATION = {
    # Keys use dataset spelling (post NAME_OVERRIDES). Backs the structural filter.
    "Czech Republic": "UEFA", "Mexico": "CONCACAF", "South Africa": "CAF", "South Korea": "AFC",
    "Bosnia and Herzegovina": "UEFA", "Canada": "CONCACAF", "Qatar": "AFC", "Switzerland": "UEFA",
    "Brazil": "CONMEBOL", "Haiti": "CONCACAF", "Morocco": "CAF", "Scotland": "UEFA",
    "Australia": "AFC", "Paraguay": "CONMEBOL", "Turkey": "UEFA", "United States": "CONCACAF",
    "Curaçao": "CONCACAF", "Ecuador": "CONMEBOL", "Germany": "UEFA", "Ivory Coast": "CAF",
    "Japan": "AFC", "Netherlands": "UEFA", "Sweden": "UEFA", "Tunisia": "CAF",
    "Belgium": "UEFA", "Egypt": "CAF", "Iran": "AFC", "New Zealand": "OFC",
    "Cape Verde": "CAF", "Saudi Arabia": "AFC", "Spain": "UEFA", "Uruguay": "CONMEBOL",
    "France": "UEFA", "Iraq": "AFC", "Norway": "UEFA", "Senegal": "CAF",
    "Algeria": "CAF", "Argentina": "CONMEBOL", "Austria": "UEFA", "Jordan": "AFC",
    "Colombia": "CONMEBOL", "DR Congo": "CAF", "Portugal": "UEFA", "Uzbekistan": "AFC",
    "Croatia": "UEFA", "England": "UEFA", "Ghana": "CAF", "Panama": "CONCACAF",
}


def group_of() -> dict[str, str]:
    """Reverse lookup: team -> group letter (dataset spelling)."""
    return {team: g for g, teams in load_groups().items() for team in teams}


def load_groups() -> dict[str, list[str]]:
    """Return {group_letter: [team, ...]} from the seed file (dataset spelling)."""
    raw = json.loads((SEED_DIR / "groups_2026.json").read_text(encoding="utf-8"))
    groups = raw["groups"]
    return {g: [NAME_OVERRIDES.get(t, t) for t in teams] for g, teams in groups.items()}


def all_tournament_teams() -> list[str]:
    """Flat sorted list of all 48 teams (dataset spelling)."""
    teams: list[str] = []
    for members in load_groups().values():
        teams.extend(members)
    return sorted(teams)


def group_fixtures() -> list[dict]:
    """Round-robin group-stage fixtures: 6 per group, 72 total."""
    fixtures: list[dict] = []
    for group, teams in load_groups().items():
        for home, away in combinations(teams, 2):
            fixtures.append({"group": group, "home": home, "away": away})
    return fixtures


def validate_names() -> list[str]:
    """Return seeded team names that don't match any team in the dataset."""
    known = set(list_teams())
    return [t for t in all_tournament_teams() if t not in known]


if __name__ == "__main__":  # pragma: no cover - manual smoke check
    missing = validate_names()
    print(f"Teams: {len(all_tournament_teams())}, group fixtures: {len(group_fixtures())}")
    if missing:
        print("MISSING from dataset (need NAME_OVERRIDES):", missing)
    else:
        print("All 48 team names matched the dataset.")
