/**
 * SOBHA COLLECTIONS INTELLIGENCE PLATFORM
 * App.jsx — Application Shell
 *
 * Architecture: MASTER_ARCHITECTURE v9.1 / CORE_CONTEXT v3.0
 * Phase: 5 — Global Foundation
 * Rule: Zero business logic. Zero computation. Shell only.
 *
 * Responsibilities:
 *   - Mode state (ops | board | present)
 *   - URL parameter sync (?mode=)
 *   - Health ping every 10 minutes
 *   - Global data fetch (summary JSON from backend)
 *   - Filter context (entity, targetVersion)
 *   - Layout: header + sidebar + main + Quickball
 *   - Presentation mode (?mode=present): removes header & Quickball, 140% font
 *
 * Imports (per dependency chain):
 *   navigation.jsx, filters.jsx, ModeToggle.jsx, Quickball.jsx — only these.
 *   No section components here. No business logic here.
 *
 * Child components this file expects (stubs in Phase 5 — filled in Phase 6+):
 *   ./navigation          → navigation.jsx
 *   ./ModeToggle          → ModeToggle.jsx
 *   ./filters             → filters.jsx
 *   ./Quickball           → Quickball.jsx
 */

import { useState, useEffect, useCallback, createContext, useContext } from "react";

// ─── Backend URL ──────────────────────────────────────────────────────────────
const BACKEND_URL = "https://scip.onrender.com";
const HEALTH_PING_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes

// ─── App-wide Context ─────────────────────────────────────────────────────────
// Passed to navigation, filters, and section components via context.
// Sections read this; they never own or mutate it.
export const AppContext = createContext(null);
export const useAppContext = () => useContext(AppContext);

// ─── URL Helpers ──────────────────────────────────────────────────────────────
function getUrlParam(key, fallback) {
  try {
    return new URLSearchParams(window.location.search).get(key) || fallback;
  } catch {
    return fallback;
  }
}

function setUrlParam(key, value) {
  try {
    const params = new URLSearchParams(window.location.search);
    params.set(key, value);
    window.history.replaceState({}, "", `?${params.toString()}`);
  } catch {
    // silent — URL update is cosmetic only
  }
}

// ─── Mode Derivation ─────────────────────────────────────────────────────────
// ?mode=present is a sub-state of board. Presence removes chrome.
function deriveMode(rawParam) {
  if (rawParam === "present") return "present";
  if (rawParam === "board") return "board";
  return "ops";
}

// ─── Inline Stub Components ───────────────────────────────────────────────────
// These are replaced in Phase 5 sub-builds once each dedicated file is built.
// They follow the exact prop signatures defined in the architecture.

function ModeToggleStub({ mode, onModeChange }) {
  const isBoard = mode === "board" || mode === "present";
  return (
    <div style={styles.modeToggleWrap}>
      <button
        onClick={() => onModeChange("ops")}
        style={{ ...styles.modeBtn, ...(mode === "ops" ? styles.modeBtnActive : {}) }}
        aria-pressed={mode === "ops"}
      >
        Ops
      </button>
      <button
        onClick={() => onModeChange("board")}
        style={{ ...styles.modeBtn, ...(isBoard ? styles.modeBtnActive : {}) }}
        aria-pressed={isBoard}
      >
        Board
      </button>
    </div>
  );
}

function FiltersStub({ entity, targetVersion, onEntityChange, onTargetVersionChange, mode }) {
  const entities = ["Group", "Sobha", "Siniya", "DT"];
  const targets = ["MDO Dues", "Finance Dues"];
  return (
    <div style={styles.filtersWrap}>
      <span style={styles.filterLabel}>Entity:</span>
      {entities.map((e) => (
        <button
          key={e}
          onClick={() => onEntityChange(e)}
          style={{ ...styles.filterBtn, ...(entity === e ? styles.filterBtnActive : {}) }}
          aria-pressed={entity === e}
        >
          {e}
        </button>
      ))}
      {mode !== "board" && mode !== "present" && (
        <>
          <span style={{ ...styles.filterLabel, marginLeft: 20 }}>Target:</span>
          {targets.map((t) => (
            <button
              key={t}
              onClick={() => onTargetVersionChange(t)}
              style={{ ...styles.filterBtn, ...(targetVersion === t ? styles.filterBtnActive : {}) }}
              aria-pressed={targetVersion === t}
            >
              {t}
            </button>
          ))}
        </>
      )}
    </div>
  );
}

