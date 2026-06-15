"""Confederation lookup for national teams (dataset spelling).

Used to correct the model's cross-confederation bias: ratings learned mostly
from intra-confederation play don't transfer cleanly between confederations.
Covers the 48 World Cup teams plus the major nations that appear in historical
cross-confederation matches; unknown teams return None (excluded from fitting).
"""
from __future__ import annotations

_GROUPS = {
    "CONMEBOL": "Argentina,Brazil,Uruguay,Colombia,Chile,Peru,Ecuador,Paraguay,Bolivia,Venezuela",
    "UEFA": "Spain,France,England,Germany,Italy,Netherlands,Portugal,Belgium,Croatia,Denmark,"
            "Switzerland,Poland,Sweden,Serbia,Austria,Ukraine,Wales,Scotland,Czech Republic,Turkey,"
            "Norway,Greece,Russia,Hungary,Romania,Republic of Ireland,Iceland,Slovakia,Slovenia,"
            "Bosnia and Herzegovina,Finland,Northern Ireland,Albania,Bulgaria,Georgia",
    "CAF": "Morocco,Senegal,Nigeria,Cameroon,Egypt,Ghana,Ivory Coast,Algeria,Tunisia,Mali,"
           "South Africa,DR Congo,Cape Verde,Burkina Faso,Guinea",
    "AFC": "Japan,South Korea,Iran,Saudi Arabia,Australia,Qatar,Iraq,United Arab Emirates,"
           "Uzbekistan,China PR,Jordan,Oman,Bahrain",
    "CONCACAF": "Mexico,United States,Canada,Costa Rica,Panama,Honduras,Jamaica,Haiti,Curaçao,El Salvador",
    "OFC": "New Zealand",
}

CONFEDERATION: dict[str, str] = {
    team.strip(): conf for conf, teams in _GROUPS.items() for team in teams.split(",")
}


def confederation_of(team: str) -> str | None:
    return CONFEDERATION.get(team)
