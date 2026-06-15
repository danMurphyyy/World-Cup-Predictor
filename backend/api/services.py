"""Service layer: turns models + data into the JSON shapes the frontend needs.

Keeps FastAPI route handlers thin. Expensive products (team metadata, the full
relationship graph) are built once and cached in-process; the simulation is
cached on disk via the model layer.
"""
from __future__ import annotations

from functools import lru_cache

from backend.data.fixtures import CONFEDERATION, group_fixtures, group_of, load_groups
from backend.data.store import head_to_head, head_to_head_summary
from backend.model.blend import predict_blended
from backend.model.preview import generate_preview
from backend.model.simulate import get_simulation
from backend.model.strength import get_models


def predict_match(home: str, away: str, neutral: bool = True) -> dict:
    """Match prediction (W/D/L + expected goals) using the Elo-blended model."""
    elo, dc = get_models()
    return predict_blended(elo, dc, home, away, neutral=neutral)


@lru_cache(maxsize=1)
def teams() -> list[dict]:
    """All 48 teams with strength + simulation metadata, ranked by title odds."""
    elo, dc = get_models()
    sim = get_simulation()
    grp = group_of()
    rows = []
    for name in load_groups_flat():
        rows.append({
            "name": name,
            "group": grp[name],
            "confederation": CONFEDERATION.get(name, "?"),
            "elo": round(elo.rating(name), 1),
            "attack": round(dc.attack.get(name, 0.0), 3),
            "defence": round(dc.defence.get(name, 0.0), 3),
            "title_odds": sim["title_odds"].get(name, 0.0),
            "reach_final": sim["reach_final"].get(name, 0.0),
            "reach_semi": sim["reach_semi"].get(name, 0.0),
            "reach_quarter": sim["reach_quarter"].get(name, 0.0),
            "reach_r16": sim["reach_r16"].get(name, 0.0),
            "qualify_knockout": sim["qualify_knockout"].get(name, 0.0),
        })
    return sorted(rows, key=lambda r: -r["title_odds"])


def load_groups_flat() -> list[str]:
    return [t for members in load_groups().values() for t in members]


def _edge(home: str, away: str, group: str, meet_prob: float | None = None) -> dict:
    """Build one graph edge with the model prediction and head-to-head count."""
    pred = predict_match(home, away, neutral=True)
    h2h = head_to_head_summary(home, away)
    edge = {
        "source": home, "target": away, "group": group,
        "prob_home": pred["prob_home"], "prob_draw": pred["prob_draw"],
        "prob_away": pred["prob_away"], "xg_home": pred["xg_home"],
        "xg_away": pred["xg_away"], "meetings": h2h["played"],
    }
    if meet_prob is not None:
        edge["meet_prob"] = meet_prob
    return edge


@lru_cache(maxsize=1)
def _nodes() -> list[dict]:
    return [
        {
            "id": r["name"], "group": r["group"], "confederation": r["confederation"],
            "elo": r["elo"], "title_odds": r["title_odds"],
        }
        for r in teams()
    ]


@lru_cache(maxsize=1)
def _group_edges() -> list[dict]:
    """Group-stage matchups (72 edges)."""
    return [_edge(fx["home"], fx["away"], fx["group"]) for fx in group_fixtures()]


@lru_cache(maxsize=1)
def _knockout_edges(limit: int = 24) -> list[dict]:
    """Cross-group edges for the most likely knockout meetings (from the sim).

    Capped small so the map stays readable — these are the headline deep-run
    matchups, not every possible pairing.
    """
    sim = get_simulation()
    return [
        _edge(m["a"], m["b"], "KO", meet_prob=m["prob"])
        for m in sim["knockout_meetings"][:limit]
    ]


def filtered_graph(mode: str = "group", group: str | None = None,
                   confederation: str | None = None) -> dict:
    """Graph for the chosen edge mode, subset by structural filters."""
    nodes = _nodes()
    edges = _knockout_edges() if mode == "knockout" else _group_edges()
    if group:
        nodes = [n for n in nodes if n["group"] == group]
    if confederation:
        nodes = [n for n in nodes if n["confederation"] == confederation]
    keep = {n["id"] for n in nodes}
    edges = [e for e in edges if e["source"] in keep and e["target"] in keep]
    return {"nodes": nodes, "edges": edges}


def fixtures_with_predictions() -> list[dict]:
    """Group-stage fixtures, each with its match prediction."""
    out = []
    for fx in group_fixtures():
        pred = predict_match(fx["home"], fx["away"], neutral=True)
        out.append({"group": fx["group"], "home": fx["home"], "away": fx["away"],
                    "prediction": pred})
    return out


def h2h_detail(team_a: str, team_b: str, limit: int = 10) -> dict:
    """Head-to-head summary plus the most recent meetings."""
    summary = head_to_head_summary(team_a, team_b)
    recent = head_to_head(team_a, team_b).tail(limit)
    summary["recent"] = [
        {"date": m["date"].date().isoformat(), "home": m["home_team"],
         "away": m["away_team"], "home_score": int(m["home_score"]),
         "away_score": int(m["away_score"]), "tournament": m["tournament"]}
        for _, m in recent.iterrows()
    ]
    summary["prediction"] = predict_match(team_a, team_b, neutral=True)
    return summary


def match_preview(home: str, away: str) -> dict:
    """Data-driven match narrative built locally from the model's numbers."""
    elo, dc = get_models()
    pred = predict_blended(elo, dc, home, away, neutral=True)
    h2h = head_to_head_summary(home, away)
    return {"home": home, "away": away, "preview": generate_preview(pred, h2h, home, away)}


def simulation_summary() -> dict:
    """Tournament simulation results, teams ranked by title odds."""
    sim = get_simulation()
    ranked = sorted(
        ({"name": t, "title_odds": p,
          "reach_final": sim["reach_final"].get(t, 0.0),
          "reach_semi": sim["reach_semi"].get(t, 0.0),
          "reach_quarter": sim["reach_quarter"].get(t, 0.0),
          "qualify_knockout": sim["qualify_knockout"].get(t, 0.0)}
         for t, p in sim["title_odds"].items()),
        key=lambda r: -r["title_odds"],
    )
    return {"n": sim["n"], "teams": ranked}