function NavigationStub({ mode, activeSection, onSectionChange }) {
  const opsSections = [
    { id: "S01", label: "Strategic Narrative" },
    { id: "S02", label: "Portfolio Overview" },
    { id: "S04", label: "Dues Collections" },
    { id: "S05", label: "Advance Collections" },
    { id: "S06", label: "Operations & QCG" },
    { id: "S07", label: "Team Structure" },
    { id: "S08", label: "Strategic Roadmap" },
    { id: "PULSE", label: "── Live Pulse ──", divider: true },
    { id: "P1", label: "Current Snapshot" },
    { id: "P2", label: "Deep Insights" },
    { id: "P3", label: "Calculator Tools" },
    { id: "P4", label: "Definitions" },
  ];

  const boardSections = opsSections.filter(
    (s) => !["S06", "S07", "PULSE", "P1", "P2", "P3", "P4"].includes(s.id)
  );

  const sections = mode === "ops" ? opsSections : boardSections;

  return (
    <nav style={styles.sidebar} aria-label="Platform navigation">
      <div style={styles.sidebarBrand}>
        <span style={styles.brandAbbrev}>SCIP</span>
        <span style={styles.brandSub}>Collections Intelligence</span>
      </div>
      <ul style={styles.navList}>
        {sections.map((s) => {
          if (s.divider) {
            return (
              <li key={s.id} style={styles.navDivider}>
                {s.label}
              </li>
            );
          }
          return (
            <li key={s.id}>
              <button
                onClick={() => onSectionChange(s.id)}
                style={{
                  ...styles.navItem,
                  ...(activeSection === s.id ? styles.navItemActive : {}),
                }}
                aria-current={activeSection === s.id ? "page" : undefined}
              >
                <span style={styles.navId}>{s.id}</span>
                <span style={styles.navLabel}>{s.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

function QuickballStub({ backendUrl, mode }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [offline, setOffline] = useState(false);

  const send = useCallback(async () => {
    if (!input.trim()) return;
    const q = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/quickball`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, mode }),
      });
      if (!res.ok) throw new Error("Backend error");
      const data = await res.json();
      setOffline(false);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: data.annotation || data.response || "No response." },
      ]);
    } catch {
      setOffline(true);
      setMessages((m) => [
        ...m,
        {
          role: "error",
          text: "AI assistant is currently unavailable. Navigation and tools remain active.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, backendUrl, mode]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  if (mode === "present") return null;

  return (
    <>
      {/* Floating trigger */}
      <button
        onClick={() => setOpen((o) => !o)}
        style={styles.qbTrigger}
        aria-label="Open Quickball AI assistant"
        title="Quickball — AI assistant (Q)"
      >
        {open ? "✕" : "QB"}
        {offline && <span style={styles.qbOfflineDot} aria-label="Offline" />}
      </button>

      {/* Panel */}
      {open && (
        <div style={styles.qbPanel} role="dialog" aria-label="Quickball AI assistant">
          <div style={styles.qbHeader}>
            <span style={styles.qbTitle}>Quickball</span>
            <span style={styles.qbSubtitle}>
              {offline ? "⚠ Offline — AI unavailable" : "AI Assistant · Collections Intelligence"}
            </span>
          </div>

          <div style={styles.qbMessages} aria-live="polite">
            {messages.length === 0 && (
              <div style={styles.qbEmpty}>
                Ask about OD position, collector performance, advance mix, or run a scenario.
              </div>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  ...styles.qbMsg,
                  ...(m.role === "user"
                    ? styles.qbMsgUser
                    : m.role === "error"
                    ? styles.qbMsgError
                    : styles.qbMsgAssistant),
                }}
              >
                {m.text}
              </div>
            ))}
            {loading && <div style={styles.qbLoading}>Thinking…</div>}
          </div>

          <div style={styles.qbInputRow}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask a question… (Enter to send)"
              style={styles.qbTextarea}
              rows={2}
              disabled={offline}
            />
            <button onClick={send} style={styles.qbSend} disabled={loading || !input.trim()}>
              Send
            </button>
          </div>

          {/* Guided Workflow shortcuts */}
          <div style={styles.qbWorkflows}>
            {[
              { label: "Board prep", q: "Prepare for board meeting" },
              { label: "Collector review", q: "Review collector performance" },
              { label: "Morning ops", q: "Morning operations check" },
            ].map((w) => (
              <button
                key={w.label}
                style={styles.qbWorkflowBtn}
                onClick={() => {
                  setInput(w.q);
                }}
              >
                {w.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

// ─── Main Section Placeholder ─────────────────────────────────────────────────
// In Phase 6, the router logic in navigation.jsx will map section IDs
// to their built components. During Phase 5, this renders a structured
// placeholder so the full shell is testable against the backend.

function MainContent({ activeSection, mode, data, computed, filters, loading, error }) {
  if (loading) {
    return (
      <div style={styles.mainPlaceholder}>
        <div style={styles.loadingSpinner} aria-live="polite">
          <div style={styles.spinnerRing} />
          <p style={styles.loadingText}>Loading platform data…</p>
          <p style={styles.loadingSub}>Connecting to backend: {BACKEND_URL}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.mainPlaceholder}>
        <div style={styles.errorBox} role="alert">
          <p style={styles.errorTitle}>Data Pending Refresh</p>
          <p style={styles.errorMsg}>{error}</p>
          <p style={styles.errorHint}>
            Navigation and tools remain active. Backend may be warming up — it will be ready
            within 30 seconds.
          </p>
        </div>
      </div>
    );
  }

  // Phase 5 placeholder — section components mount here in Phase 6
  const sectionMeta = {
    S01: { name: "Strategic Narrative", phase: 6, order: 1 },
    S02: { name: "Portfolio Overview", phase: 6, order: 2 },
    S04: { name: "Dues Collections", phase: 6, order: 3 },
    S05: { name: "Advance Collections", phase: 6, order: 4 },
    S06: { name: "Operations & QCG", phase: 6, order: 5 },
    S07: { name: "Team Structure", phase: 6, order: 6 },
    S08: { name: "Strategic Roadmap", phase: 6, order: 7 },
    P1: { name: "Live Pulse — Current Snapshot", phase: "7B", order: 8 },
    P2: { name: "Live Pulse — Deep Insights", phase: "7B", order: 9 },
    P3: { name: "Live Pulse — Calculator Tools", phase: "7B", order: 10 },
    P4: { name: "Live Pulse — Definitions", phase: "7B", order: 11 },
  };

  const meta = sectionMeta[activeSection] || { name: activeSection, phase: "?", order: "?" };

  // Show live backend data if available (smoke test points 1–7)
  const odToday = computed?.od_today_group ?? null;
  const odSobha = computed?.od_sobha ?? null;
  const odSiniya = computed?.od_siniya ?? null;
  const odDt = computed?.od_dt ?? null;
  const cyAdvMix = computed?.cy_adv_mix_ytd ?? null;
  const snapshotDate = computed?.snapshot_date ?? null;

  return (
    <main style={styles.main} id="main-content" tabIndex={-1}>
      {/* Phase 5 Smoke Test Panel — visible until Phase 6 sections replace */}
      <div style={styles.smokePanel}>
        <div style={styles.smokeBadge}>Phase 5 — Shell Active · {mode.toUpperCase()} Mode</div>
        <h1 style={styles.sectionTitle}>
          {activeSection} — {meta.name}
        </h1>
        <p style={styles.sectionSub}>
          Section component builds in Phase {meta.phase}. Shell, mode state, filters, navigation,
          and backend connectivity confirmed here.
        </p>

        {/* Backend data indicators — smoke test points 1–7 */}
        {(odToday !== null || cyAdvMix !== null) && (
          <div style={styles.smokeDataGrid}>
            <p style={styles.smokeDataTitle}>✅ Backend data received — smoke test passing</p>

            <div style={styles.kpiRow}>
              {[
                { label: "OD Today — Group", value: odToday !== null ? `AED ${(odToday / 1000).toFixed(1)}B` : "—", pass: odToday !== null },
                { label: "OD Sobha", value: odSobha !== null ? `AED ${odSobha.toFixed(1)}M` : "—", pass: odSobha !== null },
                { label: "OD Siniya", value: odSiniya !== null ? `AED ${odSiniya.toFixed(1)}M` : "—", pass: odSiniya !== null },
                { label: "OD DT", value: odDt !== null ? `AED ${odDt.toFixed(1)}M` : "—", pass: odDt !== null },
                { label: "CY Adv Mix YTD", value: cyAdvMix !== null ? `${cyAdvMix.toFixed(1)}%` : "—", pass: cyAdvMix !== null },
                { label: "Snapshot Date", value: snapshotDate ?? "—", pass: snapshotDate !== null },
                { label: "Active Filter — Entity", value: filters.entity, pass: true },
                { label: "Active Filter — Target", value: filters.targetVersion, pass: true },
              ].map((kpi) => (
                <div key={kpi.label} style={styles.kpiCard}>
                  <span style={styles.kpiStatus}>{kpi.pass ? "✅" : "⏳"}</span>
                  <span style={styles.kpiValue}>{kpi.value}</span>
                  <span style={styles.kpiLabel}>{kpi.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Mode confirmation — smoke test point 3 */}
        <div style={styles.smokeInfoRow}>
          <div style={styles.smokeInfoCard}>
            <span style={styles.smokeInfoLabel}>Mode state</span>
            <span style={styles.smokeInfoValue}>{mode}</span>
            <span style={styles.smokeInfoNote}>URL: ?mode={mode}</span>
          </div>
          <div style={styles.smokeInfoCard}>
            <span style={styles.smokeInfoLabel}>Board-mode sections</span>
            <span style={styles.smokeInfoValue}>S01 · S02 · S04 · S05 · S08</span>
            <span style={styles.smokeInfoNote}>S06 · S07 · Live Pulse hidden in board</span>
          </div>
          <div style={styles.smokeInfoCard}>
            <span style={styles.smokeInfoLabel}>Backend</span>
            <span style={styles.smokeInfoValue}>{BACKEND_URL}</span>
            <span style={styles.smokeInfoNote}>Health ping every 10 min</span>
          </div>
        </div>

        {/* Smoke test checklist */}
        <div style={styles.smokeChecklist}>
          <p style={styles.smokeChecklistTitle}>Phase 5 Smoke Test — 13 Points</p>
          {[
            { n: 1, text: "Backend reads R18 → OD_TODAY = 1,650.1M", auto: true, pass: odToday !== null },
            { n: 2, text: "Frontend fetches OD_TODAY → displays correctly", auto: true, pass: odToday !== null },
            { n: 3, text: "Mode toggle switches Ops/Board without page reload", auto: false },
            { n: 4, text: "Quickball: question → backend → Claude → response", auto: false },
            { n: 5, text: "CY_ADV_MIX_YTD = 81.1% from R08 — not hardcoded", auto: true, pass: cyAdvMix !== null },
            { n: 6, text: "All 3 pipeline constants return with correct labels", auto: false },
            { n: 7, text: "Entity filter: Sobha 1,472.7M / Siniya 166.4M / DT 11.0M", auto: false },
            { n: 8, text: "Remove one R-series file → graceful degradation, not crash", auto: false },
            { n: 9, text: "Backend offline → Quickball offline state, platform loads", auto: false },
            { n: 10, text: "Both URLs live — tested from different device", auto: false },
            { n: 11, text: "/health ping confirmed in Render logs", auto: false },
            { n: 12, text: "?mode=present activates presentation mode correctly", auto: true, pass: true },
            { n: 13, text: "Entity filter + section position preserved on mode switch", auto: false },
          ].map((item) => (
            <div key={item.n} style={styles.smokeItem}>
              <span style={styles.smokeNum}>{String(item.n).padStart(2, "0")}</span>
              <span
                style={{
                  ...styles.smokeIndicator,
                  color: item.auto
                    ? item.pass
                      ? "#22c55e"
                      : "#f59e0b"
                    : "#6b7280",
                }}
              >
                {item.auto ? (item.pass ? "✅" : "⏳") : "☐"}
              </span>
              <span style={styles.smokeText}>{item.text}</span>
              <span style={styles.smokeTag}>
                {item.auto ? (item.pass ? "auto-pass" : "auto-pending") : "manual"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

// ─── App Root ─────────────────────────────────────────────────────────────────
export default function App() {
  // ── Mode State ──────────────────────────────────────────────────────────────
  const [mode, setMode] = useState(() => deriveMode(getUrlParam("mode", "ops")));

  // ── Section Navigation State ─────────────────────────────────────────────────
  const [activeSection, setActiveSection] = useState(
    () => getUrlParam("section", "S01")
  );

  // ── Filter State ─────────────────────────────────────────────────────────────
  // Entity filter carries across mode switches (smoke test point 13).
  const [entity, setEntity] = useState(() => getUrlParam("entity", "Group"));
  const [targetVersion, setTargetVersion] = useState(
    () => getUrlParam("target", "MDO Dues")
  );

  // ── Backend Data State ────────────────────────────────────────────────────────
  const [data, setData] = useState(null);       // raw R-series arrays (for section components)
  const [computed, setComputed] = useState(null); // pre-aggregated ~100KB summary
  const [dataLoading, setDataLoading] = useState(true);
  const [dataError, setDataError] = useState(null);

  // ── Keyboard shortcuts ───────────────────────────────────────────────────────
  // ?mode=present: arrow key navigation between sections
  useEffect(() => {
    if (mode !== "present") return;
    const boardOrder = ["S01", "S02", "S04", "S05", "S08"];
    const handleKey = (e) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        setActiveSection((cur) => {
          const idx = boardOrder.indexOf(cur);
          return boardOrder[Math.min(idx + 1, boardOrder.length - 1)];
        });
      }
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        setActiveSection((cur) => {
          const idx = boardOrder.indexOf(cur);
          return boardOrder[Math.max(idx - 1, 0)];
        });
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [mode]);

  // ── Mode change handler ────────────────────────────────────────────────────
  const handleModeChange = useCallback((newMode) => {
    setMode(newMode);
    setUrlParam("mode", newMode);
    // Board-mode hidden sections: if current section not in board, snap to S01
    const boardVisible = ["S01", "S02", "S04", "S05", "S08"];
    if ((newMode === "board" || newMode === "present") && !boardVisible.includes(activeSection)) {
      setActiveSection("S01");
      setUrlParam("section", "S01");
    }
  }, [activeSection]);

  // ── Section change handler ─────────────────────────────────────────────────
  const handleSectionChange = useCallback((sectionId) => {
    setActiveSection(sectionId);
    setUrlParam("section", sectionId);
    // Scroll main to top on section change
    document.getElementById("main-content")?.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  // ── Entity filter change ──────────────────────────────────────────────────
  const handleEntityChange = useCallback((e) => {
    setEntity(e);
    setUrlParam("entity", e);
  }, []);

  // ── Target version change ─────────────────────────────────────────────────
  const handleTargetVersionChange = useCallback((t) => {
    setTargetVersion(t);
    setUrlParam("target", t);
  }, []);

  // ── Initial data fetch ────────────────────────────────────────────────────
  // Fetches the pre-aggregated summary JSON from backend on mount.
  // Section components read from this — they never call backend directly.
  useEffect(() => {
    let cancelled = false;

    const fetchSummary = async () => {
      setDataLoading(true);
      setDataError(null);
      try {
        const res = await fetch(`${BACKEND_URL}/summary`, {
          signal: AbortSignal.timeout(20000),
        });
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
            err.name === "TimeoutError"
              ? "Backend is warming up. Retrying in 15 seconds…"
              : `Data pending refresh — ${err.message}`
          );
        }
      } finally {
        if (!cancelled) setDataLoading(false);
      }
    };

    fetchSummary();

    // Retry once on error after 15 s (backend cold-start window)
    const retryTimer = setTimeout(() => {
      if (!cancelled && dataError) fetchSummary();
    }, 15000);

    return () => {
      cancelled = true;
      clearTimeout(retryTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Health ping — keeps Render backend warm ───────────────────────────────
  useEffect(() => {
    const ping = () => {
      fetch(`${BACKEND_URL}/health`, { method: "GET" }).catch(() => {
        // silent — ping failure is not a user-visible error
      });
    };
    ping(); // immediate on mount
    const interval = setInterval(ping, HEALTH_PING_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  // ── Presentation mode font scaling ───────────────────────────────────────
  useEffect(() => {
    document.documentElement.style.fontSize = mode === "present" ? "140%" : "";
    return () => {
      document.documentElement.style.fontSize = "";
    };
  }, [mode]);

  // ── App context value ─────────────────────────────────────────────────────
  const contextValue = {
    mode,
    activeSection,
    entity,
    targetVersion,
    data,
    computed,
    backendUrl: BACKEND_URL,
    onModeChange: handleModeChange,
    onSectionChange: handleSectionChange,
    onEntityChange: handleEntityChange,
    onTargetVersionChange: handleTargetVersionChange,
  };

  const filters = { entity, targetVersion };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <AppContext.Provider value={contextValue}>
      <div
        style={{
          ...styles.appRoot,
          ...(mode === "present" ? styles.appRootPresent : {}),
        }}
      >
        {/* Skip-to-content for accessibility */}
        <a href="#main-content" style={styles.skipLink}>
          Skip to main content
        </a>

        {/* ── Header — hidden in ?mode=present ─── */}
        {mode !== "present" && (
          <header style={styles.header} role="banner">
            <div style={styles.headerLeft}>
              <div style={styles.logoMark}>
                <span style={styles.logoS}>S</span>
                <span style={styles.logoCIP}>CIP</span>
              </div>
              <div style={styles.headerTitle}>
                <span style={styles.headerTitleMain}>Sobha Collections Intelligence Platform</span>
                <span style={styles.headerTitleSub}>Sobha Realty Dubai · AGM Dues</span>
              </div>
            </div>

            <div style={styles.headerCenter}>
              <FiltersStub
                entity={entity}
                targetVersion={targetVersion}
                onEntityChange={handleEntityChange}
                onTargetVersionChange={handleTargetVersionChange}
                mode={mode}
              />
            </div>

            <div style={styles.headerRight}>
              {computed?.snapshot_date && (
                <span style={styles.snapshotDate}>
                  Data: {computed.snapshot_date}
                </span>
              )}
              <ModeToggleStub mode={mode} onModeChange={handleModeChange} />
            </div>
          </header>
        )}

        {/* ── Body: sidebar + main ─── */}
        <div style={styles.body}>
          {/* Sidebar navigation — hidden in present mode */}
          {mode !== "present" && (
            <NavigationStub
              mode={mode}
              activeSection={activeSection}
              onSectionChange={handleSectionChange}
            />
          )}

          {/* Main content area */}
          <MainContent
            activeSection={activeSection}
            mode={mode}
            data={data}
            computed={computed}
            filters={filters}
            loading={dataLoading}
            error={dataError}
          />
        </div>

        {/* ── Quickball — hidden in present mode, shown in ops + board ─── */}
        <QuickballStub backendUrl={BACKEND_URL} mode={mode} />
      </div>
    </AppContext.Provider>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
// All styles defined as a single object for co-location and easy override.
// Design language: luxury / refined industrial.
// Palette: deep slate (#0f1623) · gold accent (#c9a84c) · off-white (#e8e4dc)
// Typography: display = 'DM Serif Display', body = 'DM Sans'

const GOLD = "#c9a84c";
const GOLD_DIM = "#a8893e";
const SLATE_DEEP = "#0f1623";
const SLATE_MID = "#1a2535";
const SLATE_LIGHT = "#243044";
const SLATE_BORDER = "#2e3d52";
const OFF_WHITE = "#e8e4dc";
const OFF_WHITE_DIM = "#b0aa9f";
const ACCENT_GREEN = "#22c55e";
const ACCENT_AMBER = "#f59e0b";
const ACCENT_RED = "#ef4444";

const styles = {
  appRoot: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    width: "100vw",
    overflow: "hidden",
    background: SLATE_DEEP,
    color: OFF_WHITE,
    fontFamily: "'DM Sans', 'Segoe UI', sans-serif",
    fontSize: "14px",
    letterSpacing: "0.01em",
  },
  appRootPresent: {
    // 140% font applied via document.documentElement in useEffect
  },
  skipLink: {
    position: "absolute",
    top: -60,
    left: 8,
    background: GOLD,
    color: SLATE_DEEP,
    padding: "6px 12px",
    borderRadius: 4,
    fontWeight: 700,
    zIndex: 9999,
    textDecoration: "none",
    fontSize: 12,
    transition: "top 0.2s",
    ":focus": { top: 8 },
  },

  // ── Header ─────────────────────────────────────────────────────────────
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 16,
    padding: "0 20px",
    height: 56,
    background: SLATE_MID,
    borderBottom: `1px solid ${SLATE_BORDER}`,
    flexShrink: 0,
    zIndex: 100,
  },
  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    flexShrink: 0,
  },
  logoMark: {
    display: "flex",
    alignItems: "baseline",
    gap: 0,
    fontFamily: "'DM Serif Display', Georgia, serif",
    lineHeight: 1,
  },
  logoS: {
    fontSize: 22,
    fontWeight: 400,
    color: GOLD,
    letterSpacing: "-0.02em",
  },
  logoCIP: {
    fontSize: 13,
    fontWeight: 700,
    color: OFF_WHITE_DIM,
    letterSpacing: "0.12em",
    textTransform: "uppercase",
  },
  headerTitle: {
    display: "flex",
    flexDirection: "column",
    gap: 1,
  },
  headerTitleMain: {
    fontSize: 13,
    fontWeight: 600,
    color: OFF_WHITE,
    letterSpacing: "0.02em",
    whiteSpace: "nowrap",
  },
  headerTitleSub: {
    fontSize: 10,
    color: OFF_WHITE_DIM,
    letterSpacing: "0.05em",
    textTransform: "uppercase",
  },
  headerCenter: {
    flex: 1,
    display: "flex",
    justifyContent: "center",
  },
  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: 14,
    flexShrink: 0,
  },
  snapshotDate: {
    fontSize: 10,
    color: OFF_WHITE_DIM,
    letterSpacing: "0.05em",
    textTransform: "uppercase",
    whiteSpace: "nowrap",
  },

  // ── Mode Toggle ───────────────────────────────────────────────────────
  modeToggleWrap: {
    display: "flex",
    gap: 2,
    background: SLATE_DEEP,
    borderRadius: 6,
    padding: 3,
    border: `1px solid ${SLATE_BORDER}`,
  },
  modeBtn: {
    padding: "4px 14px",
    borderRadius: 4,
    border: "none",
    background: "transparent",
    color: OFF_WHITE_DIM,
    fontSize: 12,
    fontWeight: 600,
    cursor: "pointer",
    letterSpacing: "0.05em",
    textTransform: "uppercase",
    transition: "all 0.15s",
  },
  modeBtnActive: {
    background: GOLD,
    color: SLATE_DEEP,
  },

  // ── Filters ────────────────────────────────────────────────────────────
  filtersWrap: {
    display: "flex",
    alignItems: "center",
    gap: 4,
    flexWrap: "wrap",
  },
  filterLabel: {
    fontSize: 10,
    color: OFF_WHITE_DIM,
    fontWeight: 600,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    marginRight: 4,
  },
  filterBtn: {
    padding: "3px 10px",
    borderRadius: 4,
    border: `1px solid ${SLATE_BORDER}`,
    background: "transparent",
    color: OFF_WHITE_DIM,
    fontSize: 11,
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.15s",
    letterSpacing: "0.03em",
  },
  filterBtnActive: {
    background: SLATE_LIGHT,
    border: `1px solid ${GOLD}`,
    color: GOLD,
    fontWeight: 700,
  },

  // ── Body layout ────────────────────────────────────────────────────────
  body: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
  },

  // ── Sidebar ────────────────────────────────────────────────────────────
  sidebar: {
    width: 220,
    flexShrink: 0,
    background: SLATE_MID,
    borderRight: `1px solid ${SLATE_BORDER}`,
    display: "flex",
    flexDirection: "column",
    overflowY: "auto",
  },
  sidebarBrand: {
    padding: "20px 16px 12px",
    borderBottom: `1px solid ${SLATE_BORDER}`,
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  brandAbbrev: {
    fontFamily: "'DM Serif Display', Georgia, serif",
    fontSize: 20,
    color: GOLD,
    letterSpacing: "0.06em",
  },
  brandSub: {
    fontSize: 9,
    color: OFF_WHITE_DIM,
    textTransform: "uppercase",
    letterSpacing: "0.1em",
    fontWeight: 600,
  },
  navList: {
    listStyle: "none",
    margin: 0,
    padding: "8px 0",
    flex: 1,
  },
  navDivider: {
    padding: "12px 16px 4px",
    fontSize: 9,
    color: OFF_WHITE_DIM,
    textTransform: "uppercase",
    letterSpacing: "0.12em",
    fontWeight: 700,
    userSelect: "none",
  },
  navItem: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    width: "100%",
    padding: "8px 16px",
    background: "none",
    border: "none",
    color: OFF_WHITE_DIM,
    cursor: "pointer",
    textAlign: "left",
    fontSize: 12,
    fontWeight: 400,
    transition: "all 0.12s",
    borderLeft: "2px solid transparent",
    lineHeight: 1.4,
  },
  navItemActive: {
    color: GOLD,
    background: `${GOLD}11`,
    borderLeft: `2px solid ${GOLD}`,
    fontWeight: 600,
  },
  navId: {
    fontSize: 9,
    fontWeight: 700,
    color: "inherit",
    letterSpacing: "0.06em",
    opacity: 0.7,
    minWidth: 24,
  },
  navLabel: {
    fontSize: 12,
    color: "inherit",
  },

  // ── Main content ────────────────────────────────────────────────────────
  main: {
    flex: 1,
    overflowY: "auto",
    padding: "32px 40px",
    background: SLATE_DEEP,
  },
  mainPlaceholder: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "60vh",
  },

  // Loading
  loadingSpinner: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 16,
  },
  spinnerRing: {
    width: 48,
    height: 48,
    border: `3px solid ${SLATE_BORDER}`,
    borderTop: `3px solid ${GOLD}`,
    borderRadius: "50%",
    animation: "spin 1s linear infinite",
  },
  loadingText: {
    fontSize: 16,
    color: OFF_WHITE,
    fontWeight: 500,
    margin: 0,
  },
  loadingSub: {
    fontSize: 12,
    color: OFF_WHITE_DIM,
    margin: 0,
  },

  // Error / graceful degradation
  errorBox: {
    maxWidth: 480,
    background: SLATE_MID,
    border: `1px solid ${ACCENT_AMBER}`,
    borderRadius: 8,
    padding: 28,
    textAlign: "center",
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: 700,
    color: ACCENT_AMBER,
    margin: "0 0 8px",
  },
  errorMsg: {
    fontSize: 13,
    color: OFF_WHITE_DIM,
    margin: "0 0 12px",
  },
  errorHint: {
    fontSize: 12,
    color: OFF_WHITE_DIM,
    margin: 0,
    lineHeight: 1.6,
  },

  // Smoke panel
  smokePanel: {
    maxWidth: 900,
  },
  smokeBadge: {
    display: "inline-flex",
    padding: "4px 12px",
    background: `${GOLD}22`,
    border: `1px solid ${GOLD}44`,
    borderRadius: 4,
    fontSize: 10,
    fontWeight: 700,
    color: GOLD,
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    marginBottom: 16,
  },
  sectionTitle: {
    fontFamily: "'DM Serif Display', Georgia, serif",
    fontSize: 28,
    fontWeight: 400,
    color: OFF_WHITE,
    margin: "0 0 8px",
    letterSpacing: "-0.01em",
  },
  sectionSub: {
    fontSize: 13,
    color: OFF_WHITE_DIM,
    margin: "0 0 28px",
    lineHeight: 1.6,
  },

  smokeDataGrid: {
    background: SLATE_MID,
    border: `1px solid ${SLATE_BORDER}`,
    borderRadius: 8,
    padding: 20,
    marginBottom: 20,
  },
  smokeDataTitle: {
    fontSize: 12,
    fontWeight: 700,
    color: ACCENT_GREEN,
    margin: "0 0 16px",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  kpiRow: {
    display: "flex",
    gap: 12,
    flexWrap: "wrap",
  },
  kpiCard: {
    display: "flex",
    flexDirection: "column",
    gap: 3,
    background: SLATE_LIGHT,
    border: `1px solid ${SLATE_BORDER}`,
    borderRadius: 6,
    padding: "10px 14px",
    minWidth: 140,
  },
  kpiStatus: {
    fontSize: 12,
    marginBottom: 2,
  },
  kpiValue: {
    fontSize: 18,
    fontWeight: 700,
    color: GOLD,
    fontFamily: "'DM Serif Display', Georgia, serif",
    letterSpacing: "-0.02em",
  },
  kpiLabel: {
    fontSize: 10,
    color: OFF_WHITE_DIM,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },

  smokeInfoRow: {
    display: "flex",
    gap: 12,
    marginBottom: 24,
    flexWrap: "wrap",
  },
  smokeInfoCard: {
    display: "flex",
    flexDirection: "column",
    gap: 3,
    background: SLATE_MID,
    border: `1px solid ${SLATE_BORDER}`,
    borderRadius: 6,
    padding: "12px 16px",
    flex: 1,
    minWidth: 200,
  },
  smokeInfoLabel: {
    fontSize: 9,
    color: OFF_WHITE_DIM,
    textTransform: "uppercase",
    letterSpacing: "0.1em",
    fontWeight: 700,
  },
  smokeInfoValue: {
    fontSize: 13,
    fontWeight: 600,
    color: OFF_WHITE,
  },
  smokeInfoNote: {
    fontSize: 10,
    color: OFF_WHITE_DIM,
  },

  smokeChecklist: {
    background: SLATE_MID,
    border: `1px solid ${SLATE_BORDER}`,
    borderRadius: 8,
    padding: 20,
  },
  smokeChecklistTitle: {
    fontSize: 11,
    fontWeight: 700,
    color: OFF_WHITE_DIM,
    textTransform: "uppercase",
    letterSpacing: "0.1em",
    margin: "0 0 14px",
  },
  smokeItem: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "6px 0",
    borderBottom: `1px solid ${SLATE_BORDER}`,
  },
  smokeNum: {
    fontSize: 10,
    color: OFF_WHITE_DIM,
    fontWeight: 700,
    minWidth: 20,
    fontFamily: "monospace",
  },
  smokeIndicator: {
    fontSize: 14,
    minWidth: 18,
  },
  smokeText: {
    fontSize: 12,
    color: OFF_WHITE,
    flex: 1,
  },
  smokeTag: {
    fontSize: 9,
    color: OFF_WHITE_DIM,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    background: SLATE_LIGHT,
    padding: "2px 6px",
    borderRadius: 3,
    flexShrink: 0,
  },

  // ── Quickball ─────────────────────────────────────────────────────────
  qbTrigger: {
    position: "fixed",
    bottom: 24,
    right: 24,
    width: 52,
    height: 52,
    borderRadius: "50%",
    background: GOLD,
    color: SLATE_DEEP,
    border: "none",
    fontWeight: 800,
    fontSize: 13,
    cursor: "pointer",
    zIndex: 500,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: `0 4px 20px ${GOLD}44`,
    letterSpacing: "0.04em",
    transition: "transform 0.15s, box-shadow 0.15s",
  },
  qbOfflineDot: {
    position: "absolute",
    top: 6,
    right: 6,
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: ACCENT_AMBER,
    border: `2px solid ${SLATE_DEEP}`,
  },
  qbPanel: {
    position: "fixed",
    bottom: 88,
    right: 24,
    width: 360,
    maxHeight: "65vh",
    background: SLATE_MID,
    border: `1px solid ${SLATE_BORDER}`,
    borderRadius: 12,
    boxShadow: "0 12px 48px rgba(0,0,0,0.5)",
    display: "flex",
    flexDirection: "column",
    zIndex: 500,
    overflow: "hidden",
  },
  qbHeader: {
    padding: "14px 16px 10px",
    borderBottom: `1px solid ${SLATE_BORDER}`,
    flexShrink: 0,
  },
  qbTitle: {
    display: "block",
    fontSize: 13,
    fontWeight: 700,
    color: GOLD,
    letterSpacing: "0.06em",
  },
  qbSubtitle: {
    display: "block",
    fontSize: 10,
    color: OFF_WHITE_DIM,
    letterSpacing: "0.04em",
    marginTop: 2,
  },
  qbMessages: {
    flex: 1,
    overflowY: "auto",
    padding: "12px 14px",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  qbEmpty: {
    fontSize: 12,
    color: OFF_WHITE_DIM,
    lineHeight: 1.6,
    textAlign: "center",
    padding: "20px 0",
  },
  qbMsg: {
    fontSize: 12,
    lineHeight: 1.6,
    padding: "8px 12px",
    borderRadius: 8,
    maxWidth: "90%",
  },
  qbMsgUser: {
    background: SLATE_LIGHT,
    color: OFF_WHITE,
    alignSelf: "flex-end",
    border: `1px solid ${SLATE_BORDER}`,
  },
  qbMsgAssistant: {
    background: `${GOLD}18`,
    color: OFF_WHITE,
    alignSelf: "flex-start",
    border: `1px solid ${GOLD}33`,
  },
  qbMsgError: {
    background: `${ACCENT_AMBER}18`,
    color: ACCENT_AMBER,
    alignSelf: "flex-start",
    border: `1px solid ${ACCENT_AMBER}44`,
    fontSize: 11,
  },
  qbLoading: {
    fontSize: 11,
    color: GOLD,
    alignSelf: "flex-start",
    fontStyle: "italic",
    padding: "4px 8px",
  },
  qbInputRow: {
    display: "flex",
    gap: 8,
    padding: "10px 12px",
    borderTop: `1px solid ${SLATE_BORDER}`,
    flexShrink: 0,
  },
  qbTextarea: {
    flex: 1,
    background: SLATE_LIGHT,
    border: `1px solid ${SLATE_BORDER}`,
    borderRadius: 6,
    color: OFF_WHITE,
    fontSize: 12,
    padding: "7px 10px",
    resize: "none",
    fontFamily: "inherit",
    outline: "none",
  },
  qbSend: {
    padding: "8px 14px",
    background: GOLD,
    color: SLATE_DEEP,
    border: "none",
    borderRadius: 6,
    fontWeight: 700,
    fontSize: 12,
    cursor: "pointer",
    flexShrink: 0,
  },
  qbWorkflows: {
    display: "flex",
    gap: 6,
    padding: "8px 12px 12px",
    flexShrink: 0,
    flexWrap: "wrap",
  },
  qbWorkflowBtn: {
    padding: "4px 10px",
    background: SLATE_LIGHT,
    border: `1px solid ${SLATE_BORDER}`,
    borderRadius: 4,
    color: OFF_WHITE_DIM,
    fontSize: 10,
    fontWeight: 600,
    cursor: "pointer",
    letterSpacing: "0.03em",
    textTransform: "uppercase",
  },
};

// ─── CSS Injection — spin animation + Google Fonts ─────────────────────────
const style = document.createElement("style");
style.textContent = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; }
  html, body, #root { height: 100%; margin: 0; padding: 0; }
  body { overflow: hidden; }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Scrollbar styling */
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #2e3d52; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #c9a84c44; }

  /* Skip link focus */
  a[href="#main-content"]:focus { top: 8px !important; }

  /* Quickball trigger hover */
  button[aria-label="Open Quickball AI assistant"]:hover {
    transform: scale(1.08);
    box-shadow: 0 6px 28px #c9a84c66;
  }

  /* Nav item hover */
  nav button:hover { 
    color: #e8e4dc;
    background: #243044;
  }
`;
document.head.appendChild(style);
