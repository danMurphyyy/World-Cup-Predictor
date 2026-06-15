export type Confederation =
  | "UEFA" | "CONMEBOL" | "CAF" | "CONCACAF" | "AFC" | "OFC" | "?";

export interface Team {
  name: string;
  group: string;
  confederation: Confederation;
  elo: number;
  attack: number;
  defence: number;
  title_odds: number;
  reach_final: number;
  reach_semi: number;
  reach_quarter: number;
  reach_r16: number;
  qualify_knockout: number;
}

export interface Prediction {
  home: string;
  away: string;
  neutral: boolean;
  xg_home: number;
  xg_away: number;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
}

export interface GraphNode {
  id: string;
  group: string;
  confederation: Confederation;
  elo: number;
  title_odds: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  group: string;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  xg_home: number;
  xg_away: number;
  meetings: number;
  meet_prob?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Fixture {
  group: string;
  home: string;
  away: string;
  prediction: Prediction;
}

export interface SimTeam {
  name: string;
  title_odds: number;
  reach_final: number;
  reach_semi: number;
  reach_quarter: number;
  qualify_knockout: number;
}

export interface SimulationSummary {
  n: number;
  teams: SimTeam[];
}

export interface H2HMatch {
  date: string;
  home: string;
  away: string;
  home_score: number;
  away_score: number;
  tournament: string;
}

export interface H2H {
  team_a: string;
  team_b: string;
  played: number;
  a_wins: number;
  draws: number;
  b_wins: number;
  a_goals: number;
  b_goals: number;
  recent: H2HMatch[];
  prediction: Prediction;
}

export interface TeamDetail extends Team {
  group_fixtures: Fixture[];
}

export interface ScoreMatch {
  date: string;
  home: string;
  away: string;
  home_score: number;
  away_score: number;
  outcome: string;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  xg_home: number;
  xg_away: number;
  prob_actual: number;
  hit: boolean;
}

export interface Preview {
  home: string;
  away: string;
  preview: string;
}

export interface Scoreboard {
  n: number;
  tournament_start: string | null;
  model_log_loss: number | null;
  baseline_log_loss: number | null;
  model_brier: number | null;
  baseline_brier: number | null;
  pick_accuracy: number | null;
  matches: ScoreMatch[];
}
