"""Monte-Carlo simulation of the 2026 World Cup.

Each match is sampled from the Dixon-Coles expected goals (host nations get the
home-advantage term). Groups are played as round-robins; the top two plus the
eight best third-placed teams advance to a 32-team knockout seeded by group
finish then Elo. Running many tournaments yields advancement and title odds.
"""
from __future__ import annotations

import json
from collections import Counter
from itertools import combinations

import numpy as np

from backend.config import CACHE_DIR, HOST_NATIONS
from backend.data.fixtures import load_groups
from backend.model.blend import blend_expected_goals
from backend.model.dixon_coles import DixonColesModel
from backend.model.elo import HOME_ADVANTAGE, EloModel
from backend.model.strength import get_models

SIM_CACHE = CACHE_DIR / "simulation.json"


# --- Deterministic helpers (pure, unit-tested) ---------------------------------

def compute_standings(teams: list[str], matches: list[tuple[str, str, int, int]]) -> list[dict]:
    """Group table sorted by points, then goal difference, then goals for."""
    stats = {t: {"team": t, "played": 0, "points": 0, "gf": 0, "ga": 0} for t in teams}
    for home, away, hg, ag in matches:
        for t, gf, ga in ((home, hg, ag), (away, ag, hg)):
            s = stats[t]
            s["played"] += 1
            s["gf"] += gf
            s["ga"] += ga
        if hg > ag:
            stats[home]["points"] += 3
        elif hg < ag:
            stats[away]["points"] += 3
        else:
            stats[home]["points"] += 1
            stats[away]["points"] += 1
    for s in stats.values():
        s["gd"] = s["gf"] - s["ga"]
    return sorted(stats.values(), key=lambda s: (-s["points"], -s["gd"], -s["gf"], s["team"]))


def rank_third_placed(thirds: list[dict]) -> list[dict]:
    """The eight best third-placed teams, by points then GD then goals for."""
    ordered = sorted(thirds, key=lambda s: (-s["points"], -s["gd"], -s["gf"], s["team"]))
    return ordered[:8]


def _seed_order(n: int) -> list[int]:
    """Standard single-elimination bracket positions (top seeds kept apart)."""
    order = [0]
    while len(order) < n:
        m = len(order) * 2
        order = [x for seed in order for x in (seed, m - 1 - seed)]
    return order


# --- Match sampling -------------------------------------------------------------

def _expected_goals(elo: EloModel, dc: DixonColesModel, a: str, b: str) -> tuple[float, float]:
    """Elo-blended expected goals (a, b), with host nations getting home advantage."""
    a_host, b_host = a in HOST_NATIONS, b in HOST_NATIONS
    if a_host and not b_host:
        lh0, la0 = dc.expected_goals(a, b, neutral=False)
        ediff = elo.rating(a) - elo.rating(b) + HOME_ADVANTAGE
        return blend_expected_goals(lh0, la0, ediff)
    if b_host and not a_host:
        lh0, la0 = dc.expected_goals(b, a, neutral=False)
        eb, ea = blend_expected_goals(lh0, la0, elo.rating(b) - elo.rating(a) + HOME_ADVANTAGE)
        return ea, eb
    lh0, la0 = dc.expected_goals(a, b, neutral=True)
    return blend_expected_goals(lh0, la0, elo.rating(a) - elo.rating(b))


def _sample_goals(elo, dc, a, b, rng) -> tuple[int, int]:
    la, lb = _expected_goals(elo, dc, a, b)
    return int(rng.poisson(la)), int(rng.poisson(lb))


def _knockout_winner(elo, dc, a, b, rng) -> str:
    ga, gb = _sample_goals(elo, dc, a, b, rng)
    if ga > gb:
        return a
    if gb > ga:
        return b
    # Drawn after normal/extra time -> shootout, weighted by attacking strength.
    la, lb = _expected_goals(elo, dc, a, b)
    return a if rng.random() < la / (la + lb) else b


# --- One tournament -------------------------------------------------------------

