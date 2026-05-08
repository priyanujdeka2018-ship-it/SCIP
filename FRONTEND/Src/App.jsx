/**
 * SOBHA COLLECTIONS INTELLIGENCE PLATFORM
 * App.jsx - Simplified Intelligence Shell
 *
 * Direction: SCIP opens as a two-door intelligence lobby:
 *   1. Live Pulse     - operational now-view
 *   2. Narratives     - executive story-view
 *
 * The app keeps the backend/context contract from the Phase 5 shell while
 * reducing first-load cognitive load. Header/sidebar/mode controls are no
 * longer first-level choices; they reveal contextually after the user chooses
 * a path.
 */

import { useState, useEffect, useCallback, createContext, useContext, useMemo } from "react";

const BACKEND_URL = "https://scip.onrender.com";
const HEALTH_PING_INTERVAL_MS = 10 * 60 * 1000;

export const AppContext = createContext(null);
export const useAppContext = () => useContext(AppContext);

const PATHS = {
  landing: "/home",
  pulse: "/pulse",
  narratives: "/narratives",
};

const PULSE_NAV = [
  { id: "P1", focus: "current", label: "Now", eyebrow: "Signal" },
  { id: "P1", focus: "month", label: "Month", eyebrow: "MTD" },
  { id: "P1", focus: "ytd", label: "YTD", eyebrow: "Track" },
  { id: "P2", focus: "risk", label: "Risk", eyebrow: "Action" },
];

const STORY_NAV = [
  { id: "S01", label: "Story", eyebrow: "01" },
  { id: "S02", label: "Portfolio", eyebrow: "02" },
  { id: "S04", label: "Dues", eyebrow: "04" },
  { id: "S05", label: "Advance", eyebrow: "05" },
  { id: "S08", label: "Roadmap", eyebrow: "08" },
];

const FULL_NAV = [
  { id: "S01", label: "Strategic Narrative", group: "Narratives" },
  { id: "S02", label: "Portfolio Overview", group: "Narratives" },
  { id: "S04", label: "Dues Collections", group: "Narratives" },
  { id: "S05", label: "Advance Collections", group: "Narratives" },
  { id: "S06", label: "Operations & QCG", group: "Operational" },
  { id: "S07", label: "Team Structure", group: "Operational" },
  { id: "S08", label: "Strategic Roadmap", group: "Narratives" },
  { id: "P1", label: "Current Snapshot", group: "Live Pulse" },
  { id: "P2", label: "Deep Insights", group: "Live Pulse" },
  { id: "P3", label: "Calculator Tools", group: "Live Pulse" },
  { id: "P4", label: "Definitions", group: "Live Pulse" },
];

const SECTION_META = {
  S01: {
    label: "Strategic Narrative",
    short: "Story",
    kicker: "Executive signal",
    summary: "Board-ready interpretation across collections, portfolio movement, dues, advance, and strategic roadmap.",
  },
  S02: {
    label: "Portfolio Overview",
    short: "Portfolio",
    kicker: "Portfolio lens",
    summary: "The current portfolio picture, movement by entity, and what it implies for collections focus.",
  },
  S04: {
    label: "Dues Collections",
    short: "Dues",
    kicker: "Dues position",
    summary: "The dues story, overdue movement, entity exposure, and where executive attention is needed.",
  },
  S05: {
    label: "Advance Collections",
    short: "Advance",
    kicker: "Advance mix",
    summary: "The advance collections story, YTD mix, and how it supports liquidity and forward visibility.",
  },
  S06: {
    label: "Operations & QCG",
    short: "Actions",
    kicker: "Operational action",
    summary: "Priority actions, quality-control movement, and what the teams should focus on next.",
  },
  S07: {
    label: "Team Structure",
    short: "Collectors",
    kicker: "Collector lens",
    summary: "Collector and team view for execution ownership, escalation, and operational follow-through.",
  },
  S08: {
    label: "Strategic Roadmap",
    short: "Roadmap",
    kicker: "Forward path",
    summary: "The strategic roadmap connecting collections discipline, operating cadence, and next executive decisions.",
  },
  P1: {
    label: "Current Snapshot",
    short: "Snapshot",
    kicker: "Live Pulse",
    summary: "Current position, operational movement, and the numbers that need attention now.",
  },
  P2: {
    label: "Deep Insights",
    short: "Risks",
    kicker: "Risk signal",
    summary: "Where risk is forming, what changed, and which entity or movement needs closer inspection.",
  },
  P3: {
    label: "Calculator Tools",
    short: "Calculators",
    kicker: "Scenario tools",
    summary: "Operational calculators and scenario surfaces for action planning.",
  },
  P4: {
    label: "Definitions",
    short: "Definitions",
    kicker: "Shared language",
    summary: "Common terms, metric definitions, and interpretation notes for consistent discussion.",
  },
};

const BOARD_SECTIONS = STORY_NAV.map((item) => item.id);
const PULSE_SECTIONS = ["P1", "P2", "S06", "S07", "P3", "P4"];
const PULSE_FOCUS_TO_SECTION = { home: "P1", current: "P1", month: "P1", ytd: "P1", risk: "P2" };
const SECTION_TO_PULSE_FOCUS = { P1: "current", P2: "risk", S06: "risk", S07: "risk", P3: "current", P4: "current" };

function normalizePulseFocus(rawFocus) {
  return ["home", "current", "month", "ytd", "risk"].includes(rawFocus) ? rawFocus : "home";
}

function getUrlParam(key, fallback = null) {
  try {
    return new URLSearchParams(window.location.search).get(key) || fallback;
  } catch {
    return fallback;
  }
}

function normalizeMode(rawMode, view) {
  if (rawMode === "present") return "present";
  if (rawMode === "board") return "board";
  if (rawMode === "ops") return "ops";
  return view === "narratives" ? "board" : "ops";
}

function normalizeView(rawView) {
  if (rawView === "pulse" || rawView === "narratives" || rawView === "landing") return rawView;
  return "landing";
}

function getPathView() {
  try {
    const path = window.location.pathname.replace(/\/+$/, "") || "/";
    if (path.endsWith("/pulse")) return "pulse";
    if (path.endsWith("/narratives")) return "narratives";
    if (path.endsWith("/home")) return "landing";
    return null;
  } catch {
    return null;
  }
}

function getStoredView() {
  try {
    const stored = window.localStorage.getItem("scip.lastView");
    return stored === "pulse" || stored === "narratives" ? stored : null;
  } catch {
    return null;
  }
}

function setStoredView(view) {
  try {
    if (view === "pulse" || view === "narratives") {
      window.localStorage.setItem("scip.lastView", view);
      window.localStorage.setItem("scip.hasVisited", "true");
    }
  } catch {
    // Local storage is convenience only.
  }
}

function getInitialAppState() {
  const pathView = getPathView();
  const viewParam = getUrlParam("view", null);
  const rawMode = getUrlParam("mode", null);
  const sectionParam = getUrlParam("section", null);
  const rawPulseFocus = getUrlParam("focus", "home");

  let view = normalizeView(viewParam || pathView || null);

  if (!viewParam && !pathView) {
    if (rawMode === "board" || rawMode === "present") view = "narratives";
    else if (rawMode === "ops" && sectionParam && PULSE_SECTIONS.includes(sectionParam)) view = "pulse";
    else view = getStoredView() || "landing";
  }

  const mode = view === "landing" ? "ops" : normalizeMode(rawMode, view);
  const section = getInitialSection(view, mode, sectionParam);

  return { view, mode, section, pulseFocus: normalizePulseFocus(rawPulseFocus) };
}

function getInitialSection(view, mode, candidate) {
  if (mode === "present") {
    return BOARD_SECTIONS.includes(candidate) ? candidate : "S01";
  }
  if (view === "pulse") {
    return PULSE_SECTIONS.includes(candidate) ? candidate : "P1";
  }
  if (view === "narratives") {
    if (mode === "ops") {
      return FULL_NAV.some((item) => item.id === candidate) ? candidate : "S01";
    }
    return BOARD_SECTIONS.includes(candidate) ? candidate : "S01";
  }
  return candidate || "P1";
}

function replaceUrlState({ view, mode, section, entity, targetVersion, pulseFocus }) {
  try {
    const params = new URLSearchParams(window.location.search);
    params.set("view", view);
    if (mode) params.set("mode", mode);
    else params.delete("mode");
    if (section) params.set("section", section);
    else params.delete("section");
    if (entity) params.set("entity", entity);
    if (targetVersion) params.set("target", targetVersion);
    if (pulseFocus) params.set("focus", pulseFocus);

    const path = PATHS[view] || PATHS.landing;
    const query = params.toString();
    window.history.replaceState({}, "", `${path}${query ? `?${query}` : ""}`);
  } catch {
    // URL sync is cosmetic. State remains source of truth.
  }
}

function formatAedMillions(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `AED ${Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 })}M`;
}

