interface Props {
  home: number;
  draw: number;
  away: number;
  height?: number;
}

/** Stacked win / draw / loss probability bar. */
export default function ProbBar({ home, draw, away, height = 8 }: Props) {
  return (
    <div className="prob-bar" style={{ height }} title={`${pct(home)} / ${pct(draw)} / ${pct(away)}`}>
      <span style={{ width: `${home * 100}%`, background: "var(--pitch)" }} />
      <span style={{ width: `${draw * 100}%`, background: "var(--warn)" }} />
      <span style={{ width: `${away * 100}%`, background: "var(--danger)" }} />
    </div>
  );
}

const pct = (x: number) => `${Math.round(x * 100)}%`;
