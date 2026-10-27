"use client";

/*
  StatsTab: FotMob-style top stats (from the Stats Engine, no AI)
  and a shot map built from the shot events.
*/

import { useState } from "react";
import { teamStyle } from "../lib/teams";
import { useI18n } from "../lib/i18n";

const ROWS = [
  { key: "pass_accuracy_pct", unit: "%" },
  { key: "passes", unit: "" },
  { key: "avg_pass_difficulty", unit: "" },
  { key: "passes_under_pressure_pct", unit: "%", lowerIsBetter: true },
  { key: "shots", unit: "" },
  { key: "shots_on_target", unit: "" },
  { key: "fastest_shot_kmh", unit: " km/h" },
  { key: "saves", unit: "" },
  { key: "corners", unit: "" },
  { key: "counter_attacks", unit: "" },
  { key: "tackles", unit: "" },
  { key: "interceptions", unit: "" },
  { key: "turnovers", unit: "", lowerIsBetter: true },
  { key: "fouls", unit: "", lowerIsBetter: true },
  { key: "yellow_cards", unit: "", lowerIsBetter: true },
  { key: "red_cards", unit: "", lowerIsBetter: true },
];

function Value({ value, unit, highlight, team }) {
  const style = teamStyle(team);
  return (
    <span
      className={highlight ? "value hl" : "value"}
      style={highlight ? { background: style.color, color: style.text } : undefined}
    >
      {value}
      {unit}
    </span>
  );
}

function TopStats({ stats, info }) {
  const { t } = useI18n();
  const home = info.home;
  const away = info.away;
  const h = stats.teams[home];
  const a = stats.teams[away];
  const hs = teamStyle(home);
  const as = teamStyle(away);

  return (
    <section className="card">
      <div className="card-title center">
        <h2>{t("top_stats")}</h2>
      </div>

      <div className="possession">
        <div className="possession-label">{t("ball_possession")}</div>
        <div className="possession-bar">
          <div style={{ width: `${h.possession_pct}%`, background: hs.color, color: hs.text }}>
            {h.possession_pct}%
          </div>
          <div style={{ width: `${a.possession_pct}%`, background: as.color, color: as.text }}>
            {a.possession_pct}%
          </div>
        </div>
        {h.possession_last_10_min_pct != null && (
          <div className="possession-sub">
            {t("last_10")}: {home} {h.possession_last_10_min_pct}% · {away} {a.possession_last_10_min_pct}%
          </div>
        )}
      </div>

      <ul className="stat-rows">
        {ROWS.map(({ key, unit, lowerIsBetter }) => {
          const hv = Number(h[key] ?? 0);
          const av = Number(a[key] ?? 0);
          const homeBetter = lowerIsBetter ? hv < av : hv > av;
          const awayBetter = lowerIsBetter ? av < hv : av > hv;
          return (
            <li key={key}>
              <Value value={h[key] ?? 0} unit={unit} highlight={homeBetter} team={home} />
              <span className="stat-name">{t(`stat_${key}`)}</span>
              <Value value={a[key] ?? 0} unit={unit} highlight={awayBetter} team={away} />
            </li>
          );
        })}
      </ul>
    </section>
  );
}

const W = 105;
const H = 68;

// Shots come from the shooter's point of view (100 = goal they attack).
// Home attacks right, away attacks left.
function shotPoint(shot, home) {
  const [x, y] = shot.start;
  return shot.team === home ? [(x / 100) * W, (y / 100) * H] : [((100 - x) / 100) * W, ((100 - y) / 100) * H];
}

function ShotMap({ shots, info }) {
  const { t } = useI18n();
  const [selected, setSelected] = useState(null);
  const home = info.home;
  const away = info.away;
  const current = selected ?? shots[shots.length - 1];

  return (
    <section className="card">
      <div className="card-title center">
        <h2>{t("shot_map")}</h2>
      </div>

      <div className="shotmap-legend">
        <span>← {t("attack", { team: away })}</span>
        <span>{t("attack", { team: home })} →</span>
      </div>

      <svg className="shotmap" viewBox={`-1 -1 ${W + 2} ${H + 2}`} role="img" aria-label={t("shot_map")}>
        <rect x="0" y="0" width={W} height={H} className="sm-pitch" />
        <g className="sm-lines">
          <rect x="0" y="0" width={W} height={H} />
          <line x1={W / 2} y1="0" x2={W / 2} y2={H} />
          <circle cx={W / 2} cy={H / 2} r="9.15" />
          <rect x="0" y={(H - 40.3) / 2} width="16.5" height="40.3" />
          <rect x={W - 16.5} y={(H - 40.3) / 2} width="16.5" height="40.3" />
          <rect x="0" y={(H - 18.3) / 2} width="5.5" height="18.3" />
          <rect x={W - 5.5} y={(H - 18.3) / 2} width="5.5" height="18.3" />
        </g>
        {shots.map((shot) => {
          const [cx, cy] = shotPoint(shot, home);
          const style = teamStyle(shot.team);
          const goal = shot.outcome === "goal";
          const r = 0.9 + (shot.shot_speed_kmh / 120) * 1.4;
          const isCurrent = current && current.id === shot.id;
          return (
            <circle
              key={shot.id}
              cx={cx}
              cy={cy}
              r={goal ? r + 0.6 : r}
              fill={goal || shot.on_target ? style.color : "transparent"}
              stroke={style.color}
              strokeWidth={isCurrent ? 0.9 : 0.45}
              opacity={isCurrent ? 1 : 0.75}
              className="sm-shot"
              onClick={() => setSelected(shot)}
            >
              <title>{`${shot.player} ${shot.minute}' · ${shot.outcome}`}</title>
            </circle>
          );
        })}
      </svg>

      <div className="shotmap-key">
        <span><i className="key filled" /> {t("on_target")}</span>
        <span><i className="key" /> {t("off_target_key")}</span>
        <span>{t("bigger_faster")}</span>
      </div>

      {current ? (
        <div className="shot-detail">
          <div className="shot-player">
            <strong>{current.player}</strong>
            <span className="muted">{current.team} · {current.minute}&apos;</span>
          </div>
          <dl>
            <div><dt>{t("result")}</dt><dd>{t(`outcome_${current.outcome}`)}</dd></div>
            <div><dt>{t("shot_speed")}</dt><dd>{current.shot_speed_kmh} km/h</dd></div>
            <div><dt>{t("on_target")}</dt><dd>{current.on_target ? t("yes") : t("no")}</dd></div>
            <div><dt>{t("under_pressure")}</dt><dd>{current.under_pressure ? t("yes") : t("no")}</dd></div>
          </dl>
        </div>
      ) : (
        <p className="empty">{t("no_shots")}</p>
      )}
      <div className="shot-count">
        <span style={{ color: teamStyle(home).color }}>{shots.filter((s) => s.team === home).length}</span>
        <span className="muted">{t("shots")}</span>
        <span style={{ color: teamStyle(away).color }}>{shots.filter((s) => s.team === away).length}</span>
      </div>
    </section>
  );
}

export default function StatsTab({ stats, info, events }) {
  const { t } = useI18n();
  if (!stats || !info) {
    return <section className="card"><p className="empty">{t("stats_appear")}</p></section>;
  }
  const shots = events.filter((e) => e.type === "shot");
  return (
    <div className="stats-grid">
      <ShotMap shots={shots} info={info} />
      <TopStats stats={stats} info={info} />
    </div>
  );
}