function formatAedBillionsFromMillions(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `AED ${(Number(value) / 1000).toLocaleString(undefined, { maximumFractionDigits: 2 })}B`;
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${Number(value).toFixed(1)}%`;
}

function safeSnapshotDate(computed) {
  return computed?.snapshot_date || "Mar 2026";
}

function GlobalStyles() {
  return (
    <style>{`
      :root {
        --scip-bg: #080d14;
        --scip-slate-900: #080d14;
        --scip-slate-850: #0b121d;
        --scip-slate-800: #0f1623;
        --scip-slate-700: #172232;
        --scip-slate-600: #223047;
        --scip-glass-1: rgba(255, 255, 255, 0.055);
        --scip-glass-2: rgba(255, 255, 255, 0.085);
        --scip-glass-3: rgba(255, 255, 255, 0.12);
        --scip-border: rgba(255, 255, 255, 0.13);
        --scip-border-soft: rgba(255, 255, 255, 0.08);
        --scip-gold: #c9a84c;
        --scip-gold-light: #e2c76c;
        --scip-gold-deep: #8f7434;
        --scip-text: #f4efe5;
        --scip-text-2: #c8c0b3;
        --scip-text-3: #8f98a6;
        --scip-good: #22c55e;
        --scip-attention: #f59e0b;
        --scip-risk: #ef4444;
        --scip-shadow: 0 24px 80px rgba(0, 0, 0, 0.38);
        --scip-ease: cubic-bezier(0.22, 1, 0.36, 1);
      }

      * { box-sizing: border-box; }
      html, body, #root { width: 100%; height: 100%; margin: 0; }
      body { background: var(--scip-bg); }
      button, textarea, input { font: inherit; }
      button { -webkit-tap-highlight-color: transparent; }

      .scip-app {
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        position: relative;
        color: var(--scip-text);
        background:
          radial-gradient(circle at 15% 5%, rgba(201,168,76,0.16), transparent 28%),
          radial-gradient(circle at 82% 14%, rgba(226,199,108,0.10), transparent 24%),
          radial-gradient(circle at 50% 100%, rgba(74,101,139,0.18), transparent 36%),
          linear-gradient(145deg, #080d14 0%, #0f1623 45%, #080d14 100%);
        font-family: Inter, "DM Sans", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        letter-spacing: 0.01em;
      }

      .scip-app::before,
      .scip-app::after {
        content: "";
        position: absolute;
        inset: auto;
        pointer-events: none;
        filter: blur(4px);
        opacity: 0.45;
        transform: translate3d(0,0,0);
      }

      .scip-app::before {
        width: 640px;
        height: 640px;
        left: -180px;
        top: -240px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(201,168,76,0.18), transparent 62%);
        animation: scip-drift-a 18s var(--scip-ease) infinite alternate;
      }

      .scip-app::after {
        width: 760px;
        height: 760px;
        right: -260px;
        bottom: -300px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(115,143,184,0.16), transparent 60%);
        animation: scip-drift-b 22s var(--scip-ease) infinite alternate;
      }

      .skip-link {
        position: absolute;
        left: 16px;
        top: -80px;
        z-index: 999;
        padding: 8px 12px;
        border-radius: 999px;
        background: var(--scip-gold);
        color: var(--scip-slate-900);
        font-weight: 800;
        text-decoration: none;
      }

      .skip-link:focus { top: 16px; }

      .glass-card,
      .glass-island,
      .glass-rail,
      .glass-pill {
        background: linear-gradient(135deg, rgba(255,255,255,0.10), rgba(255,255,255,0.035));
        backdrop-filter: blur(28px) saturate(135%);
        -webkit-backdrop-filter: blur(28px) saturate(135%);
        border: 1px solid var(--scip-border);
        box-shadow: var(--scip-shadow), inset 0 1px 0 rgba(255,255,255,0.16);
      }

      .glass-card,
      .glass-island,
      .glass-rail { position: relative; overflow: hidden; }

      .glass-card::before,
      .glass-island::before,
      .glass-rail::before {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        background: radial-gradient(circle at 20% 0%, rgba(201,168,76,0.20), transparent 34%);
        opacity: 0.85;
      }

      .glass-card > *,
      .glass-island > *,
      .glass-rail > * { position: relative; z-index: 1; }

      .solid-card {
        background: linear-gradient(180deg, rgba(15,22,35,0.96), rgba(11,18,29,0.96));
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 18px 56px rgba(0,0,0,0.30);
      }

      .landing-shell {
        min-height: 100%;
        padding: 28px clamp(22px, 4vw, 60px) 108px;
        display: flex;
        flex-direction: column;
        position: relative;
        z-index: 1;
      }

      .landing-topbar {
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: var(--scip-text-2);
      }

      .brand-lockup { display: flex; align-items: baseline; gap: 10px; }
      .brand-mark {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 24px;
        letter-spacing: 0.12em;
        color: var(--scip-gold-light);
      }
      .brand-subtitle {
        font-size: 11px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--scip-text-3);
        font-weight: 800;
      }
      .data-date {
        font-size: 11px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--scip-text-2);
      }

      .landing-center {
        flex: 1;
        display: grid;
        place-items: center;
        padding: 42px 0 24px;
      }

      .landing-copy {
        text-align: center;
        max-width: 900px;
        margin: 0 auto 34px;
      }

      .landing-kicker,
      .section-kicker,
      .card-kicker {
        margin: 0 0 12px;
        color: var(--scip-gold-light);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.18em;
        text-transform: uppercase;
      }

      .landing-title {
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(42px, 6vw, 82px);
        line-height: 0.96;
        letter-spacing: -0.055em;
        color: var(--scip-text);
        text-wrap: balance;
      }

      .landing-subtitle {
        margin: 22px auto 0;
        max-width: 640px;
        color: var(--scip-text-2);
        font-size: clamp(16px, 1.5vw, 20px);
        line-height: 1.65;
      }

      .entry-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(260px, 1fr));
        gap: 20px;
        width: min(860px, 100%);
        margin: 0 auto;
      }

      .entry-card {
        min-height: 245px;
        border-radius: 34px;
        padding: 28px;
        text-align: left;
        cursor: pointer;
        color: var(--scip-text);
        transition: transform 280ms var(--scip-ease), border-color 280ms var(--scip-ease), background 280ms var(--scip-ease);
      }

      .entry-card:hover,
      .entry-card:focus-visible {
        transform: translateY(-6px);
        border-color: rgba(226,199,108,0.42);
        outline: none;
      }

      .entry-card h2 {
        margin: 20px 0 12px;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 34px;
        letter-spacing: -0.035em;
      }

      .entry-card p {
        margin: 0;
        color: var(--scip-text-2);
        line-height: 1.6;
        font-size: 15px;
      }

      .entry-icon {
        width: 46px;
        height: 46px;
        display: grid;
        place-items: center;
        border-radius: 18px;
        background: rgba(201,168,76,0.12);
        border: 1px solid rgba(201,168,76,0.25);
        color: var(--scip-gold-light);
        font-weight: 900;
        letter-spacing: 0.08em;
      }

      .entry-cta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 28px;
        color: var(--scip-gold-light);
        font-weight: 800;
        letter-spacing: 0.04em;
      }

      .app-shell {
        height: 100%;
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        padding: 22px;
        gap: 18px;
      }

      .context-island {
        min-height: 64px;
        border-radius: 28px;
        padding: 10px 12px;
        display: grid;
        grid-template-columns: minmax(210px, auto) 1fr auto;
        align-items: center;
        gap: 14px;
      }

      .logo-button {
        border: 0;
        background: transparent;
        color: var(--scip-text);
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 12px;
        border-radius: 20px;
        transition: background 220ms var(--scip-ease);
      }

      .logo-button:hover,
      .logo-button:focus-visible { background: rgba(255,255,255,0.06); outline: none; }

      .logo-stack { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
      .logo-main {
        font-family: Georgia, "Times New Roman", serif;
        color: var(--scip-gold-light);
        font-size: 20px;
        letter-spacing: 0.12em;
      }
      .logo-caption {
        color: var(--scip-text-3);
        font-size: 9px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 800;
      }

      .context-middle,
      .context-right,
      .filter-group,
      .depth-control {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
      }

      .context-middle { justify-content: center; }
      .context-right { justify-content: flex-end; }
      .filter-label {
        color: var(--scip-text-3);
        font-size: 10px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 900;
        margin-right: 2px;
      }

      .pill-button,
      .depth-button,
      .rail-button,
      .story-button,
      .sidebar-button,
      .prompt-button {
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.045);
        color: var(--scip-text-2);
        cursor: pointer;
        transition: background 220ms var(--scip-ease), color 220ms var(--scip-ease), border-color 220ms var(--scip-ease), transform 220ms var(--scip-ease);
      }

      .pill-button,
      .depth-button {
        min-height: 34px;
        padding: 8px 13px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
      }

      .pill-button:hover,
      .depth-button:hover,
      .rail-button:hover,
      .story-button:hover,
      .sidebar-button:hover,
      .prompt-button:hover {
        color: var(--scip-text);
        background: rgba(255,255,255,0.08);
        border-color: rgba(226,199,108,0.28);
      }

      .pill-button.is-active,
      .depth-button.is-active,
      .rail-button.is-active,
      .story-button.is-active,
      .sidebar-button.is-active {
        color: #10131a;
        background: linear-gradient(135deg, var(--scip-gold-light), var(--scip-gold));
        border-color: rgba(226,199,108,0.72);
        box-shadow: 0 12px 28px rgba(201,168,76,0.18);
      }

      .shell-body {
        flex: 1;
        min-height: 0;
        display: flex;
        gap: 18px;
      }

      .compact-rail {
        width: 142px;
        border-radius: 28px;
        padding: 12px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        align-self: flex-start;
      }

      .rail-button {
        width: 100%;
        border-radius: 20px;
        padding: 12px 10px;
        display: flex;
        flex-direction: column;
        gap: 4px;
        text-align: left;
      }

      .rail-eyebrow,
      .story-eyebrow,
      .sidebar-section-id {
        font-size: 9px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 900;
        opacity: 0.72;
      }

      .rail-label,
      .story-label { font-size: 13px; font-weight: 850; }

      .full-sidebar {
        width: 246px;
        border-radius: 30px;
        padding: 14px;
        overflow: auto;
      }

      .sidebar-title {
        margin: 4px 8px 14px;
        color: var(--scip-text-3);
        font-size: 10px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 900;
      }

      .sidebar-group {
        margin: 16px 8px 8px;
        color: var(--scip-gold-light);
        font-size: 10px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 900;
      }

      .sidebar-button {
        width: 100%;
        display: grid;
        grid-template-columns: 34px 1fr;
        gap: 8px;
        align-items: center;
        text-align: left;
        border-radius: 18px;
        padding: 10px;
        margin-bottom: 6px;
      }

      .sidebar-section-label { font-size: 12px; font-weight: 780; line-height: 1.25; }

      .content-column {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .story-rail {
        border-radius: 26px;
        padding: 10px;
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 8px;
      }

      .story-button {
        border-radius: 18px;
        min-height: 58px;
        padding: 10px 12px;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        flex-direction: column;
        text-align: left;
      }

      .main-surface {
        flex: 1;
        min-height: 0;
        overflow: auto;
        border-radius: 34px;
        padding: clamp(22px, 3vw, 42px);
      }

      .present-surface {
        height: 100%;
        padding: clamp(28px, 5vw, 72px);
        border-radius: 0;
      }

      .section-header {
        display: flex;
        justify-content: space-between;
        gap: 18px;
        align-items: flex-start;
        margin-bottom: 24px;
      }

      .section-title {
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(36px, 4vw, 62px);
        line-height: 0.98;
        letter-spacing: -0.055em;
        color: var(--scip-text);
      }

      .section-subtitle {
        margin: 14px 0 0;
        max-width: 760px;
        color: var(--scip-text-2);
        line-height: 1.65;
        font-size: 15px;
      }

      .status-chip {
        flex: 0 0 auto;
        border-radius: 999px;
        border: 1px solid rgba(226,199,108,0.26);
        background: rgba(201,168,76,0.10);
        color: var(--scip-gold-light);
        padding: 9px 13px;
        font-size: 11px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 900;
      }

      .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 16px;
      }

      .kpi-card {
        border-radius: 24px;
        padding: 20px;
        min-height: 132px;
      }

      .kpi-label {
        color: var(--scip-text-3);
        font-size: 11px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 900;
        margin-bottom: 14px;
      }

      .kpi-value {
        color: var(--scip-text);
        font-size: clamp(24px, 2.4vw, 34px);
        font-weight: 850;
        letter-spacing: -0.05em;
      }

      .kpi-note {
        margin-top: 9px;
        color: var(--scip-text-3);
        font-size: 12px;
        line-height: 1.45;
      }

      .insight-grid {
        display: grid;
        grid-template-columns: 1.1fr 0.9fr;
        gap: 16px;
      }

      .insight-stack { display: grid; gap: 16px; }

      .narrative-card,
      .action-card {
        border-radius: 26px;
        padding: 24px;
      }

      .card-title {
        margin: 0 0 10px;
        font-size: 17px;
        font-weight: 880;
        color: var(--scip-text);
      }

      .card-body {
        margin: 0;
        color: var(--scip-text-2);
        line-height: 1.65;
        font-size: 14px;
      }

      .signal-list {
        display: grid;
        gap: 10px;
        margin-top: 18px;
      }

      .signal-row {
        display: grid;
        grid-template-columns: 12px 1fr;
        gap: 10px;
        align-items: start;
        color: var(--scip-text-2);
        font-size: 13px;
        line-height: 1.5;
      }

      .signal-dot {
        width: 8px;
        height: 8px;
        border-radius: 99px;
        margin-top: 6px;
        background: var(--scip-gold);
        box-shadow: 0 0 0 5px rgba(201,168,76,0.10);
      }

      .data-status {
        border-radius: 22px;
        padding: 14px 16px;
        margin-bottom: 16px;
        color: var(--scip-text-2);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
      }

      .data-status strong { color: var(--scip-text); }

      .quickball-shell {
        position: fixed;
        left: 50%;
        bottom: 22px;
        transform: translateX(-50%);
        z-index: 50;
        width: min(760px, calc(100vw - 40px));
        pointer-events: none;
      }

      .qb-capsule {
        pointer-events: auto;
        width: min(540px, 100%);
        min-height: 56px;
        margin: 0 auto;
        border-radius: 999px;
        padding: 10px 12px 10px 22px;
        border: 1px solid rgba(255,255,255,0.14);
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: var(--scip-text-2);
        cursor: pointer;
        transition: transform 240ms var(--scip-ease), border-color 240ms var(--scip-ease);
      }

      .qb-capsule:hover,
      .qb-capsule:focus-visible {
        transform: translateY(-3px);
        border-color: rgba(226,199,108,0.42);
        outline: none;
      }

      .qb-capsule-main { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
      .qb-capsule-label { color: var(--scip-text); font-weight: 850; }
      .qb-capsule-hint { color: var(--scip-text-3); font-size: 11px; }
      .qb-key {
        min-width: 34px;
        height: 34px;
        display: grid;
        place-items: center;
        border-radius: 999px;
        border: 1px solid rgba(226,199,108,0.34);
        color: var(--scip-gold-light);
        background: rgba(201,168,76,0.10);
        font-size: 12px;
        font-weight: 900;
      }

      .quickball-panel {
        pointer-events: auto;
        border-radius: 30px;
        padding: 18px;
        transform-origin: bottom center;
        animation: qb-rise 280ms var(--scip-ease) both;
      }

      .qb-panel-header {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: flex-start;
        margin-bottom: 12px;
      }

      .qb-title { font-size: 18px; font-weight: 900; color: var(--scip-text); }
      .qb-context { margin-top: 4px; color: var(--scip-text-3); font-size: 12px; }
      .qb-close {
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.04);
        color: var(--scip-text-2);
        width: 36px;
        height: 36px;
        border-radius: 999px;
        cursor: pointer;
      }

      .qb-messages {
        max-height: 230px;
        overflow: auto;
        display: grid;
        gap: 10px;
        padding: 4px 2px 12px;
      }

      .qb-empty { color: var(--scip-text-3); font-size: 13px; line-height: 1.55; }
      .qb-message {
        border-radius: 18px;
        padding: 12px 14px;
        font-size: 13px;
        line-height: 1.5;
      }
      .qb-message.user { background: rgba(226,199,108,0.12); color: var(--scip-text); justify-self: end; max-width: 82%; }
      .qb-message.assistant { background: rgba(255,255,255,0.06); color: var(--scip-text-2); justify-self: start; max-width: 88%; }
      .qb-message.error { background: rgba(239,68,68,0.10); color: #fecaca; justify-self: start; max-width: 88%; }

      .qb-input-row {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 10px;
        align-items: end;
      }

      .qb-textarea {
        width: 100%;
        min-height: 54px;
        resize: vertical;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.12);
        background: rgba(8,13,20,0.70);
        color: var(--scip-text);
        padding: 13px 14px;
        outline: none;
      }

      .qb-textarea:focus { border-color: rgba(226,199,108,0.45); }

      .qb-send {
        height: 54px;
        border: 0;
        border-radius: 18px;
        padding: 0 18px;
        background: linear-gradient(135deg, var(--scip-gold-light), var(--scip-gold));
        color: #10131a;
        font-weight: 900;
        cursor: pointer;
      }

      .qb-send:disabled { opacity: 0.45; cursor: not-allowed; }

      .prompt-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
      }

      .prompt-button {
        border-radius: 999px;
        padding: 8px 11px;
        font-size: 12px;
        font-weight: 750;
      }


      .world-grid,
      .curiosity-row,
      .action-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .world-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin: 18px 0 18px;
      }

      .world-card {
        border-radius: 26px;
        padding: 22px;
        min-height: 166px;
        text-align: left;
        color: var(--scip-text);
        cursor: pointer;
        transition: transform 240ms var(--scip-ease), border-color 240ms var(--scip-ease), background 240ms var(--scip-ease);
      }

      .world-card:hover,
      .world-card:focus-visible {
        transform: translateY(-4px);
        border-color: rgba(226,199,108,0.42);
        outline: none;
      }

      .world-card h2 {
        margin: 8px 0 8px;
        font-size: 20px;
        letter-spacing: -0.035em;
      }

      .world-card p {
        margin: 0;
        color: var(--scip-text-2);
        line-height: 1.55;
        font-size: 13px;
      }

      .primary-answer {
        border-radius: 28px;
        padding: 24px;
        margin-bottom: 16px;
      }

      .primary-answer h2 {
        margin: 0 0 10px;
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(26px, 2.6vw, 42px);
        line-height: 1.04;
        letter-spacing: -0.045em;
      }

      .primary-answer p {
        margin: 0;
        color: var(--scip-text-2);
        line-height: 1.65;
        max-width: 840px;
      }

      .question-contract {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: var(--scip-gold-light);
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 12px;
      }

      .curiosity-row {
        margin: 16px 0 0;
      }

      .curiosity-chip,
      .action-chip {
        border: 1px solid rgba(255,255,255,0.11);
        background: rgba(255,255,255,0.045);
        color: var(--scip-text-2);
        border-radius: 999px;
        padding: 10px 13px;
        cursor: pointer;
        font-size: 12px;
        font-weight: 850;
        transition: background 220ms var(--scip-ease), color 220ms var(--scip-ease), border-color 220ms var(--scip-ease), transform 220ms var(--scip-ease);
      }

      .curiosity-chip:hover,
      .action-chip:hover,
      .curiosity-chip.is-active,
      .action-chip.is-active {
        color: #10131a;
        background: linear-gradient(135deg, var(--scip-gold-light), var(--scip-gold));
        border-color: rgba(226,199,108,0.72);
        transform: translateY(-2px);
      }

      .explanation-drawer,
      .evidence-panel,
      .action-layer {
        border-radius: 26px;
        padding: 22px;
        margin: 16px 0;
        animation: qb-rise 260ms var(--scip-ease) both;
      }

      .explanation-drawer h3,
      .evidence-panel h3,
      .action-layer h3 {
        margin: 0 0 10px;
        color: var(--scip-text);
        font-size: 18px;
      }

      .explanation-list {
        margin: 0;
        padding-left: 18px;
        color: var(--scip-text-2);
        line-height: 1.65;
        font-size: 14px;
      }

      .evidence-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin-top: 14px;
      }

      .evidence-tile {
        border-radius: 20px;
        padding: 16px;
      }

      .evidence-tile strong {
        display: block;
        color: var(--scip-text);
        margin-bottom: 6px;
      }

      .evidence-tile span {
        color: var(--scip-text-3);
        font-size: 12px;
        line-height: 1.45;
      }

      @keyframes scip-drift-a {
        from { transform: translate3d(0, 0, 0) scale(1); }
        to { transform: translate3d(80px, 56px, 0) scale(1.08); }
      }

      @keyframes scip-drift-b {
        from { transform: translate3d(0, 0, 0) scale(1); }
        to { transform: translate3d(-82px, -42px, 0) scale(1.06); }
      }

      @keyframes qb-rise {
        from { transform: translateY(14px) scale(0.98); opacity: 0; }
        to { transform: translateY(0) scale(1); opacity: 1; }
      }

      @media (max-width: 1120px) {
        .context-island { grid-template-columns: 1fr; align-items: start; }
        .context-middle { justify-content: flex-start; }
        .context-right { justify-content: flex-start; }
        .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .insight-grid { grid-template-columns: 1fr; }
      }

      @media (max-width: 780px) {
        .landing-shell { padding: 22px 18px 96px; }
        .landing-topbar { align-items: flex-start; gap: 12px; flex-direction: column; }
        .entry-grid { grid-template-columns: 1fr; }
        .entry-card { min-height: 210px; }
        .app-shell { padding: 12px; }
        .shell-body { flex-direction: column; overflow: auto; }
        .compact-rail { width: 100%; flex-direction: row; overflow-x: auto; }
        .rail-button { min-width: 128px; }
        .story-rail { grid-template-columns: 1fr; }
        .full-sidebar { width: 100%; max-height: 240px; }
        .main-surface { overflow: visible; }
        .kpi-grid, .world-grid, .evidence-grid { grid-template-columns: 1fr; }
        .section-header { flex-direction: column; }
      }

      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          scroll-behavior: auto !important;
          transition-duration: 0.01ms !important;
        }
      }
    `}</style>
  );
}

function SCIPLanding({ computed, onOpenView }) {
  return (
    <section className="landing-shell" aria-label="SCIP arrival screen">
      <div className="landing-topbar">
        <div className="brand-lockup" aria-label="SCIP">
          <span className="brand-mark">SCIP</span>
          <span className="brand-subtitle">Sobha Collections Intelligence Platform</span>
        </div>
        <span className="data-date">Data: {safeSnapshotDate(computed)}</span>
      </div>

      <div className="landing-center">
        <div>
          <div className="landing-copy">
            <p className="landing-kicker">Collections intelligence, refined</p>
            <h1 className="landing-title">Begin with the signal.</h1>
            <p className="landing-subtitle">
              Choose the operational pulse for what needs attention now, or open the executive narrative for the story behind the numbers.
            </p>
          </div>

          <div className="entry-grid">
            <button className="entry-card glass-card" onClick={() => onOpenView("pulse")}>
              <span className="entry-icon">LP</span>
              <h2>Live Pulse</h2>
              <p>Today&apos;s position, movement, risk, and operational focus.</p>
              <span className="entry-cta"><span>Open Pulse</span><span>-&gt;</span></span>
            </button>

            <button className="entry-card glass-card" onClick={() => onOpenView("narratives")}>
              <span className="entry-icon">NR</span>
              <h2>Narratives</h2>
              <p>Board-ready interpretation across collections, portfolio, dues, advance, and roadmap.</p>
              <span className="entry-cta"><span>Open Story</span><span>-&gt;</span></span>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

function ContextIsland({
  view,
  mode,
  activeSection,
  pulseFocus,
  computed,
  entity,
  targetVersion,
  onHome,
  onModeChange,
  onEntityChange,
  onTargetVersionChange,
  onSectionChange,
  onPulseFocusChange,
}) {
  const viewLabel = view === "pulse" ? "Live Pulse" : "Narratives";

  return (
    <header className="context-island glass-island" role="banner">
      <button className="logo-button" onClick={onHome} aria-label="Return to SCIP home">
        <span className="logo-main">SCIP</span>
        <span className="logo-stack">
          <span className="logo-caption">Sobha Collections</span>
          <span className="logo-caption">{viewLabel}</span>
        </span>
      </button>

      <div className="context-middle">
        <FilterGroup
          entity={entity}
          targetVersion={targetVersion}
          mode={mode}
          onEntityChange={onEntityChange}
          onTargetVersionChange={onTargetVersionChange}
        />
      </div>

      <div className="context-right">
        <span className="data-date">Data: {safeSnapshotDate(computed)}</span>
        {view === "narratives" ? (
          <NarrativeDepthControl mode={mode} onModeChange={onModeChange} />
        ) : (
          <PulseFocusControl pulseFocus={pulseFocus} onPulseFocusChange={onPulseFocusChange} />
        )}
      </div>
    </header>
  );
}

function FilterGroup({ entity, targetVersion, mode, onEntityChange, onTargetVersionChange }) {
  const entities = ["Group", "Sobha", "Siniya", "DT"];
  const targets = ["MDO Dues", "Finance Dues"];
  const showTarget = mode !== "board" && mode !== "present";

  return (
    <div className="filter-group" aria-label="Context filters">
      <span className="filter-label">Entity</span>
      {entities.map((item) => (
        <button
          key={item}
          type="button"
          className={`pill-button ${entity === item ? "is-active" : ""}`}
          onClick={() => onEntityChange(item)}
          aria-pressed={entity === item}
        >
          {item}
        </button>
      ))}
      {showTarget && <span className="filter-label" style={{ marginLeft: 8 }}>Target</span>}
      {showTarget && targets.map((item) => (
        <button
          key={item}
          type="button"
          className={`pill-button ${targetVersion === item ? "is-active" : ""}`}
          onClick={() => onTargetVersionChange(item)}
          aria-pressed={targetVersion === item}
        >
          {item}
        </button>
      ))}
    </div>
  );
}

function NarrativeDepthControl({ mode, onModeChange }) {
  const items = [
    { mode: "board", label: "Executive View" },
    { mode: "ops", label: "Detailed View" },
    { mode: "present", label: "Present" },
  ];

  return (
    <div className="depth-control" aria-label="Narrative depth">
      {items.map((item) => (
        <button
          key={item.mode}
          type="button"
          className={`depth-button ${mode === item.mode ? "is-active" : ""}`}
          onClick={() => onModeChange(item.mode)}
          aria-pressed={mode === item.mode}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

function PulseFocusControl({ pulseFocus, onPulseFocusChange }) {
  const items = [
    { focus: "current", label: "Current Signal" },
    { focus: "month", label: "This Month" },
    { focus: "ytd", label: "Year-to-Date" },
    { focus: "risk", label: "Risk & Action" },
  ];

  return (
    <div className="depth-control" aria-label="Live Pulse focus">
      {items.map((item) => (
        <button
          key={item.focus}
          type="button"
          className={`depth-button ${pulseFocus === item.focus ? "is-active" : ""}`}
          onClick={() => onPulseFocusChange(item.focus)}
          aria-pressed={pulseFocus === item.focus}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

function CompactPulseRail({ pulseFocus, onPulseFocusChange }) {
  return (
    <nav className="compact-rail glass-rail" aria-label="Live Pulse navigation">
      {PULSE_NAV.map((item) => (
        <button
          key={item.focus}
          type="button"
          className={`rail-button ${pulseFocus === item.focus ? "is-active" : ""}`}
          onClick={() => onPulseFocusChange(item.focus)}
          aria-current={pulseFocus === item.focus ? "page" : undefined}
        >
          <span className="rail-eyebrow">{item.eyebrow}</span>
          <span className="rail-label">{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

function StoryRail({ activeSection, onSectionChange }) {
  return (
    <nav className="story-rail glass-rail" aria-label="Narrative story rail">
      {STORY_NAV.map((item) => (
        <button
          key={item.id}
          type="button"
          className={`story-button ${activeSection === item.id ? "is-active" : ""}`}
          onClick={() => onSectionChange(item.id)}
          aria-current={activeSection === item.id ? "page" : undefined}
        >
          <span className="story-eyebrow">{item.eyebrow}</span>
          <span className="story-label">{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

function FullSidebar({ activeSection, onSectionChange }) {
  let currentGroup = null;

  return (
    <aside className="full-sidebar glass-rail" aria-label="Detailed platform navigation">
      <div className="sidebar-title">Detailed platform map</div>
      {FULL_NAV.map((item) => {
        const showGroup = item.group !== currentGroup;
        currentGroup = item.group;
        return (
          <div key={item.id}>
            {showGroup && <div className="sidebar-group">{item.group}</div>}
            <button
              type="button"
              className={`sidebar-button ${activeSection === item.id ? "is-active" : ""}`}
              onClick={() => onSectionChange(item.id)}
              aria-current={activeSection === item.id ? "page" : undefined}
            >
              <span className="sidebar-section-id">{item.id}</span>
              <span className="sidebar-section-label">{item.label}</span>
            </button>
          </div>
        );
      })}
    </aside>
  );
}

function DataStatus({ loading, error }) {
  if (!loading && !error) return null;

  return (
    <div className="data-status solid-card" role={error ? "alert" : "status"}>
      <span>
        <strong>{loading ? "Connecting to platform data" : "Data pending refresh"}</strong>
        {loading
          ? " - backend summary is loading. The intelligence surface remains available."
          : ` - ${error}`}
      </span>
      <span className="status-chip">Backend</span>
    </div>
  );
}

function MainContent({ view, mode, activeSection, pulseFocus, computed, filters, loading, error }) {
  const meta = SECTION_META[activeSection] || SECTION_META.S01;
  const surfaceClass = mode === "present" ? "main-surface present-surface solid-card" : "main-surface solid-card";

  return (
    <main className={surfaceClass} id="main-content" tabIndex={-1}>
      <DataStatus loading={loading} error={error} />
      {view === "pulse" ? (
        <LivePulseContent activeSection={activeSection} pulseFocus={pulseFocus} meta={meta} computed={computed} filters={filters} />
      ) : (
        <NarrativesContent activeSection={activeSection} meta={meta} mode={mode} computed={computed} filters={filters} />
      )}
    </main>
  );
}

function LivePulseContent({ activeSection, pulseFocus, meta, computed, filters }) {
  const [depthPanel, setDepthPanel] = useState(null);
  const odToday = computed?.od_today_group ?? null;
  const odSobha = computed?.od_sobha ?? null;
  const odSiniya = computed?.od_siniya ?? null;
  const odDt = computed?.od_dt ?? null;
  const cyAdvMix = computed?.cy_adv_mix_ytd ?? null;

  const openFocus = (focus) => {
    setDepthPanel(null);
    const event = new CustomEvent("scip:setPulseFocus", { detail: focus });
    window.dispatchEvent(event);
  };

  if (pulseFocus === "home") {
    return (
      <>
        <SectionHeader
          kicker="L1 / Live Pulse world"
          title="What needs attention now?"
          subtitle="Current position, movement, risk, and action. Choose one natural lens instead of operating the whole platform."
          chip={`${filters.entity} / ${filters.targetVersion}`}
        />

        <div className="primary-answer glass-card">
          <span className="question-contract">Primary answer</span>
          <h2>Start with the current signal, then deepen only where curiosity demands it.</h2>
          <p>
            Live Pulse now keeps MTD, YTD, and risk as natural time and action lenses. Collectors, calculators, definitions, and dense operational evidence stay hidden until the user asks for detail.
          </p>
        </div>

        <div className="world-grid" aria-label="Live Pulse lenses">
          <WorldCard kicker="Are we okay today?" title="Current Signal" body="OD today, required pace, actual movement, and the first risk flag." onClick={() => openFocus("current")} />
          <WorldCard kicker="How is this month moving?" title="This Month" body="MTD momentum, dues and advance mix, daily movement, and run-rate questions." onClick={() => openFocus("month")} />
          <WorldCard kicker="Are we on target?" title="Year-to-Date" body="YTD achievement, target track, MDO vs Finance basis, and the larger trend." onClick={() => openFocus("ytd")} />
        </div>

        <div className="action-layer solid-card">
          <h3>Natural next question</h3>
          <div className="action-row">
            <button className="action-chip" type="button" onClick={() => openFocus("risk")}>Where should we act?</button>
            <button className="action-chip" type="button" onClick={() => setDepthPanel("evidence")}>Show evidence map</button>
            <button className="action-chip" type="button" onClick={() => setDepthPanel("action")}>Prepare morning ops summary</button>
          </div>
        </div>

        {depthPanel && <DepthPanel kind={depthPanel} view="pulse" focus="home" />}
      </>
    );
  }

  const focus = getPulseFocusModel(pulseFocus, activeSection);

  return (
    <>
      <SectionHeader
        kicker={`L2 / ${focus.level}`}
        title={focus.title}
        subtitle={focus.question}
        chip={`${filters.entity} / ${filters.targetVersion}`}
      />

      <div className="primary-answer glass-card">
        <span className="question-contract">Primary answer</span>
        <h2>{focus.headline}</h2>
        <p>{focus.answer}</p>
        <div className="curiosity-row" aria-label="Natural next questions">
          {focus.chips.map((chip) => (
            <button
              key={chip.kind}
              className={`curiosity-chip ${depthPanel === chip.kind ? "is-active" : ""}`}
              type="button"
              onClick={() => setDepthPanel(depthPanel === chip.kind ? null : chip.kind)}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      <div className="kpi-grid" aria-label={`${focus.title} metrics`}>
        <KpiCard label={focus.kpis[0]} value={formatAedBillionsFromMillions(odToday)} note="Live backend value when available." />
        <KpiCard label={focus.kpis[1]} value={formatAedMillions(odSobha)} note="Sobha entity movement / exposure." />
        <KpiCard label={focus.kpis[2]} value={formatAedMillions(odSiniya)} note="Siniya entity movement / exposure." />
        <KpiCard label={focus.kpis[3]} value={formatPercent(cyAdvMix)} note="Collection mix signal from computed summary." />
      </div>

      {depthPanel && <DepthPanel kind={depthPanel} view="pulse" focus={pulseFocus} />}

      <div className="insight-grid">
        <div className="narrative-card solid-card">
          <p className="card-kicker">Primary visual</p>
          <h2 className="card-title">{focus.visualTitle}</h2>
          <p className="card-body">{focus.visualBody}</p>
          <div className="signal-list">
            <SignalRow>Glass is used for navigation, curiosity, and explanation.</SignalRow>
            <SignalRow>Solid surfaces are used for numbers, charts, tables, and evidence.</SignalRow>
            <SignalRow>The old platform tree remains available only when the user requests detail.</SignalRow>
          </div>
        </div>

        <div className="insight-stack">
          <div className="action-card solid-card">
            <p className="card-kicker">L5 action</p>
            <h2 className="card-title">Move from signal to action.</h2>
            <p className="card-body">Use the action layer for ops summaries, run-rate calculators, collector action lists, exports, or Quickball explanation.</p>
          </div>
          <div className="action-card solid-card">
            <p className="card-kicker">Entity exposure</p>
            <h2 className="card-title">Evidence remains one level deeper.</h2>
            <p className="card-body">Ask for entity split, collectors, ageing, source basis, formula, or full trend before dense data appears.</p>
          </div>
        </div>
      </div>

      {depthPanel === "evidence" && <EntityStrip odSobha={odSobha} odSiniya={odSiniya} odDt={odDt} />}
    </>
  );
}

function WorldCard({ kicker, title, body, onClick }) {
  return (
    <button className="world-card glass-card" type="button" onClick={onClick}>
      <p className="card-kicker">{kicker}</p>
      <h2>{title}</h2>
      <p>{body}</p>
      <span className="entry-cta"><span>Open</span><span>-&gt;</span></span>
    </button>
  );
}

function getPulseFocusModel(pulseFocus, activeSection) {
  const models = {
    current: {
      level: "Current Signal",
      title: "Current Signal",
      question: "Are we okay today?",
      headline: "Collections are read as a current signal before the user sees the whole operating model.",
      answer: "The screen holds one answer, four supporting metrics, one primary visual, and three next questions: why, which entity, and what action.",
      kpis: ["OD Today", "Sobha Exposure", "Siniya Exposure", "Advance Mix"],
      visualTitle: "Daily movement chart placeholder",
      visualBody: "This is where the small daily movement visual belongs. Full trend, formulas, and source basis live in the evidence layer.",
      chips: [
        { kind: "why", label: "Why?" },
        { kind: "entity", label: "Which entity?" },
        { kind: "action", label: "What action?" },
      ],
    },
    month: {
      level: "This Month",
      title: "This Month",
      question: "How is this month moving?",
      headline: "MTD becomes a natural time lens, not a dashboard label.",
      answer: "The user sees month movement first, then can ask for run rate, entity split, or collector impact without leaving the screen.",
      kpis: ["Dues MTD", "Sobha MTD", "Siniya MTD", "Advance MTD Mix"],
      visualTitle: "Daily bars / run-rate visual placeholder",
      visualBody: "Daily bars should remain solid and readable. The explanation drawer can state why MTD is below, on, or above pace.",
      chips: [
        { kind: "why", label: "Explain MTD" },
        { kind: "entity", label: "Show entity split" },
        { kind: "evidence", label: "Show collector impact" },
      ],
    },
    ytd: {
      level: "Year-to-Date",
      title: "Year-to-Date",
      question: "Are we on target this year?",
      headline: "YTD progress is treated as target track and interpretation, not raw period switching.",
      answer: "The user can compare target gap, MDO vs Finance basis, and full trend charts only when they ask for evidence.",
      kpis: ["YTD Position", "Sobha YTD", "Siniya YTD", "CY Advance Mix"],
      visualTitle: "Target vs actual trend placeholder",
      visualBody: "The primary chart should answer target track. Detailed target definitions and Finance/MDO basis stay one level deeper.",
      chips: [
        { kind: "why", label: "Explain gap" },
        { kind: "evidence", label: "Compare MDO vs Finance" },
        { kind: "action", label: "Prepare board summary" },
      ],
    },
    risk: {
      level: "Risk & Action",
      title: "Risk & Action",
      question: "Where should we act?",
      headline: "Risk is presented as ranked attention, not another section list.",
      answer: "The user sees the highest attention areas first, then can ask for dues risk, collectors, coverage gaps, or operational evidence.",
      kpis: ["OD Today", "Termination Gap", "Coverage Gap", "NS Gap"],
      visualTitle: "Risk ranking placeholder",
      visualBody: "Risk ranking should lead directly to actions and owners. Dense collector tables remain in the evidence layer.",
      chips: [
        { kind: "why", label: "Show dues risk" },
        { kind: "entity", label: "Show collectors" },
        { kind: "action", label: "Show roadmap action" },
      ],
    },
  };

  return models[pulseFocus] || models.current;
}

function DepthPanel({ kind, view, focus }) {
  if (kind === "evidence") {
    return (
      <div className="evidence-panel solid-card">
        <h3>L4 Evidence layer</h3>
        <p className="card-body">Evidence appears only after the user asks for it: entity split, collectors, OD ageing, source basis, target definition, full trend, or formula.</p>
        <div className="evidence-grid">
          <EvidenceTile title="Charts" body="Full trend, target vs actual, daily bars, movement bridge." />
          <EvidenceTile title="Tables" body="Entity panels, collector contribution, ageing, coverage gaps." />
          <EvidenceTile title="Definitions" body="MDO / Finance basis, source notes, formulas, interpretation rules." />
        </div>
      </div>
    );
  }

  if (kind === "action") {
    return (
      <div className="action-layer solid-card">
        <h3>L5 Action layer</h3>
        <div className="action-row">
          <button className="action-chip" type="button">Prepare summary</button>
          <button className="action-chip" type="button">Open calculator</button>
          <button className="action-chip" type="button">Ask Quickball</button>
        </div>
      </div>
    );
  }

  const title = kind === "entity" ? "Which entity drove it" : "Why this moved";
  const points = kind === "entity"
    ? [
        "Entity split is shown as an explanation first, not a table by default.",
        "Sobha, Siniya, and DT remain visible only when the current question needs attribution.",
        "The next step should be either collector detail or evidence, not a full platform jump.",
      ]
    : [
        "Dues contribution, NS movement, and advance mix should be interpreted in short plain-English points.",
        "The explanation drawer should contain three to five points, not a chart library.",
        "From here, the user can request entity split, collectors, or the source definition.",
      ];

  return (
    <div className="explanation-drawer glass-card">
      <h3>L3 / {title}</h3>
      <ol className="explanation-list">
        {points.map((point) => <li key={point}>{point}</li>)}
      </ol>
      <div className="curiosity-row">
        <button className="curiosity-chip" type="button">Show detail</button>
        <button className="curiosity-chip" type="button">Prepare summary</button>
      </div>
    </div>
  );
}

function EvidenceTile({ title, body }) {
  return (
    <div className="evidence-tile solid-card">
      <strong>{title}</strong>
      <span>{body}</span>
    </div>
  );
}

function NarrativesContent({ activeSection, meta, mode, computed, filters }) {
  const [depthPanel, setDepthPanel] = useState(null);
  const odToday = computed?.od_today_group ?? null;
  const cyAdvMix = computed?.cy_adv_mix_ytd ?? null;
  const snapshotDate = safeSnapshotDate(computed);
  const viewLabel = mode === "present" ? "Present" : mode === "ops" ? "Detailed View" : "Executive View";
  const focus = getNarrativeFocusModel(activeSection);

  return (
    <>
      <SectionHeader
        kicker={mode === "ops" ? "L4 / Detailed evidence" : "L2 / Narrative focus"}
        title={mode === "board" || mode === "present" ? focus.title : meta.label}
        subtitle={focus.question}
        chip={viewLabel}
      />

      <div className="primary-answer glass-card">
        <span className="question-contract">Primary answer</span>
        <h2>{focus.headline}</h2>
        <p>{focus.answer}</p>
        <div className="curiosity-row" aria-label="Narrative next questions">
          {focus.chips.map((chip) => (
            <button
              key={chip.kind}
              className={`curiosity-chip ${depthPanel === chip.kind ? "is-active" : ""}`}
              type="button"
              onClick={() => setDepthPanel(depthPanel === chip.kind ? null : chip.kind)}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      <div className="kpi-grid" aria-label="Narrative metrics">
        <KpiCard label="Board path" value={SECTION_META[activeSection]?.short || "Story"} note="Story, Portfolio, Dues, Advance, Roadmap." />
        <KpiCard label="OD Today" value={formatAedBillionsFromMillions(odToday)} note={`Snapshot: ${snapshotDate}`} />
        <KpiCard label="Advance Mix YTD" value={formatPercent(cyAdvMix)} note="Supports liquidity and collection narrative." />
        <KpiCard label="Context" value={filters.entity} note={mode === "ops" ? filters.targetVersion : "Executive board lens"} />
      </div>

      {depthPanel && <DepthPanel kind={depthPanel} view="narratives" focus={activeSection} />}

      <div className="insight-grid">
        <div className="narrative-card solid-card">
          <p className="card-kicker">Guided storyline</p>
          <h2 className="card-title">{meta.kicker}: {meta.label}</h2>
          <p className="card-body">
            Narratives now behave like a briefing sequence. Each stage answers one boardroom question, offers two or three curiosity paths, and keeps detailed evidence behind request-driven drawers or Detailed View.
          </p>
          <div className="signal-list">
            <SignalRow>Story maps to S01 Strategic Narrative.</SignalRow>
            <SignalRow>Portfolio maps to S02 Portfolio Overview.</SignalRow>
            <SignalRow>Dues, Advance, and Roadmap map to S04, S05, and S08.</SignalRow>
          </div>
        </div>

        <div className="insight-stack">
          <div className="action-card solid-card">
            <p className="card-kicker">L5 action</p>
            <h2 className="card-title">Action belongs to the current context.</h2>
            <p className="card-body">Present mode, board Q&A, executive summary, one-pager, and Quickball explanation are contextual actions, not global menu clutter.</p>
          </div>
          <div className="action-card solid-card">
            <p className="card-kicker">Depth language</p>
            <h2 className="card-title">Executive, Detailed, Present.</h2>
            <p className="card-body">Internally, SCIP still preserves board, ops, and present modes. Visually, users only see a natural depth control.</p>
          </div>
        </div>
      </div>
    </>
  );
}

function getNarrativeFocusModel(activeSection) {
  const models = {
    S01: {
      title: "Story",
      question: "What is the story?",
      headline: "The board journey begins with one strategic narrative, not the whole platform map.",
      answer: "The page should show one board-level headline, three supporting KPIs, one visual, and the next natural story step.",
      chips: [
        { kind: "why", label: "Why this story?" },
        { kind: "evidence", label: "Show definitions" },
        { kind: "action", label: "Prepare board Q&A" },
      ],
    },
    S02: {
      title: "Portfolio",
      question: "What is the portfolio position?",
      headline: "Portfolio explains the health behind collections movement.",
      answer: "The executive sees portfolio position first, then can ask for target performance, MDO / Finance detail, or market context.",
      chips: [
        { kind: "why", label: "Explain position" },
        { kind: "evidence", label: "Show MDO / Finance detail" },
        { kind: "action", label: "Summarize portfolio" },
      ],
    },
    S04: {
      title: "Dues",
      question: "Why is OD elevated?",
      headline: "Dues should move from OD position to ageing, efficiency, then governance evidence.",
      answer: "The user gets the dues interpretation first and only enters OD ageing, collector detail, or governance flags after asking for evidence.",
      chips: [
        { kind: "why", label: "Explain OD" },
        { kind: "entity", label: "Which entity?" },
        { kind: "evidence", label: "Show governance evidence" },
      ],
    },
    S05: {
      title: "Advance",
      question: "What is the advance collections story?",
      headline: "Advance is interpreted as mix, penetration, liquidity support, and future opportunity.",
      answer: "CY/FY mix, penetration, rebate strategy, and NPV detail are progressive depth layers rather than first-screen complexity.",
      chips: [
        { kind: "why", label: "Explain mix" },
        { kind: "evidence", label: "Show penetration detail" },
        { kind: "action", label: "Create executive note" },
      ],
    },
    S08: {
      title: "Roadmap",
      question: "What should we do next?",
      headline: "Roadmap connects risk exposure to the initiative pipeline and executive decisions.",
      answer: "The user sees top initiatives first, then can open risk-linked advisories or the full pipeline only when needed.",
      chips: [
        { kind: "why", label: "Explain initiatives" },
        { kind: "evidence", label: "Show full pipeline" },
        { kind: "action", label: "Open Present view" },
      ],
    },
  };
  return models[activeSection] || models.S01;
}

function SectionHeader({ kicker, title, subtitle, chip }) {
  return (
    <div className="section-header">
      <div>
        <p className="section-kicker">{kicker}</p>
        <h1 className="section-title">{title}</h1>
        <p className="section-subtitle">{subtitle}</p>
      </div>
      <span className="status-chip">{chip}</span>
    </div>
  );
}

function KpiCard({ label, value, note }) {
  return (
    <div className="kpi-card solid-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-note">{note}</div>
    </div>
  );
}

function SignalRow({ children }) {
  return (
    <div className="signal-row">
      <span className="signal-dot" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

function EntityStrip({ odSobha, odSiniya, odDt }) {
  return (
    <div className="kpi-grid" style={{ marginTop: 16, marginBottom: 0 }} aria-label="Entity exposure">
      <KpiCard label="Sobha" value={formatAedMillions(odSobha)} note="Entity position from computed summary." />
      <KpiCard label="Siniya" value={formatAedMillions(odSiniya)} note="Entity position from computed summary." />
      <KpiCard label="DT" value={formatAedMillions(odDt)} note="Entity position from computed summary." />
      <KpiCard label="Next action" value="Ask QB" note="Use the command layer for interpretation and follow-up." />
    </div>
  );
}

function getQuickballSuggestions(view, activeSection) {
  if (view === "landing") {
    return [
      "What should I look at first?",
      "Summarize current collections signal.",
      "Prepare a board-ready opening.",
    ];
  }

  if (view === "pulse") {
    return [
      "What changed since the last snapshot?",
      "Where is collection risk highest?",
      "Which entity needs attention today?",
      "Summarize today for AGM dues.",
    ];
  }

  const sectionLabel = SECTION_META[activeSection]?.label || "this narrative";
  return [
    `Prepare board Q&A for ${sectionLabel}.`,
    "Explain OD movement.",
    "Create executive summary.",
    "What is the advance collections story?",
  ];
}

function QuickballCapsule({ backendUrl, mode, view, activeSection, entity, targetVersion }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [offline, setOffline] = useState(false);

  const suggestions = getQuickballSuggestions(view, activeSection);
  const activeLabel = view === "landing" ? "SCIP Lobby" : SECTION_META[activeSection]?.label || "SCIP";

  useEffect(() => {
    if (mode === "present") return undefined;

    const handleKey = (event) => {
      const tag = event.target?.tagName;
      if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
      if (event.metaKey || event.ctrlKey || event.altKey) return;

      if (event.key.toLowerCase() === "q") {
        event.preventDefault();
        setOpen(true);
        return;
      }

      if (event.key.length === 1 && event.key.trim()) {
        event.preventDefault();
        setOpen(true);
        setInput((current) => current || event.key);
      }
    };

    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [mode]);

  const send = useCallback(async () => {
    const question = input.trim();
    if (!question) return;

    setInput("");
    setMessages((current) => [...current, { role: "user", text: question }]);
    setLoading(true);

    try {
      const res = await fetch(`${backendUrl}/quickball`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          mode,
          view,
          context: {
            activeSection,
            sectionLabel: SECTION_META[activeSection]?.label || activeSection,
            entity,
            targetVersion,
          },
        }),
      });

      if (!res.ok) throw new Error(`Backend responded ${res.status}`);
      const json = await res.json();
      setOffline(false);
      setMessages((current) => [
        ...current,
        { role: "assistant", text: json.annotation || json.response || "No response returned." },
      ]);
    } catch {
      setOffline(true);
      setMessages((current) => [
        ...current,
        {
          role: "error",
          text: "Quickball is currently unavailable. The SCIP surface, navigation, and filters remain active.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [activeSection, backendUrl, entity, input, mode, targetVersion, view]);

  const handleTextareaKey = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  };

  if (mode === "present") return null;

  return (
    <div className="quickball-shell" aria-live="polite">
      {!open ? (
        <button className="qb-capsule glass-island" type="button" onClick={() => setOpen(true)}>
          <span className="qb-capsule-main">
            <span className="qb-capsule-label">Ask Quickball...</span>
            <span className="qb-capsule-hint">Press Q or start typing</span>
          </span>
          <span className="qb-key">Q</span>
        </button>
      ) : (
        <section className="quickball-panel glass-card" role="dialog" aria-label="Quickball command layer">
          <div className="qb-panel-header">
            <div>
              <div className="qb-title">Quickball</div>
              <div className="qb-context">
                Context: {activeLabel} / {entity} / {mode === "board" ? "Executive View" : mode === "ops" ? targetVersion : "Present"}
                {offline ? " / Offline" : ""}
              </div>
            </div>
            <button className="qb-close" type="button" onClick={() => setOpen(false)} aria-label="Close Quickball">
              x
            </button>
          </div>

          <div className="qb-messages">
            {messages.length === 0 && (
              <div className="qb-empty">
                Ask about today&apos;s movement, board narrative, entity risk, OD explanation, or action ownership.
              </div>
            )}
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`qb-message ${message.role}`}>
                {message.text}
              </div>
            ))}
            {loading && <div className="qb-message assistant">Thinking...</div>}
          </div>

          <div className="qb-input-row">
            <textarea
              className="qb-textarea"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleTextareaKey}
              rows={2}
              placeholder="Ask anything..."
              autoFocus
            />
            <button className="qb-send" type="button" onClick={send} disabled={loading || !input.trim()}>
              Send
            </button>
          </div>

          <div className="prompt-row" aria-label="Suggested prompts">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                className="prompt-button"
                onClick={() => setInput(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default function App() {
  const initialAppState = useMemo(() => getInitialAppState(), []);

  const [view, setView] = useState(initialAppState.view);
  const [mode, setMode] = useState(initialAppState.mode);
  const [activeSection, setActiveSection] = useState(initialAppState.section);
  const [pulseFocus, setPulseFocus] = useState(initialAppState.pulseFocus);
  const [entity, setEntity] = useState(() => getUrlParam("entity", "Group"));
  const [targetVersion, setTargetVersion] = useState(() => getUrlParam("target", "MDO Dues"));
  const [data, setData] = useState(null);
  const [computed, setComputed] = useState(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [dataError, setDataError] = useState(null);

  const syncUrl = useCallback((next = {}) => {
    replaceUrlState({
      view: next.view ?? view,
      mode: next.mode ?? mode,
      section: next.section ?? activeSection,
      entity: next.entity ?? entity,
      targetVersion: next.targetVersion ?? targetVersion,
      pulseFocus: next.pulseFocus ?? pulseFocus,
    });
  }, [activeSection, entity, mode, pulseFocus, targetVersion, view]);

  const handleOpenView = useCallback((nextView) => {
    const normalizedView = normalizeView(nextView);
    const nextMode = normalizedView === "narratives" ? "board" : "ops";
    const nextSection = normalizedView === "narratives" ? "S01" : "P1";
    const nextPulseFocus = "home";

    setView(normalizedView);
    setMode(nextMode);
    setActiveSection(nextSection);
    setPulseFocus(nextPulseFocus);
    setStoredView(normalizedView);
    replaceUrlState({
      view: normalizedView,
      mode: nextMode,
      section: nextSection,
      entity,
      targetVersion,
      pulseFocus: nextPulseFocus,
    });
  }, [entity, targetVersion]);

  const handleHome = useCallback(() => {
    setView("landing");
    setMode("ops");
    replaceUrlState({ view: "landing", mode: "ops", section: null, entity, targetVersion, pulseFocus });
  }, [entity, pulseFocus, targetVersion]);

  const handleModeChange = useCallback((nextMode) => {
    let nextView = view;
    let nextSection = activeSection;

    if (nextMode === "present") {
      nextView = "narratives";
      nextSection = BOARD_SECTIONS.includes(activeSection) ? activeSection : "S01";
    } else if (nextMode === "board") {
      nextView = "narratives";
      nextSection = BOARD_SECTIONS.includes(activeSection) ? activeSection : "S01";
    } else {
      nextMode = "ops";
      if (view === "landing") nextView = "pulse";
    }

    setView(nextView);
    setMode(nextMode);
    setActiveSection(nextSection);
    if (nextView !== "landing") setStoredView(nextView);
    replaceUrlState({ view: nextView, mode: nextMode, section: nextSection, entity, targetVersion, pulseFocus });
  }, [activeSection, entity, pulseFocus, targetVersion, view]);

  const handleSectionChange = useCallback((sectionId) => {
    const nextPulseFocus = view === "pulse" ? (SECTION_TO_PULSE_FOCUS[sectionId] || pulseFocus) : pulseFocus;
    setActiveSection(sectionId);
    setPulseFocus(nextPulseFocus);
    syncUrl({ section: sectionId, pulseFocus: nextPulseFocus });
    document.getElementById("main-content")?.scrollTo({ top: 0, behavior: "smooth" });
  }, [pulseFocus, syncUrl, view]);

  const handlePulseFocusChange = useCallback((nextFocus) => {
    const normalizedFocus = normalizePulseFocus(nextFocus);
    const nextSection = PULSE_FOCUS_TO_SECTION[normalizedFocus] || "P1";
    setPulseFocus(normalizedFocus);
    setActiveSection(nextSection);
    syncUrl({ section: nextSection, pulseFocus: normalizedFocus });
    document.getElementById("main-content")?.scrollTo({ top: 0, behavior: "smooth" });
  }, [syncUrl]);

  const handleEntityChange = useCallback((nextEntity) => {
    setEntity(nextEntity);
    syncUrl({ entity: nextEntity });
  }, [syncUrl]);

  const handleTargetVersionChange = useCallback((nextTargetVersion) => {
    setTargetVersion(nextTargetVersion);
    syncUrl({ targetVersion: nextTargetVersion });
  }, [syncUrl]);

  useEffect(() => {
    const handler = (event) => {
      handlePulseFocusChange(event.detail);
    };
    window.addEventListener("scip:setPulseFocus", handler);
    return () => window.removeEventListener("scip:setPulseFocus", handler);
  }, [handlePulseFocusChange]);

  useEffect(() => {
    let cancelled = false;

    const fetchSummary = async () => {
      setDataLoading(true);
      setDataError(null);
      try {
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 20000);
        const res = await fetch(`${BACKEND_URL}/summary`, { signal: controller.signal });
        window.clearTimeout(timeout);
        if (!res.ok) throw new Error(`Backend responded ${res.status}`);
        const json = await res.json();
        if (!cancelled) {
          setData(json.data ?? null);
          setComputed(json.computed ?? null);
          setDataError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setDataError(
            err.name === "AbortError"
              ? "Backend is warming up. Try again shortly."
              : `Data pending refresh - ${err.message}`
          );
        }
      } finally {
        if (!cancelled) setDataLoading(false);
      }
    };

    fetchSummary();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const ping = () => {
      fetch(`${BACKEND_URL}/health`, { method: "GET" }).catch(() => {
        // Health ping is non-blocking.
      });
    };

    ping();
    const interval = window.setInterval(ping, HEALTH_PING_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    document.documentElement.style.fontSize = mode === "present" ? "140%" : "";
    return () => {
      document.documentElement.style.fontSize = "";
    };
  }, [mode]);

  useEffect(() => {
    if (mode !== "present") return undefined;
    const handleKey = (event) => {
      if (event.key === "Escape") {
        handleModeChange("board");
        return;
      }
      if (event.key !== "ArrowRight" && event.key !== "ArrowDown" && event.key !== "ArrowLeft" && event.key !== "ArrowUp") return;

      event.preventDefault();
      setActiveSection((current) => {
        const index = BOARD_SECTIONS.indexOf(current);
        const safeIndex = index === -1 ? 0 : index;
        const nextIndex = event.key === "ArrowRight" || event.key === "ArrowDown"
          ? Math.min(safeIndex + 1, BOARD_SECTIONS.length - 1)
          : Math.max(safeIndex - 1, 0);
        const nextSection = BOARD_SECTIONS[nextIndex];
        replaceUrlState({ view: "narratives", mode: "present", section: nextSection, entity, targetVersion, pulseFocus });
        return nextSection;
      });
    };

    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [entity, handleModeChange, mode, pulseFocus, targetVersion]);

  const contextValue = {
    view,
    mode,
    activeSection,
    pulseFocus,
    entity,
    targetVersion,
    data,
    computed,
    backendUrl: BACKEND_URL,
    onViewChange: handleOpenView,
    onModeChange: handleModeChange,
    onSectionChange: handleSectionChange,
    onPulseFocusChange: handlePulseFocusChange,
    onEntityChange: handleEntityChange,
    onTargetVersionChange: handleTargetVersionChange,
  };

  const filters = { entity, targetVersion };
  const isLanding = view === "landing";
  const showFullSidebar = view === "narratives" && mode === "ops";
  const showStoryRail = view === "narratives" && mode !== "ops" && mode !== "present";

  return (
    <AppContext.Provider value={contextValue}>
      <div className="scip-app">
        <GlobalStyles />
        <a href="#main-content" className="skip-link">Skip to main content</a>

        {isLanding ? (
          <SCIPLanding computed={computed} onOpenView={handleOpenView} />
        ) : mode === "present" ? (
          <MainContent
            view="narratives"
            mode={mode}
            activeSection={activeSection}
            pulseFocus={pulseFocus}
            computed={computed}
            filters={filters}
            loading={dataLoading}
            error={dataError}
          />
        ) : (
          <div className="app-shell">
            <ContextIsland
              view={view}
              mode={mode}
              activeSection={activeSection}
              pulseFocus={pulseFocus}
              computed={computed}
              entity={entity}
              targetVersion={targetVersion}
              onHome={handleHome}
              onModeChange={handleModeChange}
              onEntityChange={handleEntityChange}
              onTargetVersionChange={handleTargetVersionChange}
              onSectionChange={handleSectionChange}
              onPulseFocusChange={handlePulseFocusChange}
            />

            <div className="shell-body">
              {view === "pulse" && pulseFocus !== "home" && <CompactPulseRail pulseFocus={pulseFocus} onPulseFocusChange={handlePulseFocusChange} />}
              {showFullSidebar && <FullSidebar activeSection={activeSection} onSectionChange={handleSectionChange} />}

              <div className="content-column">
                {showStoryRail && <StoryRail activeSection={activeSection} onSectionChange={handleSectionChange} />}
                <MainContent
                  view={view}
                  mode={mode}
                  activeSection={activeSection}
                  pulseFocus={pulseFocus}
                  computed={computed}
                  filters={filters}
                  loading={dataLoading}
                  error={dataError}
                />
              </div>
            </div>
          </div>
        )}

        <QuickballCapsule
          backendUrl={BACKEND_URL}
          mode={mode}
          view={view}
          activeSection={activeSection}
          entity={entity}
          targetVersion={targetVersion}
        />
      </div>
    </AppContext.Provider>
  );
}
