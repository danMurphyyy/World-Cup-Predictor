"""Tests for the local, rule-based match-preview generator."""
from backend.model.preview import generate_preview


def _pred(ph, pd, pa, xgh=1.3, xga=1.1):
    return {"prob_home": ph, "prob_draw": pd, "prob_away": pa, "xg_home": xgh, "xg_away": xga}


def test_names_the_favourite():
    pred = _pred(0.62, 0.22, 0.16)
    text = generate_preview(pred, {"played": 5, "a_wins": 3, "draws": 1, "b_wins": 1}, "Spain", "Japan")
    assert "Spain" in text and "62%" in text


def test_mentions_history_or_first_meeting():
    never = generate_preview(_pred(0.5, 0.25, 0.25), {"played": 0, "a_wins": 0, "draws": 0, "b_wins": 0}, "Curaçao", "Norway")
    assert "never met" in never

    met = generate_preview(_pred(0.5, 0.25, 0.25), {"played": 23, "a_wins": 13, "draws": 5, "b_wins": 5}, "Brazil", "Germany")
    assert "23 meetings" in met


def test_flags_upset_threat_for_live_underdog():
    pred = _pred(0.5, 0.18, 0.32)  # away is a live underdog
    text = generate_preview(pred, {"played": 4, "a_wins": 2, "draws": 1, "b_wins": 1}, "France", "Senegal")
    assert "upset" in text and "Senegal" in text


def test_returns_nonempty_string():
    text = generate_preview(_pred(0.4, 0.3, 0.3), {"played": 1, "a_wins": 0, "draws": 1, "b_wins": 0}, "Mexico", "Qatar")
    assert isinstance(text, str) and len(text) > 0
