"use client";

/*
  SettingsModal: the viewer profile and replay options, in a pop-up.
  Changing the profile during a live match continues from the current minute.
*/

import { useI18n } from "../lib/i18n";

const MODES = [
  { value: "casual", key: "casual_fan" },
  { value: "analyst", key: "mode_analyst" },
  { value: "player_focus", key: "mode_player_focus" },
];
const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Español" },
  { value: "pt", label: "Português" },
];
const SPEEDS = [
  { value: 10, key: "slow" },
  { value: 30, key: "normal" },
  { value: 60, key: "fast" },
];
const START_AT = [
  { value: 0, key: "kickoff_start" },
  { value: 45, key: "second_half" },
  { value: 60, label: "60'" },
  { value: 85, label: "85'" },
];

function Pills({ options, value, onChange, label }) {
  const { t } = useI18n();
  return (
    <div className="pills" role="group" aria-label={label}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          className={o.value === value ? "pill active" : "pill"}
          onClick={() => onChange(o.value)}
        >
          {o.label || t(o.key)}
        </button>
      ))}
    </div>
  );
}

export default function SettingsModal({ open, onClose, settings, onChange, info }) {
  const { t } = useI18n();
  if (!open) return null;
  const set = (key) => (value) => onChange({ ...settings, [key]: value });
  const teams = info ? [info.home, info.away] : [];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal card" role="dialog" aria-label={t("settings")} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h2>{t("your_match")}</h2>
          <button type="button" className="close" onClick={onClose} aria-label={t("close")}>×</button>
        </div>

        <div className="field">
          <label>{t("viewing_mode")}</label>
          <Pills label={t("viewing_mode")} options={MODES} value={settings.mode} onChange={set("mode")} />
        </div>

        <div className="field">
          <label>{t("language")}</label>
          <Pills label={t("language")} options={LANGUAGES} value={settings.language} onChange={set("language")} />
        </div>

        <div className="field-row">
          <div className="field">
            <label htmlFor="club">{t("your_club")}</label>
            <select id="club" value={settings.club} onChange={(e) => set("club")(e.target.value)}>
              <option value="">{t("no_preference")}</option>
              {teams.map((team) => (
                <option key={team} value={team}>{team}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="player">{t("favourite_player")}</label>
            <select id="player" value={settings.player} onChange={(e) => set("player")(e.target.value)}>
              <option value="">{t("none")}</option>
              {teams.map((team) => (
                <optgroup key={team} label={team}>
                  {info.teams[team].players.map((p) => (
                    <option key={p.name} value={p.name}>
                      {p.number}. {p.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
        </div>

        <div className="field">
          <label>{t("replay_speed")}</label>
          <Pills label={t("replay_speed")} options={SPEEDS} value={settings.speed} onChange={set("speed")} />
        </div>

        <div className="field">
          <label>{t("start_from")}</label>
          <Pills label={t("start_from")} options={START_AT} value={settings.from_minute} onChange={set("from_minute")} />
        </div>

        <button type="button" className="btn primary wide" onClick={onClose}>{t("done")}</button>
      </div>
    </div>
  );
}
