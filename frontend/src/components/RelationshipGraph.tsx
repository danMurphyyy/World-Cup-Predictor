import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { confedColor, code } from "../lib";
import type { GraphData, GraphEdge } from "../types";

interface Props {
  data: GraphData;
  onSelectEdge: (edge: GraphEdge | null) => void;
  onSelectNode: (id: string) => void;
  selectedEdgeKey: string | null;
  pendingNode: string | null;
}

const edgeKey = (e: { source: any; target: any }) =>
  `${typeof e.source === "object" ? e.source.id : e.source}-${typeof e.target === "object" ? e.target.id : e.target}`;

/** Force-directed graph of teams (nodes) and group matchups (edges). */
export default function RelationshipGraph({
  data, onSelectEdge, onSelectNode, selectedEdgeKey, pendingNode,
}: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 800, h: 560 });
  const [hoverNode, setHoverNode] = useState<string | null>(null);

  useEffect(() => {
    if (!wrap.current) return;
    const ro = new ResizeObserver(([entry]) => {
      setDims({ w: entry.contentRect.width, h: entry.contentRect.height });
    });
    ro.observe(wrap.current);
    return () => ro.disconnect();
  }, []);

  // react-force-graph wants {nodes, links}; keep prediction fields on each link.
  const graphData = useMemo(
    () => ({
      nodes: data.nodes.map((n) => ({ ...n })),
      links: data.edges.map((e) => ({ ...e })),
    }),
    [data],
  );

  const maxOdds = Math.max(0.01, ...data.nodes.map((n) => n.title_odds));

  return (
    <div ref={wrap} className="graph-canvas">
      <ForceGraph2D
        width={dims.w}
        height={dims.h}
        graphData={graphData}
        cooldownTicks={120}
        backgroundColor="rgba(0,0,0,0)"
        nodeRelSize={1}
        linkCurvature={0.18}
        onNodeHover={(n: any) => setHoverNode(n ? n.id : null)}
        linkColor={(l: any) => {
          const key = edgeKey(l);
          if (key === selectedEdgeKey) return "rgba(57,255,136,0.95)";
          const touches = hoverNode && (l.source.id === hoverNode || l.target.id === hoverNode);
          if (touches) return "rgba(57,255,136,0.8)";
          // Dim everything else; when hovering a node, fade the rest right back.
          return hoverNode ? "rgba(120,160,140,0.06)" : "rgba(120,160,140,0.12)";
        }}
        linkWidth={(l: any) => {
          // Knockout edges: thickness = how likely the pair is to meet.
          // Group edges: thickness = how tight the predicted contest is.
          const base =
            l.meet_prob != null
              ? 0.6 + l.meet_prob * 7
              : 0.6 + (1 - Math.abs(l.prob_home - l.prob_away)) * 3;
          return edgeKey(l) === selectedEdgeKey ? base + 2 : base;
        }}
        onNodeClick={(n: any) => onSelectNode(n.id)}
        onLinkClick={(l: any) =>
          onSelectEdge({
            ...l,
            source: typeof l.source === "object" ? l.source.id : l.source,
            target: typeof l.target === "object" ? l.target.id : l.target,
          } as GraphEdge)
        }
        onBackgroundClick={() => onSelectEdge(null)}
        nodeCanvasObject={(node: any, ctx, scale) => {
          const r = 5 + (node.title_odds / maxOdds) * 13;
          const color = confedColor(node.confederation);
          const active = node.id === hoverNode || node.id === pendingNode;

          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
          ctx.fillStyle = active ? "rgba(57,255,136,0.18)" : "rgba(10,18,14,0.85)";
          ctx.fill();
          ctx.lineWidth = active ? 2.5 : 1.6;
          ctx.strokeStyle = active ? "#39ff88" : color;
          if (active) { ctx.shadowColor = "#39ff88"; ctx.shadowBlur = 18; }
          ctx.stroke();
          ctx.shadowBlur = 0;

          const fontSize = Math.max(8, r * 0.8);
          ctx.font = `700 ${fontSize}px Archivo, sans-serif`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillStyle = active ? "#eafff3" : color;
          ctx.fillText(code(node.id), node.x, node.y);
          void scale;
        }}
        nodePointerAreaPaint={(node: any, color, ctx) => {
          const r = 5 + (node.title_odds / maxOdds) * 13;
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, r + 2, 0, 2 * Math.PI);
          ctx.fill();
        }}
      />
    </div>
  );
}
