/*
  Team colours. Ultras are red, Kryptonites are white.
  To swap them, change the two entries below.
*/

export const TEAM_STYLE = {
  Ultras: { color: "#e5202f", text: "#ffffff", short: "U" },
  Kryptonites: { color: "#f2f2f2", text: "#111111", short: "K" },
};

export function teamStyle(team) {
  return TEAM_STYLE[team] || { color: "#888888", text: "#ffffff", short: (team || "?")[0] };
}
