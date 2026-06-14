import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ProbBar from "../components/ProbBar";
import { api } from "../api";
import { CONFED_COLOR, code, pct } from "../lib";
import type { Fixture, TeamDetail } from "../types";

const OUTLOOK: { key: keyof TeamDetail; label: string }[] = [
  { key: "qualify_knockout", label: "Reach knockouts" },
  { key: "reach_r16", label: "Reach last 16" },
  { key: "reach_quarter", label: "Reach quarters" },
  { key: "reach_semi", label: "Reach semis" },
  { key: "reach_final", label: "Reach final" },
  { key: "title_odds", label: "Win the cup" },
];

export default function TeamProfileView() {
  const { name = "" } = useParams();
  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setTeam(null);
    setError(false);
    api.team(name).then(setTeam).catch(() => setError(true));
  }, [name]);

  if (error) return <div className="view"><div className="loading">No 2026 team called “{name}”.</div></div>;
  if (!team) return <div className="view"><div className="loading">Loading {name}…</div></div>;

  const accent = CONFED_COLOR[team.confederation];

  return (
    <div className="view team-view">
      <Link to="/simulator" className="back-link">← All teams</Link>

      <header className="team-hero glass">
        <span className="team-hero-code display" style={{ color: accent }}>{code(team.name)}</span>
        <div className="team-hero-meta">
          <h2 className="display team-hero-name">{team.name}</h2>
          <div className="team-tags">
            <span className="chip on">Group {team.group}</span>
            <span className="chip" style={{ borderColor: accent, color: accent }}>
              <i style={{ background: accent }} />{team.confederation}
            </span>
          </div>
        </div>
        <div className="team-hero-odds">
          <span className="label">Title odds</span>
          <span className="display pitch-text team-hero-pct">{pct(team.title_odds, 1)}</span>
        </div>
      </header>

      <div className="stat-cards">
        <StatCard label="Elo rating" value={team.elo.toFixed(0)} />
        <StatCard label="Attack" value={team.attack >= 0 ? `+${team.attack.toFixed(2)}` : team.attack.toFixed(2)} />
        <StatCard label="Defence" value={team.defence >= 0 ? `+${team.defence.toFixed(2)}` : team.defence.toFixed(2)} hint="lower is better" />
      </div>

      <section className="panel-block glass">
        <h3 className="display block-title">Tournament outlook</h3>
        <div className="outlook">
          {OUTLOOK.map((o) => {
            const v = team[o.key] as number;
            return (
              <div key={o.key} className="outlook-row">
                <span className="outlook-label">{o.label}</span>
                <div className="odds-track"><div className="odds-fill" style={{ width: `${v * 100}%` }} /></div>
                <span className="outlook-pct display">{pct(v, 1)}</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="panel-block glass">
        <h3 className="display block-title">Group {team.group} fixtures</h3>
        <div className="fixture-list">
          {team.group_fixtures.map((f, i) => <ProfileFixture key={i} fx={f} self={team.name} />)}
        </div>
      </section>
    </div>
  );
}

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="stat-card glass">
      <span className="label">{label}</span>
      <span className="display stat-value">{value}</span>
      {hint && <span className="stat-hint">{hint}</span>}
    </div>
  );
}

function ProfileFixture({ fx, self }: { fx: Fixture; self: string }) {
  const opp = fx.home === self ? fx.away : fx.home;
  const p = fx.prediction;
  return (
    <div className="fixture-row">
      <div className="fx-teams">
        <span className="fx-team">{code(fx.home)}</span>
        <span className="fx-score display">{p.xg_home.toFixed(1)}<span className="dash">–</span>{p.xg_away.toFixed(1)}</span>
        <span className="fx-team right">{code(fx.away)}</span>
      </div>
      <ProbBar home={p.prob_home} draw={p.prob_draw} away={p.prob_away} />
      <Link to={`/compare?a=${encodeURIComponent(self)}&b=${encodeURIComponent(opp)}`} className="fx-link">
        vs {opp} · full head-to-head →
      </Link>
    </div>
  );
}
