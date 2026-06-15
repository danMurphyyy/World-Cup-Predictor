import { useEffect, useState } from "react";
import { api } from "../api";
import { code, pct } from "../lib";
import type { ScoreMatch, Scoreboard } from "../types";

export default function ScoreboardView() {
  const [sb, setSb] = useState<Scoreboard | null>(null);

  useEffect(() => { api.scoreboard().then(setSb); }, []);

  if (!sb) return <div className="view"><div className="loading">Scoring the tournament…</div></div>;

  if (!sb.n) {
    return (
      <div className="view">
        <header className="view-head">
          <span className="label">Model vs reality</span>
          <h2 className="display view-title">Locked in, awaiting kickoff</h2>
          <p className="view-sub">Predictions are locked. Scores appear here as matches are played.</p>
        </header>
      </div>
    );
  }

  const leading = (sb.model_log_loss ?? 1) < (sb.baseline_log_loss ?? 1);

  return (
    <div className="view">
      <header className="view-head">
        <div>
          <span className="label">Model vs reality · live</span>
          <h2 className="display view-title">Graded by the real World Cup</h2>
        </div>
        <p className="view-sub">
          The model was <strong className="pitch-text">locked before kickoff</strong> (fit only on
          matches before {sb.tournament_start}), then scored against every real result since — no
          hindsight. Updates as matches are played.
        </p>
      </header>

      <div className="sb-cards">
        <div className="sb-card glass">
          <span className="label">Matches scored</span>
          <span className="display sb-value">{sb.n}</span>
        </div>
        <div className="sb-card glass">
          <span className="label">Correct calls</span>
          <span className="display sb-value pitch-text">{pct(sb.pick_accuracy ?? 0)}</span>
          <span className="stat-hint">most-likely outcome was right</span>
        </div>
        <div className={`sb-card glass ${leading ? "sb-lead" : ""}`}>
          <span className="label">Log-loss vs baseline</span>
          <span className="display sb-value">
            {sb.model_log_loss?.toFixed(3)}
            <span className="sb-vs"> vs {sb.baseline_log_loss?.toFixed(3)}</span>
          </span>
          <span className="stat-hint">{leading ? "model leading — lower is better" : "baseline ahead so far — lower is better"}</span>
        </div>
      </div>

      <div className="sb-feed">
        {sb.matches.map((m, i) => <ScoreRow key={i} m={m} />)}
      </div>
    </div>
  );
}

function ScoreRow({ m }: { m: ScoreMatch }) {
  return (
    <div className={`sb-row glass ${m.hit ? "hit" : "miss"}`}>
      <span className="sb-date">{m.date}</span>
      <div className="sb-result">
        <span className="sb-team">{code(m.home)}</span>
        <span className="sb-score display">{m.home_score}–{m.away_score}</span>
        <span className="sb-team right">{code(m.away)}</span>
      </div>
      <div className="sb-bar prob-bar">
        <span style={{ width: `${m.prob_home * 100}%`, background: "var(--pitch)" }} />
        <span style={{ width: `${m.prob_draw * 100}%`, background: "var(--warn)" }} />
        <span style={{ width: `${m.prob_away * 100}%`, background: "var(--danger)" }} />
      </div>
      <span className="sb-call">
        <span className={`sb-badge ${m.hit ? "ok" : "x"}`}>{m.hit ? "✓" : "✗"}</span>
        gave <b>{pct(m.prob_actual)}</b> to result
      </span>
    </div>
  );
}
