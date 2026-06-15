"""One-off diagnostic: is the blended model calibrated across confederations?

For historical cross-confederation matches, compare the points the model
PREDICTED each confederation would take against the points they ACTUALLY took.
predicted > actual  => the model over-rates that confederation.
"""
from __future__ import annotations

import pandas as pd

from backend.model.blend import predict_blended
from backend.model.strength import get_models
from backend.data.store import results

CONFED = {}
def _add(conf, teams):
    for t in teams.split(","):
        CONFED[t.strip()] = conf

_add("CONMEBOL", "Argentina,Brazil,Uruguay,Colombia,Chile,Peru,Ecuador,Paraguay,Bolivia,Venezuela")
_add("UEFA", "Spain,France,England,Germany,Italy,Netherlands,Portugal,Belgium,Croatia,Denmark,"
             "Switzerland,Poland,Sweden,Serbia,Austria,Ukraine,Wales,Scotland,Czech Republic,Turkey,"
             "Norway,Greece,Russia,Hungary,Romania,Republic of Ireland,Iceland,Slovakia,Slovenia,"
             "Bosnia and Herzegovina,Finland,Northern Ireland,Albania,Bulgaria,Georgia")
_add("CAF", "Morocco,Senegal,Nigeria,Cameroon,Egypt,Ghana,Ivory Coast,Algeria,Tunisia,Mali,"
            "South Africa,DR Congo,Cape Verde,Burkina Faso,Guinea")
_add("AFC", "Japan,South Korea,Iran,Saudi Arabia,Australia,Qatar,Iraq,United Arab Emirates,"
            "Uzbekistan,China PR,Jordan,Oman,Bahrain")
_add("CONCACAF", "Mexico,United States,Canada,Costa Rica,Panama,Honduras,Jamaica,Haiti,Curaçao,El Salvador")
_add("OFC", "New Zealand")


def run(since="2002-01-01", competitive_only=False):
    elo, dc = get_models()
    df = results()
    df = df[df["date"] >= pd.Timestamp(since)]
    if competitive_only:
        df = df[df["tournament"] != "Friendly"]

    # per-confederation tallies: [predicted_points, actual_points, matches]
    agg = {}
    for m in df.itertuples():
        ch, ca = CONFED.get(m.home_team), CONFED.get(m.away_team)
        if ch is None or ca is None or ch == ca:
            continue
        pred = predict_blended(elo, dc, m.home_team, m.away_team, neutral=bool(m.neutral))
        ph, pd_, pa = pred["prob_home"], pred["prob_draw"], pred["prob_away"]
        # home perspective
        ap_home = 3 if m.home_score > m.away_score else (1 if m.home_score == m.away_score else 0)
        agg.setdefault(ch, [0.0, 0.0, 0])
        agg[ch][0] += 3 * ph + pd_; agg[ch][1] += ap_home; agg[ch][2] += 1
        # away perspective
        ap_away = 3 if m.away_score > m.home_score else (1 if m.home_score == m.away_score else 0)
        agg.setdefault(ca, [0.0, 0.0, 0])
        agg[ca][0] += 3 * pa + pd_; agg[ca][1] += ap_away; agg[ca][2] += 1

    tag = "competitive only" if competitive_only else "all matches"
    print(f"\nCross-confederation calibration since {since} ({tag}):")
    print(f"  {'confed':10} {'n':>5} {'pred pts/g':>11} {'actual pts/g':>13} {'gap':>7}")
    for conf in sorted(agg, key=lambda c: -(agg[c][1] / agg[c][2])):
        pred, act, n = agg[conf]
        gap = (act - pred) / n
        flag = "  <-- model UNDER-rates" if gap > 0.08 else ("  <-- model OVER-rates" if gap < -0.08 else "")
        print(f"  {conf:10} {n:>5} {pred/n:>11.3f} {act/n:>13.3f} {gap:>+7.3f}{flag}")


if __name__ == "__main__":
    run("2002-01-01", competitive_only=False)
    run("2002-01-01", competitive_only=True)
