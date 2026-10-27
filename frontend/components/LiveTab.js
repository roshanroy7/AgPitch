"use client";

/*
  LiveTab: the AI insight cards (left) and the live commentary (right).
  All fixed text comes from lib/i18n.js, so it follows the viewer's language.
*/

import Crest from "./Crest";
import { commentaryLine, momentHeadline, useI18n } from "../lib/i18n";

// Commentary lines that should stand out
const KEY_TYPES = ["save", "counter_attack", "corner", "moment", "yellow_card", "red_card", "injury"];

// Moments that already have their own commentary line from the event itself
const ALREADY_IN_COMMENTARY = [
  "goal", "half_time", "full_time", "speed_alert", "rocket_shot",
  "big_save", "counter_attack", "yellow_card", "red_card",
];

function PendingCard({ moment, info }) {
  const { t, lang } = useI18n();
  return (
    <li className="insight pending">
      <div className="insight-top">
        <span className="minute-pill">{moment.minute}&apos;</span>
        {moment.team && <Crest team={moment.team} size={16} />}
        <span className="tag">{t("analysing")}</span>
      </div>
      <h3>{momentHeadline(lang, moment, info)}</h3>
      <p className="thinking">
        <i /><i /><i /> {t("pundit_thinking")}
      </p>
      <div className="agents">
        <span className="agents-label">{t("flagged_by")}</span>
        <span className="agent engine">{t("stats_engine")}</span>
      </div>
    </li>
  );
}

function InsightCard({ item }) {
  const { t } = useI18n();
  const { moment, card, analysis, fallback, latency_s, computed_s } = item;
  const importance = analysis?.importance || 1;
  return (
    <li className={`insight ${moment.kind === "goal" ? "is-goal" : ""}`}>
      <div className="insight-top">
        <span className="minute-pill">{moment.minute}&apos;</span>
        {moment.team && <Crest team={moment.team} size={16} />}
        {analysis?.theme && <span className="tag">{t(`theme_${analysis.theme}`)}</span>}
        <span className="importance" aria-label={t("importance", { n: importance })}>
          {[1, 2, 3, 4, 5].map((n) => (
            <i key={n} className={n <= importance ? "on" : ""} />
          ))}
        </span>
      </div>
      <h3>{card?.headline}</h3>
      {card?.body && <p>{card.body}</p>}
      {card?.stat && (
        <div className="stat-chip">
          <span>{card.stat.label}</span>
          <strong>{String(card.stat.value)}</strong>
        </div>
      )}
      {(card?.why || analysis?.insight) && (
        <details>
          <summary>{t("why_it_matters")}</summary>
          {/* the Fan agent's version is in the viewer's language; fall back to the Pundit's */}
          <p>{card?.why || analysis.insight}</p>
        </details>
      )}

      {/* Which agents produced this card */}
      <div className="agents">
        <span className="agents-label">{t("made_by")}</span>
        <span className="agent engine">{t("stats_engine")}</span>
        {fallback ? (
          <span className="agents-time">{t("agents_unavailable")}</span>
        ) : (
          <>
            <span className="agent">Pundit</span>
            <span className="agent">Overlay</span>
            <span className="agent">Fan</span>
            <span className="agents-time">
              {latency_s < 0.5 && computed_s ? t("prepared", { s: computed_s }) : `${latency_s}s`}
            </span>
          </>
        )}
      </div>
    </li>
  );
}

export default function LiveTab({ insights, events, moments, status, info }) {
  const { t, lang } = useI18n();

  // Commentary = the main match events + the key moments flagged by the Stats Engine
  const fromEvents = events
    .map((e) => ({
      key: `e${e.id}`, minute: e.minute, second: e.second, team: e.team, type: e.type,
      text: commentaryLine(lang, e),
    }))
    .filter((e) => e.text);
  const fromMoments = moments
    .filter((m) => !ALREADY_IN_COMMENTARY.includes(m.kind))
    .map((m, i) => ({
      key: `m${i}`, minute: m.minute, second: m.second, team: m.team, type: "moment",
      text: momentHeadline(lang, m, info),
    }));
  const commentary = [...fromEvents, ...fromMoments]
    .sort((a, b) => b.minute * 60 + b.second - (a.minute * 60 + a.second))
    .slice(0, 60);

  // One card per key moment, in match order (newest first). It appears the instant
  // the moment happens and is filled in when the agents' insight arrives.
  const keyOf = (m) => `${m.minute}-${m.second}-${m.kind}-${m.team}`;
  const ready = new Map(insights.map((i) => [keyOf(i.moment), i]));
  const cards = moments
    .map((m) => ({ key: keyOf(m), moment: m, insight: ready.get(keyOf(m)) }))
    .reverse();

  return (
    <div className="live-grid">
      <section className="card">
        <div className="card-title">
          <h2>{t("ai_insights")}</h2>
          <span className="muted">{t("foundry_agents")}</span>
        </div>
        {cards.length === 0 ? (
          <p className="empty">{status === "live" ? t("agents_watching") : t("press_kickoff")}</p>
        ) : (
          <ol className="insights scroll">
            {cards.map(({ key, moment, insight }) =>
              insight ? (
                <InsightCard key={key} item={insight} />
              ) : (
                <PendingCard key={key} moment={moment} info={info} />
              )
            )}
          </ol>
        )}
      </section>

      <section className="card">
        <div className="card-title">
          <h2>{t("commentary")}</h2>
        </div>
        {commentary.length === 0 ? (
          <p className="empty">{t("waiting_kickoff")}</p>
        ) : (
          <ol className="commentary scroll">
            {commentary.map((e) => (
              <li key={e.key} className={e.type === "goal" ? "is-goal" : KEY_TYPES.includes(e.type) ? "is-moment" : ""}>
                <span className="c-minute">{e.minute}&apos;</span>
                {e.team ? <Crest team={e.team} size={14} /> : <span className="c-dot" />}
                <span className="c-text">{e.text}</span>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
