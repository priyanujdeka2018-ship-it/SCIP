/**
 * SCIP Batch 5 App.jsx
 * Role command-centre cards, data-confidence trust bar, lineage drawer,
 * blocked-answer warning state, and month-end landing forecast.
 *
 * Contract sources:
 *   GET /command-centres
 *   GET /forecast/month-end
 *   GET /quickball/explain?metric=<metric>&role=<role>
 */

import { useCallback, useEffect, useMemo, useState } from "react";

const BACKEND_URL = import.meta?.env?.VITE_BACKEND_URL || "https://scip.onrender.com";

const ROLE_ORDER = ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"];
const ROLE_LABELS = {
  board_cxo: "Board/CXO",
  cco_gm_agm: "CCO/GM/AGM",
  finance: "Finance",
  mis_qcg_admin: "MIS/QCG/Admin",
  collector_rm: "Collector/RM",
};

function formatCardValue(card) {
  return card?.display_value || card?.display || "Unavailable";
}

function DataConfidenceTrustBar({ trustBar, guardrails }) {
  const loaded = trustBar?.sources_loaded || [];
  const missing = trustBar?.sources_missing || [];
  const lineageCounts = trustBar?.critical_lineage_counts || {};
  const criticalSources = trustBar?.critical_sources || ["R18", "R04", "R02", "R08", "R36"];
  const allCriticalLineaged = criticalSources.every((source) => Number(lineageCounts[source] || 0) > 0);

  return (
    <section style={styles.trustBar} aria-label="Data confidence trust bar">
      <div style={styles.trustLeft}>
        <div style={styles.trustTitleRow}>
          <span style={{ ...styles.trustDot, background: allCriticalLineaged ? COLORS.green : COLORS.amber }} />
          <span style={styles.trustTitle}>Data Confidence</span>
          <span style={styles.trustStatus}>{allCriticalLineaged ? "Critical lineage live" : "Lineage needs review"}</span>
        </div>
        <div style={styles.trustMeta}>
          <span>Snapshot: {trustBar?.snapshot_date || "Unavailable"}</span>
          <span>Load: {trustBar?.load_timestamp || "Unavailable"}</span>
          <span>Tolerance: {trustBar?.tolerance_pct ?? 0.05}%</span>
          <span>No silent fallback: {guardrails?.no_silent_fallback ? "On" : "Check"}</span>
        </div>
      </div>
      <div style={styles.trustRight}>
        {criticalSources.map((source) => (
          <span key={source} style={styles.sourcePill} title={`${source} lineage count`}>
            {source}: {lineageCounts[source] || 0}
          </span>
        ))}
        <span style={styles.sourcePill}>Loaded: {loaded.length}</span>
        <span style={{ ...styles.sourcePill, ...(missing.length ? styles.sourcePillWarn : {}) }}>Missing: {missing.length}</span>
      </div>
    </section>
  );
}

function ForecastPanel({ forecast, onOpenLineage }) {
  if (!forecast) return null;

  if (forecast.status !== "ok") {
    return (
      <section style={styles.forecastPanel} role="alert">
        <h2 style={styles.panelTitle}>Month-end forecast blocked</h2>
        <p style={styles.warningText}>{forecast.reason || "Forecast could not be generated."}</p>
      </section>
    );
  }

  const d = forecast.display || {};
  const wd = forecast.working_days || {};
  const outputs = forecast.outputs || {};

  return (
    <section style={styles.forecastPanel} aria-label="Month-end landing forecast">
      <div style={styles.panelHeaderRow}>
        <div>
          <h2 style={styles.panelTitle}>May Month-end Landing Forecast</h2>
          <p style={styles.panelSub}>{forecast.basis_disclosure}</p>
        </div>
        <button style={styles.secondaryButton} onClick={() => onOpenLineage(forecast.lineage_refs || [], "Forecast lineage")}>View lineage</button>
      </div>

      <div style={styles.forecastGrid}>
        <MetricBox label="MTD actual" value={d.mtd_total_collections} basis="R04 Finance" />
        <MetricBox label="May target" value={d.may_total_collections_target} basis="R02 MDO" />
        <MetricBox label="Current run-rate" value={d.current_daily_run_rate} basis={`${wd.elapsed_working_days || "?"} elapsed working days`} />
        <MetricBox label="Required run-rate" value={d.required_daily_run_rate_remaining} basis={`${wd.remaining_working_days || "?"} remaining working days`} />
        <MetricBox label="Projected landing" value={d.projected_month_end_landing} basis="Straight-line projection" highlight />
        <MetricBox label="Projected achievement" value={d.projected_achievement_pct} basis={`Gap ${d.gap_to_may_mdo_target}`} highlight={Number(outputs.gap_to_may_mdo_target || 0) >= 0} />
      </div>

      <details style={styles.assumptionsBox} open>
        <summary style={styles.assumptionsSummary}>Forecast assumptions</summary>
        <ul style={styles.assumptionsList}>
          {(forecast.assumptions || []).map((item) => <li key={item}>{item}</li>)}
        </ul>
      </details>
    </section>
  );
}

