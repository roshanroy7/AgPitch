"use client";

/*
  i18n: every piece of interface text in English, Spanish and Portuguese.

  - STRINGS holds fixed labels ("Top stats", "Kick off"...).
  - commentaryLine() and momentHeadline() build match sentences in the
    chosen language from the event data, so no English slips through.
  - The AI cards are already written in the right language by the Fan agent.

  Components call  const { t, lang } = useI18n();  and then  t("kick_off").
*/

import { createContext, useContext } from "react";

const STRINGS = {
  en: {
    tagline: "Live match intelligence · synthetic data",
    tab_Live: "Live", tab_Stats: "Stats", tab_Recap: "Recap",
    api_error: "Can't reach the AgPitch API at {url}. Is the backend running?",
    stream_error: "The live stream stopped. Check the backend terminal, then press Restart.",
    footer: "Built for the Inside the Game hackathon. All teams, players and match data are synthetic.",
    mode_casual: "Casual", mode_analyst: "Analyst", mode_player_focus: "Player focus",
    not_started: "Not started", full_time: "Full time", stream_stopped: "Stream stopped",
    kick_off: "Kick off", restart: "Restart", watch_again: "Watch again", settings: "Viewer settings",
    your_match: "Your match", viewing_mode: "Viewing mode", casual_fan: "Casual fan",
    language: "Language", your_club: "Your club", no_preference: "No preference",
    favourite_player: "Favourite player", none: "None", replay_speed: "Replay speed",
    slow: "Slow", normal: "Normal", fast: "Fast", start_from: "Start from",
    kickoff_start: "Kick-off", second_half: "2nd half", done: "Done", close: "Close",
    ai_insights: "AI insights", foundry_agents: "Azure AI Foundry agents",
    agents_watching: "The agents are watching. A card appears the moment something important happens.",
    press_kickoff: "Press Kick off to start the match.",
    commentary: "Commentary", waiting_kickoff: "Waiting for kick-off.",
    analysing: "Analysing", pundit_thinking: "The Pundit agent is working out why this matters…",
    flagged_by: "Flagged by", made_by: "Made by", stats_engine: "Stats Engine",
    why_it_matters: "Why it matters", agents_unavailable: "Agents unavailable, stats only",
    prepared: "prepared · agents took {s}s", importance: "Importance {n} of 5",
    theme_control: "Control", theme_chaos: "Chaos", theme_pressure: "Pressure", theme_momentum: "Momentum",
    theme_rhythm: "Rhythm", theme_individual: "Individual", theme_result: "Result",
    stats_appear: "Stats appear once the match starts.",
    top_stats: "Top stats", ball_possession: "Ball possession", last_10: "Last 10 minutes",
    stat_pass_accuracy_pct: "Pass accuracy", stat_passes: "Passes", stat_avg_pass_difficulty: "Pass difficulty (0-10)",
    stat_passes_under_pressure_pct: "Passes under pressure", stat_shots: "Total shots",
    stat_shots_on_target: "Shots on target", stat_fastest_shot_kmh: "Fastest shot", stat_saves: "Keeper saves",
    stat_corners: "Corners", stat_counter_attacks: "Counter-attacks", stat_tackles: "Tackles",
    stat_interceptions: "Interceptions", stat_turnovers: "Turnovers", stat_fouls: "Fouls",
    stat_yellow_cards: "Yellow cards", stat_red_cards: "Red cards",
    shot_map: "Shot map", attack: "{team} attack", on_target: "On target", off_target_key: "Off target / blocked",
    bigger_faster: "Bigger = faster shot", result: "Result", shot_speed: "Shot speed",
    under_pressure: "Under pressure", yes: "Yes", no: "No", no_shots: "No shots yet.", shots: "shots",
    outcome_saved: "Saved", outcome_blocked: "Blocked", outcome_off_target: "Off target", outcome_goal: "Goal",
    recap_pending: "The recap appears here at full time.",
    recap_writing: "Full time. The Recap agent is writing your match summary…",
    recap_unavailable: "The Recap agent was unavailable.",
    recap_by: "Written for you by the Recap agent", turning_point: "Turning point", potm: "Player of the match",
  },
  es: {
    tagline: "Inteligencia del partido en vivo · datos sintéticos",
    tab_Live: "En vivo", tab_Stats: "Estadísticas", tab_Recap: "Resumen",
    api_error: "No se puede conectar con la API de AgPitch en {url}. ¿Está funcionando el backend?",
    stream_error: "La transmisión se detuvo. Revisa el terminal del backend y pulsa Reiniciar.",
    footer: "Creado para el hackathon Inside the Game. Todos los equipos, jugadores y datos son sintéticos.",
    mode_casual: "Aficionado", mode_analyst: "Analista", mode_player_focus: "Foco en jugador",
    not_started: "Sin comenzar", full_time: "Final", stream_stopped: "Transmisión detenida",
    kick_off: "Empezar", restart: "Reiniciar", watch_again: "Ver de nuevo", settings: "Ajustes",
    your_match: "Tu partido", viewing_mode: "Modo de visualización", casual_fan: "Aficionado",
    language: "Idioma", your_club: "Tu club", no_preference: "Sin preferencia",
    favourite_player: "Jugador favorito", none: "Ninguno", replay_speed: "Velocidad",
    slow: "Lenta", normal: "Normal", fast: "Rápida", start_from: "Empezar desde",
    kickoff_start: "Inicio", second_half: "2.º tiempo", done: "Listo", close: "Cerrar",
    ai_insights: "Análisis con IA", foundry_agents: "Agentes de Azure AI Foundry",
    agents_watching: "Los agentes están mirando. Aparece una tarjeta en cuanto pasa algo importante.",
    press_kickoff: "Pulsa Empezar para iniciar el partido.",
    commentary: "Relato", waiting_kickoff: "Esperando el saque inicial.",
    analysing: "Analizando", pundit_thinking: "El agente Pundit está analizando por qué importa…",
    flagged_by: "Detectado por", made_by: "Creado por", stats_engine: "Motor de estadísticas",
    why_it_matters: "Por qué importa", agents_unavailable: "Agentes no disponibles, solo estadísticas",
    prepared: "preparado · los agentes tardaron {s} s", importance: "Importancia {n} de 5",
    theme_control: "Control", theme_chaos: "Caos", theme_pressure: "Presión", theme_momentum: "Impulso",
    theme_rhythm: "Ritmo", theme_individual: "Individual", theme_result: "Resultado",
    stats_appear: "Las estadísticas aparecen cuando empieza el partido.",
    top_stats: "Estadísticas principales", ball_possession: "Posesión del balón", last_10: "Últimos 10 minutos",
    stat_pass_accuracy_pct: "Precisión de pase", stat_passes: "Pases", stat_avg_pass_difficulty: "Dificultad de pase (0-10)",
    stat_passes_under_pressure_pct: "Pases bajo presión", stat_shots: "Tiros totales",
    stat_shots_on_target: "Tiros a puerta", stat_fastest_shot_kmh: "Tiro más rápido", stat_saves: "Atajadas",
    stat_corners: "Córners", stat_counter_attacks: "Contraataques", stat_tackles: "Entradas",
    stat_interceptions: "Intercepciones", stat_turnovers: "Pérdidas", stat_fouls: "Faltas",
    stat_yellow_cards: "Tarjetas amarillas", stat_red_cards: "Tarjetas rojas",
    shot_map: "Mapa de tiros", attack: "Ataca {team}", on_target: "A puerta", off_target_key: "Fuera / bloqueado",
    bigger_faster: "Más grande = tiro más rápido", result: "Resultado", shot_speed: "Velocidad del tiro",
    under_pressure: "Bajo presión", yes: "Sí", no: "No", no_shots: "Todavía no hay tiros.", shots: "tiros",
    outcome_saved: "Atajado", outcome_blocked: "Bloqueado", outcome_off_target: "Desviado", outcome_goal: "Gol",
    recap_pending: "El resumen aparece aquí al final del partido.",
    recap_writing: "Final del partido. El agente Recap está escribiendo tu resumen…",
    recap_unavailable: "El agente Recap no estuvo disponible.",
    recap_by: "Escrito para ti por el agente Recap", turning_point: "Momento clave", potm: "Jugador del partido",
  },
  pt: {
    tagline: "Inteligência da partida ao vivo · dados sintéticos",
    tab_Live: "Ao vivo", tab_Stats: "Estatísticas", tab_Recap: "Resumo",
    api_error: "Não foi possível acessar a API do AgPitch em {url}. O backend está rodando?",
    stream_error: "A transmissão parou. Confira o terminal do backend e clique em Reiniciar.",
    footer: "Criado para o hackathon Inside the Game. Todos os times, jogadores e dados são sintéticos.",
    mode_casual: "Torcedor", mode_analyst: "Analista", mode_player_focus: "Foco no jogador",
    not_started: "Não iniciado", full_time: "Fim de jogo", stream_stopped: "Transmissão parada",
    kick_off: "Começar", restart: "Reiniciar", watch_again: "Ver de novo", settings: "Configurações",
    your_match: "Sua partida", viewing_mode: "Modo de visualização", casual_fan: "Torcedor",
    language: "Idioma", your_club: "Seu time", no_preference: "Sem preferência",
    favourite_player: "Jogador favorito", none: "Nenhum", replay_speed: "Velocidade",
    slow: "Lenta", normal: "Normal", fast: "Rápida", start_from: "Começar a partir de",
    kickoff_start: "Início", second_half: "2º tempo", done: "Pronto", close: "Fechar",
    ai_insights: "Análises com IA", foundry_agents: "Agentes do Azure AI Foundry",
    agents_watching: "Os agentes estão de olho. Um card aparece assim que algo importante acontece.",
    press_kickoff: "Clique em Começar para iniciar a partida.",
    commentary: "Narração", waiting_kickoff: "Aguardando o pontapé inicial.",
    analysing: "Analisando", pundit_thinking: "O agente Pundit está analisando por que isso importa…",
    flagged_by: "Detectado por", made_by: "Feito por", stats_engine: "Motor de estatísticas",
    why_it_matters: "Por que importa", agents_unavailable: "Agentes indisponíveis, só estatísticas",
    prepared: "preparado · os agentes levaram {s} s", importance: "Importância {n} de 5",
    theme_control: "Controle", theme_chaos: "Caos", theme_pressure: "Pressão", theme_momentum: "Embalo",
    theme_rhythm: "Ritmo", theme_individual: "Individual", theme_result: "Resultado",
    stats_appear: "As estatísticas aparecem quando a partida começa.",
    top_stats: "Principais estatísticas", ball_possession: "Posse de bola", last_10: "Últimos 10 minutos",
    stat_pass_accuracy_pct: "Precisão nos passes", stat_passes: "Passes", stat_avg_pass_difficulty: "Dificuldade do passe (0-10)",
    stat_passes_under_pressure_pct: "Passes sob pressão", stat_shots: "Finalizações",
    stat_shots_on_target: "Chutes no gol", stat_fastest_shot_kmh: "Chute mais forte", stat_saves: "Defesas do goleiro",
    stat_corners: "Escanteios", stat_counter_attacks: "Contra-ataques", stat_tackles: "Desarmes",
    stat_interceptions: "Interceptações", stat_turnovers: "Perdas de posse", stat_fouls: "Faltas",
    stat_yellow_cards: "Cartões amarelos", stat_red_cards: "Cartões vermelhos",
    shot_map: "Mapa de finalizações", attack: "{team} ataca", on_target: "No gol", off_target_key: "Para fora / bloqueado",
    bigger_faster: "Maior = chute mais forte", result: "Resultado", shot_speed: "Velocidade do chute",
    under_pressure: "Sob pressão", yes: "Sim", no: "Não", no_shots: "Ainda não há finalizações.", shots: "finalizações",
    outcome_saved: "Defendido", outcome_blocked: "Bloqueado", outcome_off_target: "Para fora", outcome_goal: "Gol",
    recap_pending: "O resumo aparece aqui no fim do jogo.",
    recap_writing: "Fim de jogo. O agente Recap está escrevendo o seu resumo…",
    recap_unavailable: "O agente Recap não estava disponível.",
    recap_by: "Escrito para você pelo agente Recap", turning_point: "Momento decisivo", potm: "Craque do jogo",
  },
};

