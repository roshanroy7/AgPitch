"use client";

/*
  AgPitch main screen, FotMob-style:
    match header (teams, score, clock, scorers, Kick off, settings)
    tabs: Live | Stats | Recap
*/

import { useEffect, useState } from "react";
import LiveTab from "../components/LiveTab";
import MatchHeader from "../components/MatchHeader";
import RecapTab from "../components/RecapTab";
import SettingsModal from "../components/SettingsModal";
import StatsTab from "../components/StatsTab";
import { API_URL, useMatchStream } from "../lib/useMatchStream";
import { I18nProvider, translate } from "../lib/i18n";

// Changing any of these during a live match reopens the stream from the current minute
const LIVE_KEYS = ["mode", "club", "player", "language", "speed"];

const DEFAULT_SETTINGS = {
  mode: "casual",
  language: "en",
  club: "",
  player: "",
  speed: 30,
  from_minute: 0,
};

const TABS = ["Live", "Stats", "Recap"];

export default function Home() {
  const match = useMatchStream();
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [info, setInfo] = useState(null);
  const [apiError, setApiError] = useState(false);
  const [tab, setTab] = useState("Live");
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Load teams and players once, so settings can list them before kick-off
  useEffect(() => {
    fetch(`${API_URL}/match`)
      .then((r) => r.json())
      .then(setInfo)
      .catch(() => setApiError(true));
  }, []);

  // Jump to the Recap tab when it arrives
  useEffect(() => {
    if (match.recap) setTab("Recap");
  }, [match.recap]);

  function options(s, fromMinute) {
    return {
      mode: s.mode,
      language: s.language,
      club: s.club,
      player: s.player,
      speed: s.speed,
      from_minute: fromMinute,
    };
  }

  function kickOff() {
    setTab("Live");
    match.start(options(settings, settings.from_minute));
  }

  function changeSettings(next) {
    // Player focus needs a player: default to the away captain
    if (next.mode === "player_focus" && !next.player && info) {
      const captain = info.teams[info.away].players.find((p) => p.captain);
      next = { ...next, player: captain ? captain.name : "" };
    }
    const changed = LIVE_KEYS.some((k) => next[k] !== settings[k]);
    setSettings(next);
    if (changed && match.status === "live" && match.stats) {
      match.start(options(next, Math.min(match.stats.minute, 90)));
    }
  }

  const shownInfo = match.info || info;
  const goals = match.events.filter((e) => e.type === "goal");
  const t = (key, vars) => translate(settings.language, key, vars);
  const profileLabel = [t(`mode_${settings.mode}`), settings.language.toUpperCase(), settings.club || null]
    .filter(Boolean)
    .join(" · ");

  return (
    <I18nProvider value={settings.language}>
    <main className="page">
      <nav className="topnav">
        <span className="wordmark">AgPitch</span>
        <span className="muted small">{t("tagline")}</span>
      </nav>

      {apiError && <div className="alert">{t("api_error", { url: API_URL })}</div>}
      {match.status === "error" && (
        <div className="alert">{t("stream_error")}</div>
      )}

      <MatchHeader
        info={shownInfo}
        score={match.stats?.score}
        minute={match.stats?.minute ?? 0}
        status={match.status}
        goals={goals}
        onKickOff={kickOff}
        onSettings={() => setSettingsOpen(true)}
        profileLabel={profileLabel}
      />

      <div className="tabs" role="tablist">
        {TABS.map((name) => (
          <button
            key={name}
            type="button"
            role="tab"
            aria-selected={tab === name}
            className={tab === name ? "tab active" : "tab"}
            onClick={() => setTab(name)}
          >
            {t(`tab_${name}`)}
            {name === "Live" && match.insights.length > 0 && <span className="count">{match.insights.length}</span>}
          </button>
        ))}
      </div>

      {tab === "Live" && <LiveTab insights={match.insights} events={match.events} moments={match.moments} status={match.status} info={shownInfo} />}
      {tab === "Stats" && <StatsTab stats={match.stats} info={shownInfo} events={match.events} />}
      {tab === "Recap" && <RecapTab recap={match.recap} status={match.status} minute={match.stats?.minute ?? 0} />}

      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={settings}
        onChange={changeSettings}
        info={shownInfo}
      />

      <footer className="footer">
        {t("footer")}
      </footer>
    </main>
    </I18nProvider>
  );
}
