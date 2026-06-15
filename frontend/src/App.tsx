import { useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import GraphView from "./views/GraphView";
import FixturesView from "./views/FixturesView";
import SimulatorView from "./views/SimulatorView";
import HeadToHeadView from "./views/HeadToHeadView";
import TeamProfileView from "./views/TeamProfileView";
import ScoreboardView from "./views/ScoreboardView";

const LINKS = [
  { to: "/graph", label: "Graph" },
  { to: "/fixtures", label: "Fixtures" },
  { to: "/simulator", label: "Simulator" },
  { to: "/scoreboard", label: "Scoreboard" },
  { to: "/compare", label: "Compare" },
];

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div className="app">
      <header className="topbar">
        <div className="bar-inner">
          <div className="brand">
            <span className="brand-ball">⚽</span>
            <span className="display brand-mark">WC<span className="pitch-text">26</span></span>
            <span className="brand-sub">Predictor</span>
          </div>
          <button
            className={`hamburger ${menuOpen ? "open" : ""}`}
            aria-label="Toggle navigation"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <span /><span /><span />
          </button>
          <nav className={`nav ${menuOpen ? "open" : ""}`}>
            {LINKS.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
                onClick={() => setMenuOpen(false)}
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
          <div className="topbar-tag label">Dixon-Coles · Elo · Monte-Carlo</div>
        </div>
      </header>

      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/graph" replace />} />
          <Route path="/graph" element={<GraphView />} />
          <Route path="/fixtures" element={<FixturesView />} />
          <Route path="/simulator" element={<SimulatorView />} />
          <Route path="/scoreboard" element={<ScoreboardView />} />
          <Route path="/compare" element={<HeadToHeadView />} />
          <Route path="/team/:name" element={<TeamProfileView />} />
        </Routes>
      </main>

      <footer className="foot">
        <div className="bar-inner foot-inner">
          <span>Model fit on 49k internationals (1872–2026).</span>
          <span className="foot-dim">Predictions are probabilistic — not betting advice.</span>
        </div>
      </footer>
    </div>
  );
}
