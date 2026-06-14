import { useEffect, useMemo, useState } from "react";
import FilterBar from "../components/FilterBar";
import ProbBar from "../components/ProbBar";
import RelationshipGraph from "../components/RelationshipGraph";
import { api } from "../api";
import { CONFEDERATIONS, CONFED_COLOR, code, pct } from "../lib";
import type { Confederation, GraphData, GraphEdge } from "../types";

type Mode = "group" | "knockout";
const edgeKey = (e: GraphEdge | null) => (e ? `${e.source}-${e.target}` : null);

const MODES: { key: Mode; label: string }[] = [
  { key: "group", label: "Group stage" },
  { key: "knockout", label: "Likely knockouts" },
];

export default function GraphView() {
  const [mode, setMode] = useState<Mode>("group");
  const [group, setGroup] = useState<string | null>(null);
  const [confederation, setConfederation] = useState<Confederation | null>(null);
  const [data, setData] = useState<GraphData | null>(null);
  const [edge, setEdge] = useState<GraphEdge | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  const [compareEdge, setCompareEdge] = useState<GraphEdge | null>(null);

  useEffect(() => {
    setEdge(null);
    setCompareEdge(null);
    setPending(null);
    api.graph(mode, group ?? undefined, confederation ?? undefined).then(setData);
  }, [mode, group, confederation]);

  // Click two nodes -> predict that (any) matchup and draw a temporary edge.
  async function handleNode(id: string) {
    if (!pending) { setPending(id); return; }
    if (pending === id) { setPending(null); return; }
    const a = pending;
    setPending(null);
    const h = await api.h2h(a, id);
    const e: GraphEdge = {
      source: a, target: id, group: "CMP",
      prob_home: h.prediction.prob_home, prob_draw: h.prediction.prob_draw,
      prob_away: h.prediction.prob_away, xg_home: h.prediction.xg_home,
      xg_away: h.prediction.xg_away, meetings: h.played,
    };
    setCompareEdge(e);
    setEdge(e);
  }

  const merged = useMemo<GraphData | null>(() => {
    if (!data) return null;
    return compareEdge ? { nodes: data.nodes, edges: [...data.edges, compareEdge] } : data;
  }, [data, compareEdge]);

  return (
    <div className="view graph-view">
      <header className="view-head">
        <div>
          <span className="label">The relationship map</span>
          <h2 className="display view-title">Every team, every connection</h2>
        </div>
        <p className="view-sub">
          Nodes are nations — sized by title odds, coloured by confederation. Switch the
          edge mode below, or <strong className="pitch-text">click any two teams</strong> to
          predict that matchup — group rivals or a dream final.
        </p>
      </header>

      <div className="mode-switch">
        {MODES.map((m) => (
          <button
            key={m.key}
            className={`mode-btn ${mode === m.key ? "on" : ""}`}
            onClick={() => setMode(m.key)}
          >
            {m.label}
          </button>
        ))}
        <span className="mode-hint label">
          {mode === "knockout"
            ? "Thicker line = more likely to actually meet"
            : "Thicker line = tighter predicted contest"}
        </span>
      </div>

      <FilterBar
        group={group}
        confederation={confederation}
        onGroup={setGroup}
        onConfederation={setConfederation}
      />

      <div className="graph-layout">
        <div className="graph-stage glass">
          {merged ? (
            <RelationshipGraph
              data={merged}
              onSelectEdge={setEdge}
              onSelectNode={handleNode}
              selectedEdgeKey={edgeKey(edge)}
              pendingNode={pending}
            />
          ) : (
            <div className="loading">Loading the map…</div>
          )}
          {pending && (
            <div className="compare-banner">
              <span className="display">{code(pending)}</span> selected — click another team to compare
            </div>
          )}
          <div className="legend">
            {CONFEDERATIONS.map((c) => (
              <span key={c} className="legend-item">
                <i style={{ background: CONFED_COLOR[c] }} /> {c}
              </span>
            ))}
          </div>
        </div>

        <aside className="graph-panel glass">
          {edge ? <EdgePanel edge={edge} /> : <EmptyPanel />}
        </aside>
      </div>
    </div>
  );
}

function edgeLabel(edge: GraphEdge): string {
  if (edge.group === "CMP") return "Any-matchup prediction";
  if (edge.meet_prob != null) return `Knockout · ${pct(edge.meet_prob)} likely to meet`;
  return `Group ${edge.group} · predicted`;
}

function EdgePanel({ edge }: { edge: GraphEdge }) {
  return (
    <div className="edge-panel">
      <span className="label">{edgeLabel(edge)}</span>
      <div className="matchup">
        <div className="side">
          <span className="display code">{code(edge.source)}</span>
          <span className="team-name">{edge.source}</span>
        </div>
        <span className="vs">vs</span>
        <div className="side right">
          <span className="display code">{code(edge.target)}</span>
          <span className="team-name">{edge.target}</span>
        </div>
      </div>

      <div className="xg-row">
        <span className="display xg pitch-text">{edge.xg_home.toFixed(2)}</span>
        <span className="label">expected goals</span>
        <span className="display xg" style={{ color: "var(--danger)" }}>{edge.xg_away.toFixed(2)}</span>
      </div>

      <ProbBar home={edge.prob_home} draw={edge.prob_draw} away={edge.prob_away} height={12} />
      <div className="prob-legend">
        <span className="pitch-text">{Math.round(edge.prob_home * 100)}% win</span>
        <span style={{ color: "var(--warn)" }}>{Math.round(edge.prob_draw * 100)}% draw</span>
        <span style={{ color: "var(--danger)" }}>{Math.round(edge.prob_away * 100)}% win</span>
      </div>

      <div className="meta-row">
        <span className="label">All-time meetings</span>
        <span className="display meetings">{edge.meetings}</span>
      </div>
    </div>
  );
}

function EmptyPanel() {
  return (
    <div className="empty-panel">
      <div className="pulse-dot" />
      <p className="display empty-title">Pick a matchup</p>
      <p className="view-sub">
        Click a line for that fixture, or click any two team nodes to predict a matchup
        that isn't on the map yet — quarter-final, final, anything.
      </p>
    </div>
  );
}