// Match sentences, built from the event data in each language
const LINES = {
  en: {
    assist: (e) => `${e.player} sets up ${e.receiver}`,
    shot_saved: (e, what, ctr) => `${e.player}'s ${what}${ctr} (${e.shot_speed_kmh} km/h) is saved`,
    shot_blocked: (e, what, ctr) => `${e.player}'s ${what}${ctr} is blocked`,
    shot_wide: (e, what, ctr) => `${e.player}'s ${what}${ctr} goes wide`,
    shot: "shot", header: "header", on_break: " on the break",
    save: (e) => `Save! ${e.player} keeps out ${e.shooter}'s ${e.shot_speed_kmh} km/h effort`,
    corner: (e) => `Corner to ${e.team}. ${e.player} takes it from the ${e.side}`,
    left: "left", right: "right",
    clearance: (e) => `${e.player} clears the corner`,
    counter: (e) => `${e.team} break on the counter! ${e.player} drives forward`,
    goal: (e) => `Goal! ${e.player} scores${e.assist ? `, assisted by ${e.assist}` : ""}`,
    foul: (e) => `Foul by ${e.player} on ${e.fouled}`,
    hard_foul: (e) => `Crunching challenge by ${e.player} on ${e.fouled}`,
    yellow: (e) => `Yellow card: ${e.player} is booked for a hard foul on ${e.fouled}`,
    red: (e) => `Red card! ${e.player} is sent off (second yellow)`,
    injury: (e) => `${e.player} is down injured and needs treatment`,
    sprint: (e) => `${e.player} hits ${e.top_speed_kmh} km/h on the run`,
    kickoff: (e) => `${e.team} kick off`,
    half_time: "Half time", full_time: "Full time",
  },
  es: {
    assist: (e) => `${e.player} habilita a ${e.receiver}`,
    shot_saved: (e, what, ctr) => `${what} de ${e.player}${ctr} (${e.shot_speed_kmh} km/h): atajado`,
    shot_blocked: (e, what, ctr) => `${what} de ${e.player}${ctr}: bloqueado`,
    shot_wide: (e, what, ctr) => `${what} de ${e.player}${ctr}: se va desviado`,
    shot: "Tiro", header: "Cabezazo", on_break: " al contragolpe",
    save: (e) => `¡Atajada! ${e.player} le saca el remate de ${e.shot_speed_kmh} km/h a ${e.shooter}`,
    corner: (e) => `Córner para ${e.team}. Lo saca ${e.player} desde la ${e.side}`,
    left: "izquierda", right: "derecha",
    clearance: (e) => `${e.player} despeja el córner`,
    counter: (e) => `¡Contragolpe de ${e.team}! ${e.player} arranca hacia adelante`,
    goal: (e) => `¡Gol! Marca ${e.player}${e.assist ? `, asistencia de ${e.assist}` : ""}`,
    foul: (e) => `Falta de ${e.player} sobre ${e.fouled}`,
    hard_foul: (e) => `Entrada durísima de ${e.player} sobre ${e.fouled}`,
    yellow: (e) => `Tarjeta amarilla para ${e.player} por una falta dura sobre ${e.fouled}`,
    red: (e) => `¡Tarjeta roja! ${e.player} se va expulsado (segunda amarilla)`,
    injury: (e) => `${e.player} está tendido en el campo y necesita atención`,
    sprint: (e) => `${e.player} alcanza ${e.top_speed_kmh} km/h en carrera`,
    kickoff: (e) => `Saca ${e.team}`,
    half_time: "Descanso", full_time: "Final del partido",
  },
  pt: {
    assist: (e) => `${e.player} deixa ${e.receiver} na cara do gol`,
    shot_saved: (e, what, ctr) => `${what} de ${e.player}${ctr} (${e.shot_speed_kmh} km/h): defendido`,
    shot_blocked: (e, what, ctr) => `${what} de ${e.player}${ctr}: bloqueado`,
    shot_wide: (e, what, ctr) => `${what} de ${e.player}${ctr}: para fora`,
    shot: "Chute", header: "Cabeçada", on_break: " no contra-ataque",
    save: (e) => `Defesaça! ${e.player} pega o chute de ${e.shot_speed_kmh} km/h de ${e.shooter}`,
    corner: (e) => `Escanteio para o ${e.team}. ${e.player} cobra pela ${e.side}`,
    left: "esquerda", right: "direita",
    clearance: (e) => `${e.player} afasta o escanteio`,
    counter: (e) => `Contra-ataque do ${e.team}! ${e.player} arranca em velocidade`,
    goal: (e) => `Gol! ${e.player} marca${e.assist ? `, assistência de ${e.assist}` : ""}`,
    foul: (e) => `Falta de ${e.player} em ${e.fouled}`,
    hard_foul: (e) => `Entrada dura de ${e.player} em ${e.fouled}`,
    yellow: (e) => `Cartão amarelo para ${e.player} por falta dura em ${e.fouled}`,
    red: (e) => `Cartão vermelho! ${e.player} é expulso (segundo amarelo)`,
    injury: (e) => `${e.player} caiu machucado e precisa de atendimento`,
    sprint: (e) => `${e.player} chega a ${e.top_speed_kmh} km/h na arrancada`,
    kickoff: (e) => `${e.team} dá a saída`,
    half_time: "Intervalo", full_time: "Fim de jogo",
  },
};

