/**
 * SCIP Batch 6 App.jsx
 * Liquid Glass action queues and collector drilldowns on top of Batch 5.1 contracts.
 *
 * Preserved backend contracts:
 *   GET /command-centres
 *   GET /forecast/month-end
 *   GET /quickball/explain?metric=<metric>&role=<role>
 *   GET /action-queues
 *   GET /action-queues/collector-drilldown
 *
 * Guardrails:
 *   - No frontend financial computation. The UI only displays server-provided values.
 *   - No silent fallback. If backend fails, show unavailable/error state.
 *   - Entity Head role remains removed.
 *   - Liquid Glass is used for movement, context, command and reveal.
 *   - Solid surfaces are used for KPIs, charts, evidence, formulas and financial truth.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import "./liquidGlassTokens.css";

const BACKEND_URL = import.meta?.env?.VITE_BACKEND_URL || "https://scip.onrender.com";

const ROLE_ORDER = ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"];
const ROLE_LABELS = {
  board_cxo: "Board/CXO",
  cco_gm_agm: "CCO/GM/AGM",
  finance: "Finance",
  mis_qcg_admin: "MIS/QCG/Admin",
  collector_rm: "Collector/RM",
};

const LIVE_PULSE_CHOICES = [
  {
    key: "current_signal",
    title: "Current Signal",
    question: "Are we okay today?",
    summary: "A calm reading of what needs attention now, anchored on OD, collections, and confidence.",
  },
  {
    key: "month_movement",
    title: "Month Movement",
    question: "How is this month moving?",
    summary: "MTD movement, run-rate, target gap, and the finance/MDO basis behind the month-end forecast.",
  },
  {
    key: "risk_action",
    title: "Risk & Action",
    question: "Where should we act?",
    summary: "Attention areas, OD pressure, collection gaps, and action-ready follow-up paths.",
  },
];

const NARRATIVE_STEPS = [
  { key: "story", label: "Story", question: "What is the board-level story?" },
  { key: "portfolio", label: "Portfolio", question: "What is the portfolio position?" },
  { key: "dues", label: "Dues", question: "Where is OD / dues risk?" },
  { key: "advance", label: "Advance", question: "What is the advance opportunity?" },
  { key: "roadmap", label: "Roadmap", question: "What should leadership do next?" },
];

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function formatCardValue(card) {
  return card?.display_value || card?.display || "Unavailable";
}

function pickCardsForFocus(cards, route, focus) {
  const all = safeArray(cards);
  if (all.length <= 4) return all;
  const lowered = (text) => String(text || "").toLowerCase();
  const rules = {
    current_signal: ["od", "today", "confidence", "lineage"],
    month_movement: ["mtd", "month", "forecast", "target", "run-rate", "collections"],
    risk_action: ["risk", "action", "gap", "overdue", "attention"],
    story: ["story", "board", "forecast", "pipeline"],
    portfolio: ["portfolio", "group", "pipeline", "achievement"],
    dues: ["dues", "od", "overdue", "ageing"],
    advance: ["advance", "rebate", "cy", "fy"],
    roadmap: ["roadmap", "action", "risk", "next"],
  };
  const keywords = rules[focus] || [];
  const scored = all.map((card, index) => {
    const haystack = [card.title, card.card_id, card.reporting_basis, card.action, card.severity].map(lowered).join(" ");
    const score = keywords.filter((keyword) => haystack.includes(keyword)).length;
    return { card, score, index };
  });
  const selected = scored
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .slice(0, route === "narratives" ? 4 : 4)
    .map((item) => item.card);
  return selected.length ? selected : all.slice(0, 4);
}

function getPrimaryCopy(route, focus, roleLabel) {
  const focusCopy = {
    current_signal: {
      answer: "Start with the signal, then ask for evidence only when needed.",
      copy: "The screen holds back dense tables and exposes the minimum trusted view: data confidence, the main lineaged cards, and the next curiosity path.",
    },
    month_movement: {
      answer: "The month view stays forecast-led and basis-labelled.",
      copy: "R04 Finance actuals and R02 MDO targets stay visibly labelled. The forecast panel discloses working-day assumptions and keeps calculations in the backend.",
    },
    risk_action: {
      answer: "Risk is treated as a prompt for action, not another chart wall.",
      copy: "The cards remain lineaged and action-oriented. Collector/account evidence remains gated until the user asks for depth.",
    },
    story: {
      answer: "Narratives now feel like a guided board briefing.",
      copy: "The rail moves Story → Portfolio → Dues → Advance → Roadmap. Executive output stays board-safe, while detailed evidence remains one click deeper.",
    },
    portfolio: {
      answer: "Portfolio is presented as position, implication, and proof on demand.",
      copy: "The screen prioritises a single board-safe answer and only reveals target basis, entity split, and source detail through the lineage/evidence drawer.",
    },
    dues: {
      answer: "Dues and OD are solid financial truth surfaces.",
      copy: "OD numbers never sit behind heavy blur. Glass is reserved for navigation and reveal; KPI cards remain stable and readable.",
    },
    advance: {
      answer: "Advance is framed as opportunity with CY/FY and rebate evidence.",
      copy: "R08 labels stay visible and the Sobha/UAQ hierarchy remains locked without inventing missing child splits.",
    },
    roadmap: {
      answer: "Roadmap closes the loop from insight to leadership action.",
      copy: "The interface keeps action close to context: Present, summary, export, action list, and Quickball explanation.",
    },
  };
  const item = focusCopy[focus] || focusCopy.current_signal;
  return { ...item, roleHint: `Current audience lens: ${roleLabel}.` };
}

function DataConfidenceTrustBar({ trustBar, guardrails }) {
  const loaded = safeArray(trustBar?.sources_loaded);
  const missing = safeArray(trustBar?.sources_missing);
  const lineageCounts = trustBar?.critical_lineage_counts || {};
  const criticalSources = trustBar?.critical_sources || ["R18", "R04", "R02", "R08", "R36"];
  const allCriticalLineaged = criticalSources.every((source) => Number(lineageCounts[source] || 0) > 0);

  return (
    <section className="trust-bar glass-surface" aria-label="Data confidence trust bar">
      <div>
        <div className="trust-title-row">
          <span className="trust-dot" style={{ background: allCriticalLineaged ? "var(--status-good)" : "var(--status-attention)" }} />
          <span className="trust-title">Data confidence</span>
          <span className="trust-status">{allCriticalLineaged ? "Critical lineage live" : "Lineage needs review"}</span>
        </div>
        <div className="trust-meta" aria-label="Data confidence metadata">
          <span>Snapshot: {trustBar?.snapshot_date || "Unavailable"}</span>
          <span>Load: {trustBar?.load_timestamp || "Unavailable"}</span>
          <span>Tolerance: {trustBar?.tolerance_pct ?? 0.05}%</span>
          <span>No silent fallback: {guardrails?.no_silent_fallback ? "On" : "Check"}</span>
        </div>
      </div>
      <div className="trust-sources" aria-label="Critical lineage counts">
        {criticalSources.map((source) => (
          <span className="source-pill" key={source}>{source}: {lineageCounts[source] || 0}</span>
        ))}
        <span className="source-pill">Loaded: {loaded.length}</span>
        <span className={`source-pill ${missing.length ? "warn" : ""}`}>Missing: {missing.length}</span>
      </div>
    </section>
  );
}

function MetricBox({ label, value, basis }) {
  return (
    <div className="metric-box solid-truth">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value || "Unavailable"}</span>
      <span className="metric-basis">{basis}</span>
    </div>
  );
}

function ForecastPanel({ forecast, onOpenLineage }) {
  if (!forecast) return null;

  if (forecast.status !== "ok") {
    return (
      <section className="forecast-panel solid-truth" role="alert" aria-label="Month-end forecast blocked">
        <h2 className="panel-title">Month-end forecast blocked</h2>
        <p className="panel-sub">{forecast.reason || "Forecast could not be generated. No fallback forecast is shown."}</p>
      </section>
    );
  }

  const d = forecast.display || {};
  const wd = forecast.working_days || {};

  return (
    <section className="forecast-panel solid-truth gold-edge" aria-label="Month-end landing forecast">
      <div className="panel-header-row">
        <div>
          <div className="kicker">Month Movement</div>
          <h2 className="panel-title">May month-end landing forecast</h2>
          <p className="panel-sub">{forecast.basis_disclosure}</p>
        </div>
        <button className="secondary-button" onClick={() => onOpenLineage(forecast.lineage_refs || [], "Forecast lineage")}>View lineage</button>
      </div>

      <div className="forecast-grid">
        <MetricBox label="MTD actual" value={d.mtd_total_collections} basis="R04 Finance" />
        <MetricBox label="May target" value={d.may_total_collections_target} basis="R02 MDO" />
        <MetricBox label="Current run-rate" value={d.current_daily_run_rate} basis={`${wd.elapsed_working_days || "?"} elapsed working days`} />
        <MetricBox label="Required run-rate" value={d.required_daily_run_rate_remaining} basis={`${wd.remaining_working_days || "?"} remaining working days`} />
        <MetricBox label="Projected landing" value={d.projected_month_end_landing} basis="Backend straight-line projection" />
        <MetricBox label="Projected achievement" value={d.projected_achievement_pct} basis={`Gap ${d.gap_to_may_mdo_target || "Unavailable"}`} />
      </div>

      <details className="assumptions-box" open>
        <summary>Forecast assumptions</summary>
        <ul>
          {safeArray(forecast.assumptions).map((item) => <li key={item}>{item}</li>)}
        </ul>
      </details>
    </section>
  );
}

function CommandCentreCard({ card, onOpenLineage, onExplain }) {
  const refs = card?.lineage_display || card?.lineage_refs || [];
  const lineaged = refs.length > 0 && refs.every((ref) => ref.has_lineage);
  return (
    <article className="kpi-card solid-truth" aria-label={`${card?.title || "Command centre card"} card`}>
      <span className="label">{card?.severity || "info"} · {lineaged ? "Lineaged" : "Lineage warning"}</span>
      <h3>{card?.title}</h3>
      <span className="value">{formatCardValue(card)}</span>
      <span className="basis">Reporting basis: {card?.reporting_basis || "Unavailable"}</span>
      <p>{card?.action}</p>
      {card?.basis_disclosure && <p>{card.basis_disclosure}</p>}
      {safeArray(card?.assumptions).length > 0 && (
        <details>
          <summary>Assumptions</summary>
          <ul>
            {card.assumptions.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </details>
      )}
      <div className="curiosity-row" aria-label="Card actions">
        <button className="secondary-button" onClick={() => onOpenLineage(refs, card?.title)}>Show evidence</button>
        <button className="ghost-button" onClick={() => onExplain(card?.lineage_refs?.[0]?.metric_key || card?.lineage_display?.[0]?.metric_key)}>Ask Quickball</button>
      </div>
    </article>
  );
}

function ArrivalScreen({ onEnter, dataDate }) {
  return (
    <main className="arrival" aria-label="SCIP arrival">
      <section className="arrival-card glass-surface gold-edge">
        <div className="kicker">Sobha Collections Intelligence Platform</div>
        <h1 className="arrival-title">SCIP</h1>
        <p className="arrival-subtitle">Begin with the signal. Follow an intelligent briefing that can go as deep as you ask.</p>
        <div className="arrival-doors" aria-label="Primary entry choices">
          <button className="door-card glass-surface" onClick={() => onEnter("live_pulse")}>
            <span className="kicker">Live Pulse</span>
            <h2>What needs attention now?</h2>
            <p>Current signal, month movement, risk and action. No raw tree until you ask for depth.</p>
          </button>
          <button className="door-card glass-surface" onClick={() => onEnter("narratives")}>
            <span className="kicker">Narratives</span>
            <h2>The story behind the numbers.</h2>
            <p>Guided executive briefing: Story, Portfolio, Dues, Advance, Roadmap, and Present-ready outputs.</p>
          </button>
        </div>
        <p className="data-date-note">Data date: {dataDate || "Unavailable"}</p>
      </section>
      <QuickballCommand collapsedPrompt="Ask Quickball..." />
    </main>
  );
}

function ContextIsland({ route, focus, depth, role, setRole, payload }) {
  const world = route === "narratives" ? "Narratives" : "Live Pulse";
  const focusLabel = route === "narratives"
    ? (NARRATIVE_STEPS.find((item) => item.key === focus)?.label || "Story")
    : (LIVE_PULSE_CHOICES.find((item) => item.key === focus)?.title || "Current Signal");
  return (
    <section className="context-island glass-surface" aria-label="Current context">
      <div>
        <div className="kicker">{world}</div>
        <div className="context-row">
          <span className="context-pill">Focus: {focusLabel}</span>
          <span className="context-pill">Depth: {depth}</span>
          <span className="context-pill">Entity: Group</span>
          <span className="context-pill">Basis labels: Finance · MDO · R08 · R36</span>
          <span className="context-pill">Contract: {payload?.contract_version || "Unavailable"}</span>
        </div>
      </div>
      <label>
        <span className="kicker">Audience lens</span>{" "}
        <select className="context-select" value={role} onChange={(event) => setRole(event.target.value)} aria-label="Audience lens">
          {ROLE_ORDER.map((key) => <option key={key} value={key}>{ROLE_LABELS[key]}</option>)}
        </select>
      </label>
    </section>
  );
}

function WorldHome({ route, focus, setFocus }) {
  if (route === "narratives") {
    return (
      <section className="world-home glass-surface" aria-label="Narratives home">
        <div className="kicker">Narratives</div>
        <h2 className="world-headline">A guided boardroom journey, not a dashboard menu.</h2>
        <p className="world-summary">Move through Story, Portfolio, Dues, Advance and Roadmap. Evidence appears only when requested.</p>
        <nav className="narrative-rail" aria-label="Narrative steps">
          {NARRATIVE_STEPS.map((step) => (
            <button key={step.key} className="rail-button" aria-current={focus === step.key ? "step" : undefined} onClick={() => setFocus(step.key)}>
              {step.label}
            </button>
          ))}
        </nav>
      </section>
    );
  }

  return (
    <section className="world-home glass-surface" aria-label="Live Pulse home">
      <div className="kicker">Live Pulse</div>
      <h2 className="world-headline">Three choices only. One signal at a time.</h2>
      <p className="world-summary">Target Track/YTD remains available as a follow-up from Month Movement, not as a fourth first-level choice.</p>
      <div className="choice-grid">
        {LIVE_PULSE_CHOICES.map((choice) => (
          <button key={choice.key} className="choice-card glass-surface" aria-pressed={focus === choice.key} onClick={() => setFocus(choice.key)}>
            <span className="kicker">{choice.question}</span>
            <h3>{choice.title}</h3>
            <p>{choice.summary}</p>
          </button>
        ))}
      </div>
    </section>
  );
}

function FocusScreen({ route, focus, roleLabel, cards, forecast, onOpenLineage, onExplain, setFocus }) {
  const selectedCards = pickCardsForFocus(cards, route, focus);
  const copy = getPrimaryCopy(route, focus, roleLabel);
  const primaryCard = selectedCards[0];
  const question = route === "narratives"
    ? (NARRATIVE_STEPS.find((item) => item.key === focus)?.question || "What is the board-level story?")
    : (LIVE_PULSE_CHOICES.find((item) => item.key === focus)?.question || "Are we okay today?");

  return (
    <section className="focus-screen glass-surface" aria-label="Focus screen">
      <div className="focus-layout">
        <div>
          <p className="screen-question">{question}</p>
          <h2 className="primary-answer">{copy.answer}</h2>
          <p className="answer-copy">{copy.copy} {copy.roleHint}</p>
          <div className="curiosity-row" aria-label="Curiosity paths">
            <button className="curiosity-chip" onClick={() => onOpenLineage(primaryCard?.lineage_display || primaryCard?.lineage_refs || [], primaryCard?.title || "Evidence")}>Show evidence</button>
            <button className="curiosity-chip" onClick={() => onExplain(primaryCard?.lineage_refs?.[0]?.metric_key || primaryCard?.lineage_display?.[0]?.metric_key || "OD_TODAY")}>Ask about this number</button>
            {route === "live_pulse" && focus === "month_movement" ? (
              <button className="curiosity-chip" onClick={() => setFocus("target_track")}>Open Target Track/YTD lens</button>
            ) : (
              <button className="curiosity-chip" onClick={() => setFocus(route === "narratives" ? "dues" : "risk_action")}>What should we do?</button>
            )}
          </div>
        </div>
        <div className="primary-visual solid-truth gold-edge" aria-label="Primary visual">
          <div>
            <span className="kicker">Primary visual</span>
            <div className="visual-number">{primaryCard ? formatCardValue(primaryCard) : forecast?.display?.projected_month_end_landing || "—"}</div>
          </div>
          <p className="visual-caption">{primaryCard?.title || "Forecast landing"} · Reporting basis: {primaryCard?.reporting_basis || forecast?.reporting_basis || "Backend contract"}</p>
        </div>
      </div>

      <div className="kpi-strip" aria-label="Lineaged command-centre cards">
        {selectedCards.map((card) => (
          <CommandCentreCard key={card.card_id || card.title} card={card} onOpenLineage={onOpenLineage} onExplain={onExplain} />
        ))}
      </div>
    </section>
  );
}

function ActionQueuePanel({ actionQueues, role, focus, depth, onOpenLineage }) {
  if (focus !== "risk_action") return null;
  if (!actionQueues) {
    return (
      <section className="action-queue-panel solid-truth" aria-label="Action queues unavailable">
        <div className="panel-header-row">
          <div>
            <div className="kicker">Risk & Action · L5 output</div>
            <h2 className="panel-title">Action queues unavailable</h2>
            <p className="panel-sub">The backend did not provide action-queue data. No fallback actions are shown.</p>
          </div>
        </div>
      </section>
    );
  }

  const queueRole = actionQueues.roles?.[role] || actionQueues.roles?.cco_gm_agm || {};
  const cohorts = safeArray(queueRole.project_risk_cohorts).slice(0, depth === "detailed" ? 8 : 4);
  const blocked = safeArray(queueRole.blocked_actions).slice(0, 4);
  const accountActions = safeArray(queueRole.account_actions);
  const showEvidenceTable = depth === "detailed";

  return (
    <section className="action-queue-panel solid-truth" aria-label="Account-level action queues and collector drilldowns">
      <div className="panel-header-row">
        <div>
          <div className="kicker">Risk & Action · L5 output</div>
          <h2 className="panel-title">Action queues and collector drilldowns</h2>
          <p className="panel-sub">{queueRole.headline || "Action queue status unavailable."}</p>
        </div>
        <div className="queue-status-stack">
          <span className={`queue-status ${accountActions.length ? "ready" : "blocked"}`}>
            {accountActions.length ? "Account actions ready" : "Account actions blocked"}
          </span>
          <span className="queue-basis">{queueRole.reporting_basis || actionQueues.status}</span>
        </div>
      </div>

      <div className="blocked-source-banner" role="status">
        <strong>Account-level safety gate:</strong> {queueRole.disclosure || actionQueues.data_grain_disclosure?.reason}
      </div>

      {role === "collector_rm" && blocked.length > 0 && (
        <div className="blocked-actions-grid" aria-label="Blocked collector actions">
          {blocked.map((item) => (
            <article className="blocked-action-card" key={item.action_id}>
              <div className="queue-severity">{item.severity}</div>
              <h3>{item.title}</h3>
              <p>{item.blocked_reason}</p>
              <span>{item.display_amount} · {item.ageing_bucket}</span>
              <button className="secondary-button" onClick={() => onOpenLineage(item.lineage_refs || [], item.title)}>View source evidence</button>
            </article>
          ))}
        </div>
      )}

      {role !== "collector_rm" && cohorts.length > 0 && (
        <div className="action-cohort-grid" aria-label="Project risk cohorts">
          {cohorts.map((item) => (
            <article className="action-cohort-card" key={item.action_id}>
              <div className="queue-card-topline">
                <span className={`severity-dot ${item.severity}`}></span>
                <span>{item.entity_display}</span>
                <span>{item.ageing_bucket}</span>
              </div>
              <h3>{item.title}</h3>
              <p>{item.summary}</p>
              <div className="queue-card-footer">
                <span>{item.display_amount}</span>
                <button className="secondary-button" onClick={() => onOpenLineage(item.lineage_refs || [], item.title)}>Lineage</button>
              </div>
            </article>
          ))}
        </div>
      )}

      {showEvidenceTable && role !== "collector_rm" && cohorts.length > 0 && (
        <div className="solid-evidence-table" aria-label="Detailed project risk evidence">
          <div className="evidence-table-row evidence-table-head">
            <span>Project</span><span>Entity</span><span>Ageing</span><span>Amount</span><span>Basis</span>
          </div>
          {cohorts.map((item) => (
            <div className="evidence-table-row" key={`row-${item.action_id}`}>
              <span>{item.project}</span>
              <span>{item.entity_display}</span>
              <span>{item.ageing_bucket}</span>
              <span>{item.display_amount}</span>
              <span>{item.reporting_basis}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function LineageDrawer({ open, title, refs, onClose }) {
  if (!open) return null;
  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} aria-hidden="true" />
      <aside className="lineage-drawer glass-surface" role="dialog" aria-modal="true" aria-label="Lineage drawer">
        <div className="drawer-header">
          <div>
            <h2 className="drawer-title">{title || "Evidence"}</h2>
            <p className="drawer-sub">Source file, sheet, cell/range, validation, confidence and reporting basis. Evidence is shown only after request.</p>
          </div>
          <button className="secondary-button" onClick={onClose}>Close</button>
        </div>
        <div className="drawer-body">
          {safeArray(refs).length === 0 && <div className="lineage-block solid-truth">No lineage reference supplied by backend for this item.</div>}
          {safeArray(refs).map((ref, index) => (
            <div key={`${ref.metric_key || "metric"}-${index}`} className="lineage-block solid-truth">
              <div className="lineage-metric">{ref.metric_key || "Metric"}</div>
              <div className="lineage-grid">
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
    </>
  );
}

function QuickballCommand({ role, answer, onAsk, collapsedPrompt = "Ask about this number..." }) {
  const [metric, setMetric] = useState("");
  const blocked = answer?.status === "blocked_untrusted_metric";
  return (
    <section className="quickball-capsule glass-surface" aria-label="Quickball command capsule">
      <div className="quickball-row">
        <input
          className="quickball-input"
          value={metric}
          onChange={(event) => setMetric(event.target.value)}
          placeholder={collapsedPrompt}
          aria-label="Ask Quickball"
        />
        {onAsk ? <button className="primary-button" onClick={() => onAsk(metric, role)}>Ask</button> : null}
      </div>
      {answer && (
        <div className={`quickball-answer solid-truth ${blocked ? "blocked-warning" : ""}`} role={blocked ? "alert" : "status"}>
          <strong>{blocked ? "Quickball blocked an untrusted answer." : (answer.metric_label || answer.metric_key || "Quickball")}</strong>
          <p>{blocked ? (answer.reason || "A critical metric failed lineage validation.") : answer.answer}</p>
        </div>
      )}
    </section>
  );
}

export default function App() {
  const [payload, setPayload] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [actionQueues, setActionQueues] = useState(null);
  const [role, setRole] = useState("board_cxo");
  const [route, setRoute] = useState("arrival");
  const [focus, setFocus] = useState("current_signal");
  const [depth, setDepth] = useState("summary");
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
        const [centresRes, forecastRes, actionQueuesRes] = await Promise.all([
          fetch(`${BACKEND_URL}/command-centres`),
          fetch(`${BACKEND_URL}/forecast/month-end`),
          fetch(`${BACKEND_URL}/action-queues`),
        ]);
        if (!centresRes.ok) throw new Error(`Command centres ${centresRes.status}`);
        if (!forecastRes.ok) throw new Error(`Forecast ${forecastRes.status}`);
        if (!actionQueuesRes.ok) throw new Error(`Action queues ${actionQueuesRes.status}`);
        const centresJson = await centresRes.json();
        const forecastJson = await forecastRes.json();
        const actionQueuesJson = await actionQueuesRes.json();
        if (!cancelled) {
          setPayload(centresJson);
          setForecast(forecastJson);
          setActionQueues(actionQueuesJson);
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

  const activeRole = payload?.roles?.[role] || payload?.roles?.board_cxo || {};
  const trustBar = activeRole?.trust_bar || payload?.roles?.board_cxo?.trust_bar;
  const cards = useMemo(() => safeArray(activeRole?.cards), [activeRole]);
  const roleLabel = ROLE_LABELS[role] || "Board/CXO";

  const openLineage = useCallback((refs, title) => setDrawer({ open: true, title, refs: refs || [] }), []);
  const closeLineage = useCallback(() => setDrawer({ open: false, title: "", refs: [] }), []);

  const enterWorld = useCallback((nextRoute) => {
    setRoute(nextRoute);
    setFocus(nextRoute === "narratives" ? "story" : "current_signal");
    setDepth(nextRoute === "narratives" ? "executive" : "summary");
  }, []);

  const askQuickball = useCallback(async (metric, roleKey) => {
    try {
      const params = new URLSearchParams({ metric: metric || "OD_TODAY", role: roleKey || role });
      const res = await fetch(`${BACKEND_URL}/quickball/explain?${params.toString()}`);
      if (!res.ok) throw new Error(`Quickball ${res.status}`);
      const json = await res.json();
      const actions = safeArray(json.follow_up_actions).slice(0, 2);
      setQuickballAnswer({ ...json, follow_up_actions: actions });
    } catch (err) {
      setQuickballAnswer({ status: "blocked_untrusted_metric", reason: err.message, answer: "Quickball is unavailable." });
    }
  }, [role]);

  if (loading) {
    return <main className="loading-screen">Loading SCIP Liquid Glass command surface...</main>;
  }

  if (error) {
    return (
      <main className="loading-screen" role="alert">
        <section className="error-card solid-truth">
          <h1>SCIP unavailable</h1>
          <p>{error}</p>
          <p>No fallback figures are shown. Backend data must be live and lineaged.</p>
        </section>
      </main>
    );
  }

  if (route === "arrival") {
    return <ArrivalScreen onEnter={enterWorld} dataDate={trustBar?.snapshot_date} />;
  }

  return (
    <main className="scip-app">
      <div className="liquid-page">
        <header className="top-chrome" aria-label="SCIP header">
          <div>
            <div className="kicker">SCIP Batch 6 · Liquid Glass</div>
            <h1 className="brand-title">{route === "narratives" ? "Narratives" : "Live Pulse"}</h1>
          </div>
          <div className="chrome-actions">
            <button className="ghost-button" onClick={() => setRoute("arrival")}>Home</button>
            <button className="secondary-button" onClick={() => enterWorld("live_pulse")}>Live Pulse</button>
            <button className="secondary-button" onClick={() => enterWorld("narratives")}>Narratives</button>
            <button className="ghost-button" onClick={() => setDepth(depth === "detailed" ? (route === "narratives" ? "executive" : "summary") : "detailed")}>{depth === "detailed" ? "Reduce depth" : "Detailed"}</button>
          </div>
        </header>

        <ContextIsland route={route} focus={focus} depth={depth} role={role} setRole={setRole} payload={payload} />
        <DataConfidenceTrustBar trustBar={trustBar} guardrails={payload?.guardrails} />
        <WorldHome route={route} focus={focus} setFocus={setFocus} />
        <FocusScreen route={route} focus={focus} roleLabel={roleLabel} cards={cards} forecast={forecast || payload?.forecast} onOpenLineage={openLineage} onExplain={(metric) => askQuickball(metric, role)} setFocus={setFocus} />
        {route === "live_pulse" && (focus === "month_movement" || focus === "target_track") && <ForecastPanel forecast={forecast || payload?.forecast} onOpenLineage={openLineage} />}
        {route === "live_pulse" && <ActionQueuePanel actionQueues={actionQueues} role={role} focus={focus} depth={depth} onOpenLineage={openLineage} />}
        <LineageDrawer open={drawer.open} title={drawer.title} refs={drawer.refs} onClose={closeLineage} />
      </div>
      <QuickballCommand role={role} answer={quickballAnswer} onAsk={askQuickball} collapsedPrompt={route === "narratives" ? "Ask for board explanation..." : "Ask about today's movement..."} />
    </main>
  );
}
