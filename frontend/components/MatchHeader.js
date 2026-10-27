"use client";

/*
  MatchHeader: competition line, both teams with crests, the score,
  the clock, goal scorers, and the Kick off + Settings buttons.
*/

import Crest from "./Crest";
import { DATE_LOCALE, useI18n } from "../lib/i18n";

function Scorers({ goals, team, align }) {
  const mine = goals.filter((g) => g.team === team);
  return (
    <ul className={`scorers ${align}`}>
      {mine.map((g) => (
        <li key={g.id}>
          {g.player} {g.minute}&apos;
        </li>
      ))}
    </ul>
  );
}

export default function MatchHeader({ info, score, minute, status, goals, onKickOff, onSettings, profileLabel }) {
  const { t, lang } = useI18n();
  const home = info?.home || "Home";
  const away = info?.away || "Away";

  let clock = t("not_started");
  if (status === "live") clock = `${minute}'`;
  if (status === "finished") clock = t("full_time");
  if (status === "error") clock = t("stream_stopped");

  return (
    <header className="match-header card">
      <div className="header-top">
        <span className="competition">{info?.competition || "AgPitch"}</span>
        <span className="meta">
          {info?.venue}
          {info?.date ? ` · ${new Date(info.date).toLocaleDateString(DATE_LOCALE[lang] || "en-GB", { day: "numeric", month: "short", year: "numeric" })}` : ""}
        </span>
        <div className="header-actions">
          <button type="button" className="btn ghost" onClick={onSettings} aria-label={t("settings")}>
            <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="currentColor"
                d="M19.4 13a7.5 7.5 0 0 0 0-2l2.1-1.6-2-3.5-2.5 1a7.6 7.6 0 0 0-1.7-1L15 3.3h-4l-.4 2.6a7.6 7.6 0 0 0-1.7 1l-2.5-1-2 3.5L6.6 11a7.5 7.5 0 0 0 0 2l-2.1 1.6 2 3.5 2.5-1a7.6 7.6 0 0 0 1.7 1l.4 2.6h4l.4-2.6a7.6 7.6 0 0 0 1.7-1l2.5 1 2-3.5zM13 15.5A3.5 3.5 0 1 1 13 8.5a3.5 3.5 0 0 1 0 7z"
              />
            </svg>
            {profileLabel}
          </button>
          <button type="button" className="btn primary" onClick={onKickOff}>
            {status === "live" ? t("restart") : status === "finished" ? t("watch_again") : t("kick_off")}
          </button>
        </div>
      </div>

      <div className="scoreline">
        <div className="side home">
          <span className="team-name">{home}</span>
          <Crest team={home} />
        </div>

        <div className="score-box">
          <div className="score">
            {score ? score[home] : 0} <span>-</span> {score ? score[away] : 0}
          </div>
          <div className={`clock ${status}`}>
            {status === "live" && <i className="live-dot" />}
            {clock}
          </div>
        </div>

        <div className="side away">
          <Crest team={away} />
          <span className="team-name">{away}</span>
        </div>
      </div>

      <div className="scorers-row">
        <Scorers goals={goals} team={home} align="right" />
        <span className="ball-icon" aria-hidden="true">{goals.length ? "⚽" : ""}</span>
        <Scorers goals={goals} team={away} align="left" />
      </div>
    </header>
  );
}