// Headlines for the key moments flagged by the Stats Engine
const MOMENTS = {
  en: {
    goal: (m) => `GOAL! ${m.player} scores for ${m.team}`,
    speed_alert: (m) => `${m.player} hits ${m.data.top_speed_kmh} km/h`,
    rocket_shot: (m) => `${m.player} strikes at ${m.data.shot_speed_kmh} km/h`,
    big_save: (m) => `Big save! ${m.player} denies ${m.data.shooter}`,
    counter_attack: (m) => `${m.team} break on the counter`,
    yellow_card: (m) => `Yellow card for ${m.player}`,
    red_card: (m) => `Red card for ${m.player}`,
    milestone: (m) => `${m.player} completes pass number ${m.data.passes_completed}`,
    quality_pass: (m) => `Difficult pass completed by ${m.player}`,
    turnover_streak: (m) => `${m.team} have lost the ball ${m.data.turnovers_last_5_min} times in 5 minutes`,
    pressure_spike: (m) => `${m.team} are under heavy pressure`,
    momentum_swing: (m) => `Momentum swing towards ${m.team}`,
    half_time: (m, s) => `Half time: ${s}`,
    full_time: (m, s) => `Full time: ${s}`,
  },
  es: {
    goal: (m) => `¡GOL! Marca ${m.player} para ${m.team}`,
    speed_alert: (m) => `${m.player} alcanza ${m.data.top_speed_kmh} km/h`,
    rocket_shot: (m) => `Remate de ${m.player} a ${m.data.shot_speed_kmh} km/h`,
    big_save: (m) => `¡Atajadón! ${m.player} le niega el gol a ${m.data.shooter}`,
    counter_attack: (m) => `Contragolpe de ${m.team}`,
    yellow_card: (m) => `Tarjeta amarilla para ${m.player}`,
    red_card: (m) => `Tarjeta roja para ${m.player}`,
    milestone: (m) => `${m.player} completa su pase número ${m.data.passes_completed}`,
    quality_pass: (m) => `Pase de gran dificultad de ${m.player}`,
    turnover_streak: (m) => `${m.team} perdió el balón ${m.data.turnovers_last_5_min} veces en 5 minutos`,
    pressure_spike: (m) => `${m.team} sufre una presión intensa`,
    momentum_swing: (m) => `El impulso cambia a favor de ${m.team}`,
    half_time: (m, s) => `Descanso: ${s}`,
    full_time: (m, s) => `Final: ${s}`,
  },
  pt: {
    goal: (m) => `GOL! ${m.player} marca para o ${m.team}`,
    speed_alert: (m) => `${m.player} chega a ${m.data.top_speed_kmh} km/h`,
    rocket_shot: (m) => `Chute de ${m.player} a ${m.data.shot_speed_kmh} km/h`,
    big_save: (m) => `Defesaça! ${m.player} para ${m.data.shooter}`,
    counter_attack: (m) => `Contra-ataque do ${m.team}`,
    yellow_card: (m) => `Cartão amarelo para ${m.player}`,
    red_card: (m) => `Cartão vermelho para ${m.player}`,
    milestone: (m) => `${m.player} completa o passe número ${m.data.passes_completed}`,
    quality_pass: (m) => `Passe difícil completado por ${m.player}`,
    turnover_streak: (m) => `${m.team} perdeu a bola ${m.data.turnovers_last_5_min} vezes em 5 minutos`,
    pressure_spike: (m) => `${m.team} está sob forte pressão`,
    momentum_swing: (m) => `O embalo muda para o ${m.team}`,
    half_time: (m, s) => `Intervalo: ${s}`,
    full_time: (m, s) => `Fim de jogo: ${s}`,
  },
};