function MetricBox({ label, value, basis, highlight }) {
  return (
    <div style={{ ...styles.metricBox, ...(highlight ? styles.metricBoxHighlight : {}) }}>
      <span style={styles.metricLabel}>{label}</span>
      <span style={styles.metricValue}>{value || "Unavailable"}</span>
      <span style={styles.metricBasis}>{basis}</span>
    </div>
  );
}

function BlockedAnswerWarning({ answer }) {
  if (!answer || answer.status !== "blocked_untrusted_metric") return null;
  return (
    <div style={styles.blockedWarning} role="alert">
      <strong>Quickball blocked an untrusted answer.</strong>
      <span>{answer.reason || "A critical metric failed lineage validation."}</span>
    </div>
  );
}

function CommandCentreCard({ card, onOpenLineage, onExplain }) {
  const refs = card?.lineage_display || card?.lineage_refs || [];
  const lineaged = refs.length > 0 && refs.every((ref) => ref.has_lineage);

  return (
    <article style={{ ...styles.card, ...(card?.severity === "risk" ? styles.cardRisk : {}), ...(card?.severity === "forecast" ? styles.cardForecast : {}) }}>
      <div style={styles.cardTopRow}>
        <span style={styles.cardSeverity}>{card?.severity || "info"}</span>
        <span style={{ ...styles.cardTrust, color: lineaged ? COLORS.green : COLORS.amber }}>{lineaged ? "Lineaged" : "Lineage warning"}</span>
      </div>
      <h3 style={styles.cardTitle}>{card?.title}</h3>
      <div style={styles.cardValue}>{formatCardValue(card)}</div>
      <div style={styles.cardBasis}>Reporting basis: {card?.reporting_basis || "Unavailable"}</div>
      <p style={styles.cardAction}>{card?.action}</p>
      {card?.basis_disclosure && <p style={styles.cardDisclosure}>{card.basis_disclosure}</p>}
      {(card?.assumptions || []).length > 0 && (
        <details style={styles.cardDetails}>
          <summary>Assumptions</summary>
          <ul>
            {card.assumptions.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </details>
      )}
      <div style={styles.cardActions}>
        <button style={styles.secondaryButton} onClick={() => onOpenLineage(refs, card?.title)}>Lineage</button>
        <button style={styles.secondaryButton} onClick={() => onExplain(card?.lineage_refs?.[0]?.metric_key || card?.lineage_display?.[0]?.metric_key)}>Explain</button>
      </div>
    </article>
  );
}

function LineageDrawer({ open, title, refs, onClose }) {
  if (!open) return null;
  return (
    <aside style={styles.drawer} role="dialog" aria-label="Lineage drawer">
      <div style={styles.drawerHeader}>
        <div>
          <h2 style={styles.drawerTitle}>{title || "Lineage"}</h2>
          <p style={styles.drawerSub}>Source file, sheet, cell/range, validation, confidence, and reporting basis.</p>
        </div>
        <button style={styles.closeButton} onClick={onClose}>Close</button>
      </div>
      <div style={styles.drawerBody}>
        {(refs || []).map((ref, index) => (
          <div key={`${ref.metric_key || "metric"}-${index}`} style={styles.lineageBlock}>
            <div style={styles.lineageMetric}>{ref.metric_key || "Metric"}</div>
            <div style={styles.lineageGrid}>
              <span>Source</span><strong>{ref.source_file || "Unavailable"}</strong>
              <span>Sheet</span><strong>{ref.sheet || "Unavailable"}</strong>
              <span>Cell/range</span><strong>{ref.cell_or_range || "Unavailable"}</strong>
              <span>Validation</span><strong>{ref.validation_status || "Unavailable"}</strong>
              <span>Confidence</span><strong>{ref.confidence_state || "Unavailable"}</strong>
              <span>Basis</span><strong>{ref.reporting_basis || "Unavailable"}</strong>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}

function QuickballExplainBox({ role, answer, onAsk }) {
  const [metric, setMetric] = useState("OD_TODAY");
  return (
    <section style={styles.quickballBox}>
      <div>
        <h2 style={styles.panelTitle}>Quickball Lineage Explain</h2>
        <p style={styles.panelSub}>Critical answers are blocked unless the metric has source, sheet, cell/range, validation and confidence.</p>
      </div>
      <div style={styles.quickballRow}>
        <input style={styles.input} value={metric} onChange={(e) => setMetric(e.target.value)} placeholder="OD_TODAY, PIPELINE_GROSS, MAY_TOTAL_COLLECTIONS_TARGET" />
        <button style={styles.primaryButton} onClick={() => onAsk(metric, role)}>Explain</button>
      </div>
      <BlockedAnswerWarning answer={answer} />
      {answer && answer.status !== "blocked_untrusted_metric" && (
        <div style={styles.answerBox}>
          <strong>{answer.metric_label || answer.metric_key}</strong>
          <p>{answer.answer}</p>
        </div>
      )}
    </section>
  );
}

export default function App() {
  const [payload, setPayload] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [role, setRole] = useState("board_cxo");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [drawer, setDrawer] = useState({ open: false, title: "", refs: [] });
  const [quickballAnswer, setQuickballAnswer] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [centresRes, forecastRes] = await Promise.all([
          fetch(`${BACKEND_URL}/command-centres`),
          fetch(`${BACKEND_URL}/forecast/month-end`),
        ]);
        if (!centresRes.ok) throw new Error(`Command centres ${centresRes.status}`);
        if (!forecastRes.ok) throw new Error(`Forecast ${forecastRes.status}`);
        const centresJson = await centresRes.json();
        const forecastJson = await forecastRes.json();
        if (!cancelled) {
          setPayload(centresJson);
          setForecast(forecastJson);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const activeRole = payload?.roles?.[role];
  const trustBar = activeRole?.trust_bar || payload?.roles?.board_cxo?.trust_bar;

  const allCards = useMemo(() => activeRole?.cards || [], [activeRole]);

  const openLineage = useCallback((refs, title) => setDrawer({ open: true, title, refs: refs || [] }), []);
  const closeLineage = useCallback(() => setDrawer({ open: false, title: "", refs: [] }), []);

  const askQuickball = useCallback(async (metric, roleKey) => {
    try {
      const params = new URLSearchParams({ metric: metric || "OD_TODAY", role: roleKey || role });
      const res = await fetch(`${BACKEND_URL}/quickball/explain?${params.toString()}`);
      if (!res.ok) throw new Error(`Quickball ${res.status}`);
      setQuickballAnswer(await res.json());
    } catch (err) {
      setQuickballAnswer({ status: "blocked_untrusted_metric", reason: err.message, answer: "Quickball is unavailable." });
    }
  }, [role]);

  if (loading) {
    return <main style={styles.loadingScreen}>Loading SCIP command centres...</main>;
  }

  if (error) {
    return (
      <main style={styles.loadingScreen} role="alert">
        <h1>SCIP command centre unavailable</h1>
        <p>{error}</p>
        <p>Backend may be warming up. Data is not silently replaced with fallback values.</p>
      </main>
    );
  }

  return (
    <main style={styles.appShell}>
      <header style={styles.header}>
        <div>
          <div style={styles.kicker}>SCIP Batch 5</div>
          <h1 style={styles.title}>Role Command Centres & Forecasting</h1>
          <p style={styles.subtitle}>Locked hierarchy · 0.05% tolerance · no silent fallback · Finance/MDO/R08/R36 labels visible</p>
        </div>
        <div style={styles.backendBadge}>{BACKEND_URL}</div>
      </header>

      <DataConfidenceTrustBar trustBar={trustBar} guardrails={payload?.guardrails} />

      <nav style={styles.roleTabs} aria-label="Role modes">
        {ROLE_ORDER.map((key) => (
          <button key={key} style={{ ...styles.roleTab, ...(role === key ? styles.roleTabActive : {}) }} onClick={() => setRole(key)}>
            {ROLE_LABELS[key]}
          </button>
        ))}
      </nav>

      <section style={styles.roleIntro}>
        <div>
          <h2 style={styles.roleTitle}>{activeRole?.role_label || ROLE_LABELS[role]}</h2>
          <p style={styles.rolePurpose}>{activeRole?.purpose}</p>
        </div>
        <div style={styles.contractBadge}>{payload?.contract_version}</div>
      </section>

      <ForecastPanel forecast={forecast || payload?.forecast} onOpenLineage={openLineage} />

      <section style={styles.cardGrid} aria-label={`${ROLE_LABELS[role]} command centre cards`}>
        {allCards.map((card) => (
          <CommandCentreCard key={card.card_id} card={card} onOpenLineage={openLineage} onExplain={(metric) => askQuickball(metric, role)} />
        ))}
      </section>

      <QuickballExplainBox role={role} answer={quickballAnswer} onAsk={askQuickball} />

      <LineageDrawer open={drawer.open} title={drawer.title} refs={drawer.refs} onClose={closeLineage} />
    </main>
  );
}

const COLORS = {
  bg: "#0f1623",
  panel: "#172033",
  panel2: "#1e2b42",
  border: "#30415f",
  text: "#e8e4dc",
  muted: "#a9b0bd",
  gold: "#c9a84c",
  green: "#22c55e",
  amber: "#f59e0b",
  red: "#ef4444",
};

const styles = {
  appShell: { minHeight: "100vh", background: COLORS.bg, color: COLORS.text, padding: 24, fontFamily: "Inter, Segoe UI, sans-serif" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 24, marginBottom: 18 },
  kicker: { color: COLORS.gold, textTransform: "uppercase", letterSpacing: "0.15em", fontSize: 11, fontWeight: 800 },
  title: { margin: "4px 0", fontSize: 30, lineHeight: 1.1 },
  subtitle: { margin: 0, color: COLORS.muted, maxWidth: 840 },
  backendBadge: { border: `1px solid ${COLORS.border}`, borderRadius: 999, padding: "8px 12px", color: COLORS.muted, fontSize: 12 },
  trustBar: { display: "flex", justifyContent: "space-between", gap: 20, background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 16, marginBottom: 16 },
  trustLeft: { display: "flex", flexDirection: "column", gap: 8 },
  trustTitleRow: { display: "flex", alignItems: "center", gap: 8 },
  trustDot: { width: 10, height: 10, borderRadius: 999 },
  trustTitle: { fontWeight: 800 },
  trustStatus: { color: COLORS.muted, fontSize: 12 },
  trustMeta: { display: "flex", flexWrap: "wrap", gap: 12, color: COLORS.muted, fontSize: 12 },
  trustRight: { display: "flex", flexWrap: "wrap", justifyContent: "flex-end", gap: 8 },
  sourcePill: { border: `1px solid ${COLORS.border}`, background: COLORS.panel2, borderRadius: 999, padding: "5px 9px", fontSize: 12 },
  sourcePillWarn: { borderColor: COLORS.amber, color: COLORS.amber },
  roleTabs: { display: "flex", flexWrap: "wrap", gap: 8, margin: "12px 0" },
  roleTab: { border: `1px solid ${COLORS.border}`, background: COLORS.panel, color: COLORS.text, borderRadius: 10, padding: "9px 12px", cursor: "pointer" },
  roleTabActive: { borderColor: COLORS.gold, color: COLORS.gold, background: COLORS.panel2 },
  roleIntro: { display: "flex", justifyContent: "space-between", alignItems: "center", background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 16, marginBottom: 16 },
  roleTitle: { margin: 0, fontSize: 22 },
  rolePurpose: { margin: "6px 0 0", color: COLORS.muted },
  contractBadge: { color: COLORS.muted, fontSize: 12 },
  forecastPanel: { background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 16, marginBottom: 16 },
  panelHeaderRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 },
  panelTitle: { margin: 0, fontSize: 19 },
  panelSub: { margin: "6px 0 0", color: COLORS.muted, lineHeight: 1.5 },
  forecastGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginTop: 16 },
  metricBox: { background: COLORS.panel2, border: `1px solid ${COLORS.border}`, borderRadius: 14, padding: 14, display: "flex", flexDirection: "column", gap: 5 },
  metricBoxHighlight: { borderColor: COLORS.gold },
  metricLabel: { color: COLORS.muted, fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em" },
  metricValue: { fontSize: 22, fontWeight: 800 },
  metricBasis: { color: COLORS.muted, fontSize: 12 },
  assumptionsBox: { marginTop: 14, borderTop: `1px solid ${COLORS.border}`, paddingTop: 10 },
  assumptionsSummary: { cursor: "pointer", color: COLORS.gold, fontWeight: 700 },
  assumptionsList: { color: COLORS.muted, lineHeight: 1.5 },
  cardGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(270px, 1fr))", gap: 14 },
  card: { background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 16, minHeight: 210 },
  cardRisk: { borderColor: "rgba(239,68,68,0.7)" },
  cardForecast: { borderColor: COLORS.gold },
  cardTopRow: { display: "flex", justifyContent: "space-between", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em" },
  cardSeverity: { color: COLORS.muted },
  cardTrust: { fontWeight: 800 },
  cardTitle: { margin: "12px 0 6px", fontSize: 17 },
  cardValue: { fontSize: 28, fontWeight: 900, color: COLORS.text },
  cardBasis: { marginTop: 6, color: COLORS.gold, fontSize: 12 },
  cardAction: { color: COLORS.muted, lineHeight: 1.5 },
  cardDisclosure: { color: COLORS.amber, fontSize: 12, lineHeight: 1.4 },
  cardDetails: { color: COLORS.muted, fontSize: 12 },
  cardActions: { display: "flex", gap: 8, marginTop: 14 },
  secondaryButton: { border: `1px solid ${COLORS.border}`, background: COLORS.panel2, color: COLORS.text, borderRadius: 10, padding: "8px 10px", cursor: "pointer" },
  primaryButton: { border: `1px solid ${COLORS.gold}`, background: COLORS.gold, color: COLORS.bg, borderRadius: 10, padding: "9px 14px", cursor: "pointer", fontWeight: 800 },
  drawer: { position: "fixed", right: 0, top: 0, bottom: 0, width: "min(560px, 94vw)", background: COLORS.panel, borderLeft: `1px solid ${COLORS.border}`, boxShadow: "-12px 0 40px rgba(0,0,0,0.35)", zIndex: 10, display: "flex", flexDirection: "column" },
  drawerHeader: { display: "flex", justifyContent: "space-between", gap: 12, padding: 18, borderBottom: `1px solid ${COLORS.border}` },
  drawerTitle: { margin: 0 },
  drawerSub: { margin: "6px 0 0", color: COLORS.muted, fontSize: 12 },
  closeButton: { alignSelf: "flex-start", border: `1px solid ${COLORS.border}`, background: COLORS.panel2, color: COLORS.text, borderRadius: 10, padding: "8px 10px", cursor: "pointer" },
  drawerBody: { overflowY: "auto", padding: 18, display: "flex", flexDirection: "column", gap: 12 },
  lineageBlock: { background: COLORS.panel2, border: `1px solid ${COLORS.border}`, borderRadius: 14, padding: 12 },
  lineageMetric: { fontWeight: 900, color: COLORS.gold, marginBottom: 8 },
  lineageGrid: { display: "grid", gridTemplateColumns: "110px 1fr", gap: "6px 10px", color: COLORS.muted, fontSize: 12 },
  quickballBox: { marginTop: 18, background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 16 },
  quickballRow: { display: "flex", gap: 10, marginTop: 12 },
  input: { flex: 1, border: `1px solid ${COLORS.border}`, background: COLORS.panel2, color: COLORS.text, borderRadius: 10, padding: "10px 12px" },
  blockedWarning: { marginTop: 12, display: "flex", flexDirection: "column", gap: 4, border: `1px solid ${COLORS.amber}`, background: "rgba(245,158,11,0.12)", borderRadius: 12, padding: 12, color: COLORS.amber },
  warningText: { color: COLORS.amber },
  answerBox: { marginTop: 12, background: COLORS.panel2, border: `1px solid ${COLORS.border}`, borderRadius: 12, padding: 12, lineHeight: 1.5 },
  loadingScreen: { minHeight: "100vh", background: COLORS.bg, color: COLORS.text, display: "grid", placeItems: "center", padding: 32, fontFamily: "Inter, Segoe UI, sans-serif" },
};
