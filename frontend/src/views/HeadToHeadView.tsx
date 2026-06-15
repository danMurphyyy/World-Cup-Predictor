import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import ProbBar from "../components/ProbBar";
import { api } from "../api";
import { code } from "../lib";
import type { H2H, Preview, Team } from "../types";

export default function HeadToHeadView() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [params, setParams] = useSearchParams();
  const a = params.get("a") ?? "Brazil";
  const b = params.get("b") ?? "Argentina";
  const [h2h, setH2h] = useState<H2H | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);

  useEffect(() => {
    api.teams().then((t) => setTeams([...t].sort((x, y) => x.name.localeCompare(y.name))));
  }, []);

  useEffect(() => {
    if (a === b) { setH2h(null); setPreview(null); return; }
    setH2h(null);
    setPreview(null);
    api.h2h(a, b).then(setH2h);
    api.preview(a, b).then(setPreview);
  }, [a, b]);

  const setTeam = (slot: "a" | "b", value: string) => {
    const next = new URLSearchParams(params);
    next.set(slot, value);
    setParams(next, { replace: true });
  };

  return (
    <div className="view">
      <header className="view-head">
        <div>
          <span className="label">Head-to-head</span>
          <h2 className="display view-title">Any two nations, compared</h2>
        </div>
        <p className="view-sub">
          Pick two teams for the model's predicted matchup and their full historical record.
        </p>
      </header>

      <div className="h2h-pickers">
        <TeamSelect teams={teams} value={a} onChange={(v) => setTeam("a", v)} />
        <span className="h2h-vs display">vs</span>
        <TeamSelect teams={teams} value={b} onChange={(v) => setTeam("b", v)} />
      </div>

      {a !== b && preview && (
        <div className="story glass">
          <span className="label">The numbers say</span>
          <p className="story-text">{preview.preview}</p>
        </div>
      )}

      {a === b ? (
        <div className="loading">Pick two different teams.</div>
      ) : !h2h ? (
        <div className="loading">Loading {a} vs {b}…</div>
      ) : (
        <div className="h2h-grid">
          <section className="panel-block glass">
            <h3 className="display block-title">Predicted matchup</h3>
            <div className="matchup">
              <Link to={`/team/${encodeURIComponent(a)}`} className="side">
                <span className="display code">{code(a)}</span><span className="team-name">{a}</span>
              </Link>
              <span className="vs">vs</span>
              <Link to={`/team/${encodeURIComponent(b)}`} className="side right">
                <span className="display code">{code(b)}</span><span className="team-name">{b}</span>
              </Link>
            </div>
            <div className="xg-row">
              <span className="display xg pitch-text">{h2h.prediction.xg_home.toFixed(2)}</span>
              <span className="label">expected goals</span>
              <span className="display xg" style={{ color: "var(--danger)" }}>{h2h.prediction.xg_away.toFixed(2)}</span>
            </div>
            <ProbBar home={h2h.prediction.prob_home} draw={h2h.prediction.prob_draw} away={h2h.prediction.prob_away} height={12} />
            <div className="prob-legend">
              <span className="pitch-text">{Math.round(h2h.prediction.prob_home * 100)}% {code(a)}</span>
              <span style={{ color: "var(--warn)" }}>{Math.round(h2h.prediction.prob_draw * 100)}% draw</span>
              <span style={{ color: "var(--danger)" }}>{Math.round(h2h.prediction.prob_away * 100)}% {code(b)}</span>
            </div>
          </section>

          <section className="panel-block glass">
            <h3 className="display block-title">All-time record · {h2h.played} meetings</h3>
            {h2h.played > 0 ? (
              <>
                <div className="record-bar">
                  <span style={{ flex: h2h.a_wins, background: "var(--pitch)" }} />
                  <span style={{ flex: h2h.draws, background: "var(--warn)" }} />
                  <span style={{ flex: h2h.b_wins, background: "var(--danger)" }} />
                </div>
                <div className="record-legend">
                  <span><b className="pitch-text">{h2h.a_wins}</b> {code(a)} wins</span>
                  <span><b style={{ color: "var(--warn)" }}>{h2h.draws}</b> draws</span>
                  <span><b style={{ color: "var(--danger)" }}>{h2h.b_wins}</b> {code(b)} wins</span>
                </div>
                <div className="goals-row">Goals: <b>{h2h.a_goals}</b> – <b>{h2h.b_goals}</b></div>
                <div className="recent">
                  {h2h.recent.slice().reverse().map((m, i) => (
                    <div key={i} className="recent-row">
                      <span className="recent-date">{m.date}</span>
                      <span className="recent-score">{code(m.home)} {m.home_score}–{m.away_score} {code(m.away)}</span>
                      <span className="recent-comp">{m.tournament}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="view-sub">These teams have never met.</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

function TeamSelect({ teams, value, onChange }: { teams: Team[]; value: string; onChange: (v: string) => void }) {
  return (
    <select className="team-select" value={value} onChange={(e) => onChange(e.target.value)}>
      {teams.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
    </select>
  );
}
