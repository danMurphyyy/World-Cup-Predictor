"""Local, rule-based match previews — no external API, no cost.

Turns the model's numbers (win/draw/loss, expected goals, head-to-head) into a
short data-driven narrative. Deterministic and instant; runs anywhere the model
runs. Not LLM-written — it composes sentences from the figures themselves.
"""
from __future__ import annotations

CODE_HINT = ""  # reserved; previews use full team names


def _favourite(pred: dict, home: str, away: str):
    if pred["prob_home"] >= pred["prob_away"]:
        return home, away, pred["prob_home"], pred["prob_away"]
    return away, home, pred["prob_away"], pred["prob_home"]


def _lede(fav: str, dog: str, fav_p: float, dog_p: float, draw_p: float, idx: int) -> str:
    gap = fav_p - dog_p
    if gap < 0.06:
        options = [
            f"The model can barely separate {fav} and {dog} — a coin-toss of a tie.",
            f"{fav} and {dog} are line-ball: {fav_p:.0%} plays {dog_p:.0%}, with the draw a real third outcome.",
        ]
    elif fav_p >= 0.6:
        options = [
            f"{fav} go in as heavy favourites at {fav_p:.0%} to win.",
            f"The numbers love {fav} here — {fav_p:.0%} to take it, with {dog} given {dog_p:.0%}.",
        ]
    else:
        options = [
            f"{fav} edge it on the model's reckoning, {fav_p:.0%} to {dog_p:.0%}.",
            f"A lean towards {fav} ({fav_p:.0%}), but {dog} ({dog_p:.0%}) are far from out of it.",
        ]
    return options[idx % len(options)]


def _scoring(pred: dict, home: str, away: str) -> str:
    total = pred["xg_home"] + pred["xg_away"]
    if total >= 3.0:
        return f"Expect goals: a projected {pred['xg_home']:.1f}–{pred['xg_away']:.1f} scoreline."
    if total <= 1.9:
        return f"It shapes as a tight, low-scoring affair ({pred['xg_home']:.1f}–{pred['xg_away']:.1f} expected)."
    return f"Expected goals sit at {pred['xg_home']:.1f}–{pred['xg_away']:.1f}."


def _history(h2h: dict, home: str, away: str) -> str:
    played, a, d, b = h2h["played"], h2h["a_wins"], h2h["draws"], h2h["b_wins"]
    if played == 0:
        return f"The two nations have never met — a first-ever meeting."
    if a > b:
        return f"History favours {home}: {a}–{b} (with {d} draws) across {played} meetings."
    if b > a:
        return f"History favours {away}: {b}–{a} (with {d} draws) across {played} meetings."
    return f"They're level all-time, {a}–{b} with {d} draws across {played} meetings."


def generate_preview(pred: dict, h2h: dict, home: str, away: str) -> str:
    """A 2-3 sentence data-driven preview built from the model's figures."""
    fav, dog, fav_p, dog_p = _favourite(pred, home, away)
    idx = (len(home) + len(away)) % 2
    parts = [
        _lede(fav, dog, fav_p, dog_p, pred["prob_draw"], idx),
        _scoring(pred, home, away),
        _history(h2h, home, away),
    ]
    if dog_p >= 0.28 and fav_p - dog_p >= 0.06:
        parts.append(f"Still, {dog} carry genuine upset threat at {dog_p:.0%}.")
    return " ".join(parts)
