"""FastAPI application exposing predictions, the relationship graph, and the sim."""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.api import services
from backend.model.strength import get_models

app = FastAPI(title="World Cup Predictor API", version="1.0")

# Public read-only API. CORS_ORIGINS env (comma-separated) overrides; default "*".
_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_team(name: str) -> None:
    _, dc = get_models()
    if name not in dc.attack:
        raise HTTPException(status_code=404, detail=f"Unknown team: {name!r}")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/teams")
def get_teams() -> list[dict]:
    return services.teams()


@app.get("/api/predict")
def predict(home: str, away: str, neutral: bool = True) -> dict:
    _require_team(home)
    _require_team(away)
    return services.predict_match(home, away, neutral=neutral)


@app.get("/api/fixtures")
def fixtures(group: str | None = Query(default=None)) -> list[dict]:
    out = services.fixtures_with_predictions()
    if group:
        out = [f for f in out if f["group"] == group]
    return out


@app.get("/api/graph")
def graph(mode: str = Query(default="group"),
          group: str | None = Query(default=None),
          confederation: str | None = Query(default=None)) -> dict:
    return services.filtered_graph(mode=mode, group=group, confederation=confederation)


@app.get("/api/simulate")
def simulate() -> dict:
    return services.simulation_summary()


@app.get("/api/scoreboard")
def scoreboard() -> dict:
    from backend.model.scoreboard import build_scoreboard
    return build_scoreboard()


@app.get("/api/h2h")
def h2h(a: str, b: str) -> dict:
    _require_team(a)
    _require_team(b)
    return services.h2h_detail(a, b)


@app.get("/api/preview")
def preview(home: str, away: str) -> dict:
    _require_team(home)
    _require_team(away)
    return services.match_preview(home, away)


@app.get("/api/team/{name}")
def team(name: str) -> dict:
    _require_team(name)
    match = next((t for t in services.teams() if t["name"] == name), None)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Not a 2026 team: {name!r}")
    opponents = [
        f for f in services.fixtures_with_predictions()
        if f["home"] == name or f["away"] == name
    ]
    return {**match, "group_fixtures": opponents}