export function translate(lang, key, vars = {}) {
  const text = STRINGS[lang]?.[key] ?? STRINGS.en[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, name) => (vars[name] ?? `{${name}}`));
}

export function commentaryLine(lang, e) {
  const L = LINES[lang] || LINES.en;
  switch (e.type) {
    case "pass":
      return e.outcome === "success" && e.assist ? L.assist(e) : null;
    case "shot": {
      if (e.outcome === "goal") return null;
      const what = e.header ? L.header : L.shot;
      const ctr = e.from_counter ? L.on_break : "";
      if (e.outcome === "saved") return L.shot_saved(e, what, ctr);
      if (e.outcome === "blocked") return L.shot_blocked(e, what, ctr);
      return L.shot_wide(e, what, ctr);
    }
    case "save": return L.save(e);
    case "corner": return L.corner({ ...e, side: L[e.side] || e.side });
    case "clearance": return L.clearance(e);
    case "counter_attack": return L.counter(e);
    case "goal": return L.goal(e);
    case "foul": return e.hard ? L.hard_foul(e) : L.foul(e);
    case "yellow_card": return L.yellow(e);
    case "red_card": return L.red(e);
    case "injury": return L.injury(e);
    case "sprint": return e.top_speed_kmh >= 33 ? L.sprint(e) : null; // only the fastest
    case "kickoff": return L.kickoff(e);
    case "half_time": return L.half_time;
    case "full_time": return L.full_time;
    default: return null;
  }
}

export function momentHeadline(lang, m, info) {
  const M = MOMENTS[lang] || MOMENTS.en;
  const build = M[m.kind];
  if (!build) return m.headline;
  let score = "";
  if (info && m.data?.score) {
    score = `${info.home} ${m.data.score[info.home]} - ${m.data.score[info.away]} ${info.away}`;
  }
  try {
    return build(m, score);
  } catch {
    return m.headline;
  }
}

export const DATE_LOCALE = { en: "en-GB", es: "es-ES", pt: "pt-BR" };

const I18nContext = createContext("en");
export const I18nProvider = I18nContext.Provider;

export function useI18n() {
  const lang = useContext(I18nContext);
  return { lang, t: (key, vars) => translate(lang, key, vars) };
}
