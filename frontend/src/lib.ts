import type { Confederation } from "./types";

/** Three-letter codes for the 48 teams (dataset spelling -> FIFA-style code). */
export const TEAM_CODE: Record<string, string> = {
  "Czech Republic": "CZE", Mexico: "MEX", "South Africa": "RSA", "South Korea": "KOR",
  "Bosnia and Herzegovina": "BIH", Canada: "CAN", Qatar: "QAT", Switzerland: "SUI",
  Brazil: "BRA", Haiti: "HAI", Morocco: "MAR", Scotland: "SCO",
  Australia: "AUS", Paraguay: "PAR", Turkey: "TUR", "United States": "USA",
  "Curaçao": "CUW", Ecuador: "ECU", Germany: "GER", "Ivory Coast": "CIV",
  Japan: "JPN", Netherlands: "NED", Sweden: "SWE", Tunisia: "TUN",
  Belgium: "BEL", Egypt: "EGY", Iran: "IRN", "New Zealand": "NZL",
  "Cape Verde": "CPV", "Saudi Arabia": "KSA", Spain: "ESP", Uruguay: "URU",
  France: "FRA", Iraq: "IRQ", Norway: "NOR", Senegal: "SEN",
  Algeria: "ALG", Argentina: "ARG", Austria: "AUT", Jordan: "JOR",
  Colombia: "COL", "DR Congo": "COD", Portugal: "POR", Uzbekistan: "UZB",
  Croatia: "CRO", England: "ENG", Ghana: "GHA", Panama: "PAN",
};

export const code = (name: string) =>
  TEAM_CODE[name] ?? name.slice(0, 3).toUpperCase();

export const CONFED_COLOR: Record<Confederation, string> = {
  UEFA: "#5ec5ff", CONMEBOL: "#ffd24a", CAF: "#ff8a4a",
  CONCACAF: "#ff5db0", AFC: "#b388ff", OFC: "#46e0c8", "?": "#9db3a8",
};

export const confedColor = (c: string): string =>
  CONFED_COLOR[c as Confederation] ?? CONFED_COLOR["?"];

export const CONFEDERATIONS: Confederation[] = [
  "UEFA", "CONMEBOL", "CAF", "CONCACAF", "AFC", "OFC",
];

export const GROUPS = "ABCDEFGHIJKL".split("");

export const pct = (x: number, digits = 0) => `${(x * 100).toFixed(digits)}%`;