def simulate_tournament(dc, elo: EloModel, groups: dict[str, list[str]], rng) -> dict:
    winners, runners, thirds = [], [], []
    for teams in groups.values():
        matches = [(h, a, *_sample_goals(elo, dc, h, a, rng)) for h, a in combinations(teams, 2)]
        table = compute_standings(teams, matches)
        winners.append(table[0]["team"])
        runners.append(table[1]["team"])
        thirds.append(table[2])
    best_thirds = [row["team"] for row in rank_third_placed(thirds)]

    finish = {t: 0 for t in winners} | {t: 1 for t in runners} | {t: 2 for t in best_thirds}
    qualified = list(finish)
    seeds = sorted(qualified, key=lambda t: (finish[t], -elo.rating(t)))
    bracket = [seeds[i] for i in _seed_order(len(seeds))]

    # 32 -> 16 (reach R16) -> 8 (QF) -> 4 (SF) -> 2 (Final), then play the final.
    # 31 knockout matches total; record every pairing for meeting-frequency stats.
    reached = {"r16": [], "qf": [], "sf": [], "final": []}
    meetings: list[tuple[str, str]] = []
    survivors = bracket
    for name in ["r16", "qf", "sf", "final"]:
        winners = []
        for i in range(0, len(survivors), 2):
            a, b = survivors[i], survivors[i + 1]
            meetings.append((a, b))
            winners.append(_knockout_winner(elo, dc, a, b, rng))
        survivors = winners
        reached[name] = list(survivors)
    meetings.append((survivors[0], survivors[1]))
    champion = _knockout_winner(elo, dc, survivors[0], survivors[1], rng)

    return {"champion": champion, "qualified": qualified, "meetings": meetings, **reached}


# --- Many tournaments -----------------------------------------------------------

def run_simulations(n: int = 10000, seed: int | None = None) -> dict:
    """Run ``n`` tournaments and return advancement + title probabilities."""
    elo, dc = get_models()
    groups = load_groups()
    all_teams = [t for members in groups.values() for t in members]
    rng = np.random.default_rng(seed)

    champion = Counter()
    final = Counter()
    semi = Counter()
    quarter = Counter()
    last16 = Counter()
    qualify = Counter()
    meet = Counter()

    for _ in range(n):
        r = simulate_tournament(dc, elo, groups, rng)
        champion[r["champion"]] += 1
        final.update(r["final"])
        semi.update(r["sf"])
        quarter.update(r["qf"])
        last16.update(r["r16"])
        qualify.update(r["qualified"])
        meet.update(tuple(sorted(pair)) for pair in r["meetings"])

    def probs(counter: Counter) -> dict:
        return {t: counter.get(t, 0) / n for t in all_teams}

    knockout_meetings = sorted(
        ({"a": a, "b": b, "prob": c / n} for (a, b), c in meet.items()),
        key=lambda m: -m["prob"],
    )

    return {
        "n": n,
        "title_odds": probs(champion),
        "reach_final": probs(final),
        "reach_semi": probs(semi),
        "reach_quarter": probs(quarter),
        "reach_r16": probs(last16),
        "qualify_knockout": probs(qualify),
        "knockout_meetings": knockout_meetings,
    }


def get_simulation(rebuild: bool = False, n: int = 10000) -> dict:
    """Cached simulation results for the API."""
    if SIM_CACHE.exists() and not rebuild:
        return json.loads(SIM_CACHE.read_text(encoding="utf-8"))
    result = run_simulations(n=n, seed=2026)
    SIM_CACHE.write_text(json.dumps(result), encoding="utf-8")
    return result


if __name__ == "__main__":  # pragma: no cover - manual sanity check
    import time
    t0 = time.time()
    res = run_simulations(n=5000, seed=2026)
    print(f"5000 sims in {time.time() - t0:.1f}s")
    top = sorted(res["title_odds"].items(), key=lambda kv: -kv[1])[:12]
    print("Title odds:")
    for team, p in top:
        print(f"  {team:18s} {p:5.1%}")
