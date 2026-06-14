import type { Fixture, GraphData, H2H, Prediction, SimulationSummary, Team } from "./types";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  teams: () => get<Team[]>("/teams"),
  graph: (mode: string, group?: string, confederation?: string) => {
    const q = new URLSearchParams();
    q.set("mode", mode);
    if (group) q.set("group", group);
    if (confederation) q.set("confederation", confederation);
    return get<GraphData>(`/graph?${q.toString()}`);
  },
  fixtures: (group?: string) =>
    get<Fixture[]>(`/fixtures${group ? `?group=${group}` : ""}`),
  predict: (home: string, away: string) =>
    get<Prediction>(`/predict?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`),
  simulate: () => get<SimulationSummary>("/simulate"),
  h2h: (a: string, b: string) =>
    get<H2H>(`/h2h?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`),
};
