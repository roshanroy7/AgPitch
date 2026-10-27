"use client";

/*
  RecapTab: the Recap agent's full-time summary, written for this viewer.
*/

import { useI18n } from "../lib/i18n";

export default function RecapTab({ recap, status, minute }) {
  const { t } = useI18n();
  if (!recap) {
    const writing = status === "live" && minute >= 90;
    return (
      <section className="card">
        <p className="empty">
          {writing ? t("recap_writing") : t("recap_pending")}
        </p>
      </section>
    );
  }
  if (recap.fallback || !recap.recap) {
    return <section className="card"><p className="empty">{t("recap_unavailable")}</p></section>;
  }

  const r = recap.recap;
  const paragraphs = Array.isArray(r.summary) ? r.summary : String(r.summary || "").split(/\n+/);

  return (
    <section className="card recap">
      <span className="muted small">{t("recap_by")}</span>
      <h2>{r.title}</h2>
      {paragraphs.filter(Boolean).map((p, i) => (
        <p key={i}>{p}</p>
      ))}
      <div className="recap-grid">
        {r.turning_point && (
          <div className="recap-box">
            <span>{t("turning_point")}</span>
            <p>{r.turning_point}</p>
          </div>
        )}
        {r.player_of_the_match && (
          <div className="recap-box">
            <span>{t("potm")}</span>
            <p>
              <strong>{r.player_of_the_match.name}</strong>
              <br />
              {r.player_of_the_match.reason}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
