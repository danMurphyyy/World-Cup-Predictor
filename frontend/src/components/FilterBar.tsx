import { CONFEDERATIONS, CONFED_COLOR, GROUPS } from "../lib";
import type { Confederation } from "../types";

interface Props {
  group: string | null;
  confederation: Confederation | null;
  onGroup: (g: string | null) => void;
  onConfederation: (c: Confederation | null) => void;
}

/** Structural filters: group (A–L) and confederation. Chips toggle on/off. */
export default function FilterBar({ group, confederation, onGroup, onConfederation }: Props) {
  return (
    <div className="filterbar glass">
      <div className="filter-row">
        <span className="label">Group</span>
        <div className="chips">
          {GROUPS.map((g) => (
            <button
              key={g}
              className={`chip ${group === g ? "on" : ""}`}
              onClick={() => onGroup(group === g ? null : g)}
            >
              {g}
            </button>
          ))}
        </div>
      </div>
      <div className="filter-row">
        <span className="label">Confederation</span>
        <div className="chips">
          {CONFEDERATIONS.map((c) => (
            <button
              key={c}
              className={`chip ${confederation === c ? "on" : ""}`}
              style={confederation === c ? { borderColor: CONFED_COLOR[c], color: CONFED_COLOR[c] } : undefined}
              onClick={() => onConfederation(confederation === c ? null : c)}
            >
              <i style={{ background: CONFED_COLOR[c] }} />
              {c}
            </button>
          ))}
        </div>
      </div>
      {(group || confederation) && (
        <button className="chip clear" onClick={() => { onGroup(null); onConfederation(null); }}>
          Clear ✕
        </button>
      )}
    </div>
  );
}
