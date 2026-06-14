import { useEffect, useMemo, useState } from "react";
import ProbBar from "../components/ProbBar";
import { api } from "../api";
import { GROUPS, code } from "../lib";
import type { Fixture } from "../types";

export default function FixturesView() {
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [group, setGroup] = useState<string | null>(null);

  useEffect(() => {
    api.fixtures().then(setFixtures);
  }, []);

  const byGroup = useMemo(() => {
    const map: Record<string, Fixture[]> = {};
    for (const f of fixtures) (map[f.group] ??= []).push(f);
    return map;
  }, [fixtures]);

  const shown = group ? [group] : GROUPS;

  return (
    <div className="view">
      <header className="view-head">
        <div>
          <span className="label">Group stage · model predictions</span>
          <h2 className="display view-title">72 matches, called</h2>
        </div>
        <p className="view-sub">
          Every group fixture with the Dixon-Coles expected goals and win / draw / loss
          probabilities. Bars read green-win · amber-draw · red-loss.
        </p>
      </header>

      <div className="group-tabs">
        <button className={`chip ${!group ? "on" : ""}`} onClick={() => setGroup(null)}>All</button>
        {GROUPS.map((g) => (
          <button key={g} className={`chip ${group === g ? "on" : ""}`} onClick={() => setGroup(g)}>
            {g}
          </button>
        ))}
      </div>

      <div className="group-grid">
        {shown.map((g) => (
          <section key={g} className="group-block glass">
            <h3 className="display group-letter">Group {g}</h3>
            <div className="fixture-list">
              {(byGroup[g] ?? []).map((f, i) => (
                <FixtureRow key={i} fx={f} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function FixtureRow({ fx }: { fx: Fixture }) {
  const p = fx.prediction;
  return (
    <div className="fixture-row">
      <div className="fx-teams">
        <span className="fx-team">{code(fx.home)}</span>
        <span className="fx-score display">
          {p.xg_home.toFixed(1)}<span className="dash">–</span>{p.xg_away.toFixed(1)}
        </span>
        <span className="fx-team right">{code(fx.away)}</span>
      </div>
      <ProbBar home={p.prob_home} draw={p.prob_draw} away={p.prob_away} />
    </div>
  );
}
