/*
  Crest: a simple shield badge in the team's colour.
*/

import { teamStyle } from "../lib/teams";

export default function Crest({ team, size = 44 }) {
  const style = teamStyle(team);
  return (
    <svg width={size} height={size * 1.15} viewBox="0 0 40 46" aria-hidden="true">
      <path
        d="M20 2 L37 8 V22 C37 33 29.5 40.5 20 44 C10.5 40.5 3 33 3 22 V8 Z"
        fill={style.color}
        stroke="rgba(255,255,255,0.25)"
        strokeWidth="1.5"
      />
      <path d="M20 6 L33 10.5 V22 C33 30.5 27.5 36.5 20 39.5 Z" fill="rgba(0,0,0,0.12)" />
      <text x="20" y="28" textAnchor="middle" fontSize="17" fontWeight="800" fill={style.text}>
        {style.short}
      </text>
    </svg>
  );
}
