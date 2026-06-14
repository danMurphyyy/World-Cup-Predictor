import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { code, pct } from "../lib";
import type { SimTeam, SimulationSummary } from "../types";

type Metric = "title_odds" | "reach_final" | "reach_semi" | "reach_quarter";

const METRICS: { key: Metric; label: string }[] = [
  { key: "title_odds", label: "Win it" },
  { key: "reach_final", label: "Reach final" },
  { key: "reach_semi", label: "Reach semis" },
  { key: "reach_quarter", label: "Reach QFs" },
];

export default function SimulatorView() {
  const [sim, setSim] = useState<SimulationSummary | null>(null);
  const [metric, setMetric] = useState<Metric>("title_odds");

  useEffect(() => {
    api.simulate().then(setSim);
  }, []);

  const ranked = useMemo(() => {
    if (!sim) return [];
    return [...sim.teams].sort((a, b) => b[metric] - a[metric]);
  }, [sim, metric]);

  if (!sim) return <div className="view"><div className="loading">Running 10,000 tournaments…</div></div>;

  const [first, second, third] = ranked;

  return (
    <div className="view">
      <header className="view-head">
        <div>
          <span className="label">{sim.n.toLocaleString()} simulated tournaments</span>
          <h2 className="display view-title">Who lifts the trophy?</h2>
        </div>
        <p className="view-sub">
          Each tournament is played out match-by-match from the model. Run {sim.n.toLocaleString()}{" "}
          times, here's how often each nation gets where.
        </p>
      </header>

      <div className="podium">
        {[second, first, third].map((t, i) => (
          <Podium key={t.name} team={t} place={i === 1 ? 1 : i === 0 ? 2 : 3} metric={metric} />
        ))}
      </div>

      <div className="group-tabs">
        {METRICS.map((m) => (
          <button
            key={m.key}
            className={`chip ${metric === m.key ? "on" : ""}`}
            onClick={() => setMetric(m.key)}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="odds-list glass">
        {ranked.map((t, i) => (
          <div key={t.name} className="odds-row">
            <span className="odds-rank">{i + 1}</span>
            <span className="odds-code">{code(t.name)}</span>
            <span className="odds-name">{t.name}</span>
            <div className="odds-track">
              <div className="odds-fill" style={{ width: `${t[metric] * 100}%` }} />
            </div>
            <span className="odds-pct display">{pct(t[metric], 1)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Podium({ team, place, metric }: { team: SimTeam; place: number; metric: Metric }) {
  return (
    <div className={`podium-card glass place-${place}`}>
      <span className="podium-place display">{place}</span>
      <span className="display podium-code">{code(team.name)}</span>
      <span className="podium-name">{team.name}</span>
      <span className="podium-pct display pitch-text">{pct(team[metric], 1)}</span>
    </div>
  );
}
