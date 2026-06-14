"""Contract tests for the FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_teams_returns_all_48_with_metadata():
    rows = client.get("/api/teams").json()
    assert len(rows) == 48
    first = rows[0]
    for key in ("name", "group", "confederation", "elo", "title_odds"):
        assert key in first
    # Sorted by title odds, descending.
    assert rows[0]["title_odds"] >= rows[-1]["title_odds"]


def test_predict_probabilities_sum_to_one():
    r = client.get("/api/predict", params={"home": "Brazil", "away": "Argentina"}).json()
    assert r["prob_home"] + r["prob_draw"] + r["prob_away"] == pytest.approx(1.0, abs=1e-6)
    assert r["xg_home"] > 0 and r["xg_away"] > 0


def test_predict_unknown_team_404():
    assert client.get("/api/predict", params={"home": "Atlantis", "away": "Brazil"}).status_code == 404


def test_graph_full_and_filtered():
    full = client.get("/api/graph").json()
    assert len(full["nodes"]) == 48
    assert len(full["edges"]) == 72  # 6 per group x 12

    group_c = client.get("/api/graph", params={"group": "C"}).json()
    assert len(group_c["nodes"]) == 4
    assert len(group_c["edges"]) == 6


def test_graph_knockout_mode_has_cross_group_edges():
    g = client.get("/api/graph", params={"mode": "knockout"}).json()
    assert len(g["nodes"]) == 48
    assert len(g["edges"]) > 0
    groups = {n["id"]: n["group"] for n in g["nodes"]}
    assert all("meet_prob" in e for e in g["edges"])
    # Knockout edges connect teams from different groups.
    assert any(groups[e["source"]] != groups[e["target"]] for e in g["edges"])


def test_simulate_distribution():
    sim = client.get("/api/simulate").json()
    assert len(sim["teams"]) == 48
    assert sum(t["title_odds"] for t in sim["teams"]) == pytest.approx(1.0, abs=1e-6)


def test_h2h_has_record_and_prediction():
    r = client.get("/api/h2h", params={"a": "Brazil", "b": "Argentina"}).json()
    assert r["played"] > 0
    assert "prediction" in r and len(r["recent"]) > 0


def test_team_profile_has_three_group_fixtures():
    r = client.get("/api/team/Brazil").json()
    assert r["name"] == "Brazil"
    assert len(r["group_fixtures"]) == 3
