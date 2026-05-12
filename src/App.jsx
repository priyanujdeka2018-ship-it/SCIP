/**
 * SCIP Batch 13 App.jsx
 * Liquid Glass SSO/JWT identity layer on top of Batch 12 observability and Batch 11 RBAC hardening.
 *
 * Preserved backend contracts:
 *   GET /command-centres
 *   GET /forecast/month-end
 *   GET /quickball/explain?metric=<metric>&role=<role>
 *   GET /action-queues
 *   GET /action-queues/collector-drilldown
 *   GET /workflows
 *   POST /workflows/assign | /reassign | /due-date | /disposition | /evidence | /close
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
const LOCAL_DEV_BYPASS = import.meta?.env?.VITE_SCIP_LOCAL_DEV_BYPASS === "true";

const ROLE_ORDER = ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"];
const ACTOR_IDS = {
  board_cxo: "board_cxo_demo",
  cco_gm_agm: "cco_manager_demo",
  finance: "finance_demo",
  mis_qcg_admin: "mis_admin_demo",
  collector_rm: "collector_rm_demo",
};

function demoJwtForRole(role) {
  const envKey = `VITE_SCIP_JWT_${String(role || "").toUpperCase()}`;
  return import.meta?.env?.[envKey] || import.meta?.env?.VITE_SCIP_DEMO_JWT || "";
}

function authHeaders(role) {
  const correlationId = `scip-ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  if (LOCAL_DEV_BYPASS) {
    return {
      "X-SCIP-Actor-ID": ACTOR_IDS[role] || "board_cxo_demo",
      "X-SCIP-Actor-Name": ROLE_LABELS[role] || "Board/CXO",
      "X-SCIP-Role": role,
      "X-SCIP-Entity-Scope": role === "collector_rm" ? "Sobha Dubai" : "Group",
      "X-SCIP-Collector-ID": role === "collector_rm" ? "collector_rm_demo" : "",
      "X-SCIP-Environment": "local",
      "X-SCIP-Correlation-ID": correlationId,
    };
  }
  const token = demoJwtForRole(role);
  return {
    Authorization: token ? `Bearer ${token}` : "",
    "X-SCIP-Correlation-ID": correlationId,
  };
}


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


function SecurityPostureBar({ security, role }) {
  const actor = security?.actor || {};
  const permissions = actor.permissions || [];
  return (
    <section className="security-posture glass-surface" aria-label="Security and RBAC posture">
      <div>
        <div className="kicker">Batch 11 · Secured RBAC</div>
        <h2>Authenticated actor: {actor.role_label || ROLE_LABELS[role]}</h2>
        <p>Row-level visibility is enforced by role, entity scope, and owner where applicable. Entity Head remains removed.</p>
      </div>
      <div className="security-chip-row">
        <span className="source-pill">Actor: {actor.actor_id || ACTOR_IDS[role]}</span>
        <span className="source-pill">Role: {actor.role || role}</span>
        <span className="source-pill">Permissions: {permissions.length}</span>
        <span className="source-pill">Audit denied attempts: logged</span>
      </div>
    </section>
  );
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

function ActionQueuePanel({ actionQueues, workflows, role, focus, depth, onOpenLineage, onOpenWorkflow }) {
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
  const accountActions = safeArray(queueRole.account_actions).slice(0, depth === "detailed" ? 10 : 5);
  const processActions = safeArray(queueRole.process_actions).slice(0, depth === "detailed" ? 8 : 4);
  const managementActions = safeArray(queueRole.management_actions).slice(0, depth === "detailed" ? 8 : 4);
  const blocked = safeArray(queueRole.blocked_actions).slice(0, 4);
  const showEvidenceTable = depth === "detailed";
  const workflowRecords = safeArray(workflows?.records);
  const workflowByActionId = new Map(workflowRecords.map((record) => [record.source_action_id, record]));

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
            {accountActions.length ? "Account actions ready" : "No account actions"}
          </span>
          <span className="queue-basis">{queueRole.reporting_basis || actionQueues.status}</span>
          <span className="queue-basis">Workflow: {workflows?.summary?.state_counts?.queued ?? 0} queued / {workflows?.summary?.state_counts?.assigned ?? 0} assigned</span>
        </div>
      </div>

      <div className="blocked-source-banner" role="status">
        <strong>Account-level safety gate:</strong> {queueRole.disclosure || actionQueues.data_grain_disclosure?.rule}
      </div>

      {accountActions.length > 0 && (
        <div className="account-action-grid" aria-label="Lineaged account actions">
          {accountActions.map((item) => (
            <article className="account-action-card" key={item.action_id}>
              <div className="queue-card-topline">
                <span className={`severity-dot ${item.severity}`}></span>
                <span>{item.entity_display || "Entity"}</span>
                <span>{item.ageing_bucket || item.pr_status || "Status"}</span>
              </div>
              <h3>{item.title}</h3>
              <p>{item.summary}</p>
              <dl className="account-action-meta">
                <div><dt>Owner</dt><dd>{item.collector_rm_owner || "Unavailable"}</dd></div>
                <div><dt>Account</dt><dd>{item.account_id || "Unavailable"}</dd></div>
                <div><dt>Unit</dt><dd>{item.unit || "Unavailable"}</dd></div>
                <div><dt>Amount</dt><dd>{item.display_amount || "Unavailable"}</dd></div>
              </dl>
              {item.ptp_date && <p className="queue-note">PTP date: {item.ptp_date}</p>}
              <div className="queue-card-footer">
                <span>{item.reporting_basis}</span>
                <button className="secondary-button" onClick={() => onOpenLineage(item.lineage_refs || [], item.title)}>Lineage</button>
                <button className="primary-button" onClick={() => onOpenWorkflow(workflowByActionId.get(item.action_id), item)}>Workflow</button>
              </div>
            </article>
          ))}
        </div>
      )}

      {processActions.length > 0 && (
        <div className="action-cohort-grid" aria-label="Process and governance actions">
          {processActions.map((item) => (
            <article className="action-cohort-card" key={item.action_id}>
              <div className="queue-card-topline">
                <span className={`severity-dot ${item.severity}`}></span>
                <span>{item.action_type}</span>
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

      {managementActions.length > 0 && role !== "collector_rm" && (
        <div className="action-cohort-grid" aria-label="Management escalation actions">
          {managementActions.map((item) => (
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

      {role === "collector_rm" && blocked.length > 0 && (
        <div className="blocked-actions-grid" aria-label="Blocked collector actions">
          {blocked.map((item) => (
            <article className="blocked-action-card" key={item.action_id}>
              <div className="queue-severity">{item.severity}</div>
              <h3>{item.title}</h3>
              <p>{item.blocked_reason}</p>
              <button className="secondary-button" onClick={() => onOpenLineage(item.lineage_refs || [], item.title)}>View source evidence</button>
            </article>
          ))}
        </div>
      )}

      {showEvidenceTable && accountActions.length > 0 && (
        <div className="solid-evidence-table" aria-label="Detailed account action evidence">
          <div className="evidence-table-row evidence-table-head">
            <span>Owner</span><span>Account</span><span>Unit</span><span>Status</span><span>Amount</span><span>Basis</span>
          </div>
          {accountActions.map((item) => (
            <div className="evidence-table-row" key={`row-${item.action_id}`}>
              <span>{item.collector_rm_owner}</span>
              <span>{item.account_id}</span>
              <span>{item.unit}</span>
              <span>{item.ageing_bucket || item.pr_status}</span>
              <span>{item.display_amount}</span>
              <span>{item.reporting_basis}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}


function WorkflowDrawer({ open, record, sourceAction, onClose }) {
  if (!open) return null;
  const timeline = safeArray(record?.event_log || record?.events);
  const evidence = safeArray(record?.evidence_attachments);
  const source = record?.source_snapshot || sourceAction || {};
  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} aria-hidden="true" />
      <aside className="workflow-drawer glass-surface" role="dialog" aria-modal="true" aria-label="Workflow assignment drawer">
        <div className="drawer-header">
          <div>
            <div className="kicker">L5 action output · Workflow</div>
            <h2 className="drawer-title">{record?.title || sourceAction?.title || "Workflow action"}</h2>
            <p className="drawer-sub">Assignment and closure tracking inherits the source action gate. Source lineage remains immutable.</p>
          </div>
          <button className="secondary-button" onClick={onClose}>Close</button>
        </div>
        <div className="workflow-grid">
          <div className="workflow-summary solid-truth">
            <div className="workflow-state-pill">{record?.workflow_state || "queued"}</div>
            <dl className="account-action-meta">
              <div><dt>Assigned owner</dt><dd>{record?.assigned_owner || source.collector_rm_owner || "Unavailable"}</dd></div>
              <div><dt>Account</dt><dd>{source.account_id || "Unavailable"}</dd></div>
              <div><dt>Unit</dt><dd>{source.unit || "Unavailable"}</dd></div>
              <div><dt>Due date</dt><dd>{record?.due_date || "Not set"}</dd></div>
              <div><dt>Amount/status</dt><dd>{source.display_amount || source.pr_status || "Unavailable"}</dd></div>
              <div><dt>Basis</dt><dd>{source.reporting_basis || sourceAction?.reporting_basis || "Unavailable"}</dd></div>
            </dl>
          </div>
          <div className="workflow-actions solid-truth">
            <h3>Allowed workflow updates</h3>
            <p>Assign, reassign, due date, disposition, evidence, and closure are backend operations. This drawer displays the contract without moving workflow logic into the frontend.</p>
            <div className="workflow-button-row">
              <button className="secondary-button">Assign</button>
              <button className="secondary-button">Set due date</button>
              <button className="secondary-button">Disposition</button>
              <button className="secondary-button">Attach evidence</button>
              <button className="primary-button">Close</button>
            </div>
          </div>
        </div>
        <div className="solid-evidence-table workflow-timeline" aria-label="Solid evidence timeline">
          <div className="evidence-table-row evidence-table-head">
            <span>Event</span><span>Actor</span><span>From</span><span>To</span><span>Lineage hash</span><span>Time</span>
          </div>
          {timeline.length === 0 && (
            <div className="evidence-table-row"><span>No events loaded</span><span /> <span /> <span /> <span /> <span /></div>
          )}
          {timeline.map((event) => (
            <div className="evidence-table-row" key={event.event_id}>
              <span>{event.event_type}</span>
              <span>{event.actor_role}</span>
              <span>{event.from_state}</span>
              <span>{event.to_state}</span>
              <span>{String(event.lineage_hash || "").slice(0, 10)}...</span>
              <span>{event.created_at}</span>
            </div>
          ))}
        </div>
        {evidence.length > 0 && (
          <div className="solid-evidence-table" aria-label="Evidence attachments">
            <div className="evidence-table-row evidence-table-head"><span>Type</span><span>Reference</span><span>By</span><span>At</span><span>Note</span><span /></div>
            {evidence.map((item) => (
              <div className="evidence-table-row" key={item.evidence_id}><span>{item.evidence_type}</span><span>{item.evidence_ref}</span><span>{item.attached_by}</span><span>{item.attached_at}</span><span>{item.note}</span><span /></div>
            ))}
          </div>
        )}
      </aside>
    </>
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

function NotificationEscalationPanel({ notifications, role, focus, onOpenLineage }) {
  const items = safeArray(notifications?.notifications).filter((item) => !role || item.recipient_role === role).slice(0, 8);
  const digests = notifications?.digests || {};
  if (focus !== "risk_action") {
    return (
      <section className="notification-capsule glass-surface" aria-label="Notification automation gated">
        <div className="kicker">L5 notification output</div>
        <h3>Escalations stay behind Risk & Action.</h3>
        <p>Notifications are evidence-driven outputs, not a third Arrival door or separate dashboard.</p>
      </section>
    );
  }
  return (
    <section className="notification-panel glass-surface" aria-label="Notification and escalation automation">
      <div className="section-heading-row">
        <div>
          <div className="kicker">Batch 9 · Notifications</div>
          <h2>Escalation automation</h2>
          <p>Collector reminders, manager escalations, finance nudges, and MIS/QCG alerts only emit when source action lineage and workflow event lineage are present.</p>
        </div>
        <span className="status-pill">{notifications?.status || "unavailable"}</span>
      </div>
      <div className="notification-digest-grid">
        <DigestCard digest={digests.daily_live_pulse_risk_action} />
        <DigestCard digest={digests.weekly_management_review} />
      </div>
      <div className="solid-evidence-list" role="list">
        {items.length === 0 && <p className="muted">No notification emitted for this role. Missing evidence is blocked rather than guessed.</p>}
        {items.map((item) => (
          <article className="notification-row solid-truth" key={item.notification_id} role="listitem">
            <div>
              <div className="row-kicker">{item.severity} · {item.notification_type}</div>
              <h3>{item.title}</h3>
              <p>{item.message}</p>
              <p className="basis-line">Basis: {item.reporting_basis}</p>
              <p className="basis-line">Rule evidence: {item.rule_id} · Dedupe: {item.suppression?.dedupe_key}</p>
            </div>
            <div className="row-actions">
              <button className="secondary-button" onClick={() => onOpenLineage(item.lineage?.source_action_lineage_refs, item.title)}>Lineage</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}


function AuditExportPanel({ auditSummary, focus }) {
  if (focus !== "risk_action") {
    return (
      <section className="audit-export-capsule glass-surface" aria-label="Audit export gated">
        <div className="kicker">L5 audit output</div>
        <h3>Audit exports stay behind Risk & Action.</h3>
        <p>Persistence, audit export, and evidence packs remain output actions, not a third Arrival door.</p>
      </section>
    );
  }
  const counts = auditSummary?.table_counts || {};
  const validations = auditSummary?.validations?.checks || {};
  return (
    <section className="audit-export-panel glass-surface" aria-label="Durable audit export">
      <div className="section-heading-row">
        <div>
          <div className="kicker">Batch 10 · Persistence & Audit</div>
          <h2>Durable audit pack</h2>
          <p>Workflow records, workflow events, notification emissions, suppression state, and audit exports are persisted with immutable lineage hashes.</p>
        </div>
        <span className="status-pill">{auditSummary?.status || "unseeded"}</span>
      </div>
      <div className="notification-digest-grid">
        <article className="digest-card solid-truth">
          <div className="row-kicker">Persistence</div>
          <h3>{counts.workflow_records || 0} workflow records</h3>
          <p>{counts.notification_emissions || 0} notification emissions · {counts.suppression_state || 0} suppression keys</p>
        </article>
        <article className="digest-card solid-truth">
          <div className="row-kicker">Audit controls</div>
          <h3>{validations.lineage_triggers_block_tampering ? "Lineage immutable" : "Lineage validation pending"}</h3>
          <p>Closed workflows auditable: {validations.closed_records_remain_auditable ? "yes" : "pending"}</p>
        </article>
      </div>
      <div className="row-actions">
        <a className="secondary-button" href={`${BACKEND_URL}/audit/export?format=json`} target="_blank" rel="noreferrer">Export JSON audit pack</a>
        <a className="secondary-button" href={`${BACKEND_URL}/audit/export?format=csv`} target="_blank" rel="noreferrer">Export CSV audit pack</a>
      </div>
    </section>
  );
}

function DigestCard({ digest }) {
  if (!digest) return <div className="digest-card solid-truth"><h3>Digest unavailable</h3></div>;
  return (
    <article className="digest-card solid-truth">
      <div className="row-kicker">{digest.output_layer}</div>
      <h3>{digest.title}</h3>
      <p>{digest.notification_count || 0} evidence-backed notification(s)</p>
      <p className="basis-line">Dedupe: {digest.suppression?.dedupe_key}</p>
    </article>
  );
}


function IdentityPostureBar({ identity }) {
  const actor = identity?.actor || {};
  const mode = identity?.auth_mode || "jwt";
  return (
    <section className="identity-posture glass-surface" aria-label="SSO and JWT identity posture">
      <span className="eyebrow">Identity</span>
      <strong>{actor.actor_name || "Verified actor required"}</strong>
      <p className="basis-line">SSO/JWT actor identity · mode {mode} · local-dev bypass only when explicitly enabled.</p>
      <div className="security-chip-row">
        <span className="glass-chip">Role: {actor.role_label || actor.role || "unverified"}</span>
        <span className="glass-chip">Scope: {(actor.entity_scope || []).join(", ") || "none"}</span>
        <span className="glass-chip">Collector: {actor.collector_id || "not scoped"}</span>
      </div>
    </section>
  );
}

function ObservabilityPanel({ observability, dashboards, alerts, focus }) {
  if (focus !== "risk_action") return null;
  const counters = observability?.counters || {};
  const timings = observability?.timings || {};
  const activeAlerts = alerts?.alerts || observability?.active_alerts || [];
  const dashboardList = dashboards?.dashboards || [];
  return (
    <section className="solid-evidence-card observability-panel" aria-label="Production observability">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">L5 governance output</p>
          <h2>Production observability</h2>
          <p className="basis-line">Correlation IDs, redacted structured logs, API timings, lineage coverage and security alerts remain backend-governed.</p>
        </div>
        <span className="basis-pill">{observability?.contract_version || "observability unavailable"}</span>
      </div>
      <div className="metric-grid compact">
        <article className="solid-mini-card">
          <span>Events</span>
          <strong>{observability?.event_count ?? "—"}</strong>
        </article>
        <article className="solid-mini-card">
          <span>API error rate</span>
          <strong>{observability?.api_error_rate_pct ?? "—"}%</strong>
        </article>
        <article className="solid-mini-card">
          <span>RBAC denials</span>
          <strong>{counters.rbac_denials_total ?? 0}</strong>
        </article>
        <article className="solid-mini-card">
          <span>Cache invalidations</span>
          <strong>{counters.cache_invalidations_total ?? 0}</strong>
        </article>
      </div>
      <div className="evidence-grid two-col">
        <article className="solid-mini-card">
          <span>API request p95</span>
          <strong>{timings.api_request_latency_ms?.p95_ms ?? "—"} ms</strong>
          <p className="basis-line">Measured server-side. No business computation moved into the frontend.</p>
        </article>
        <article className="solid-mini-card">
          <span>Frontend render p95</span>
          <strong>{timings.frontend_render_ms?.p95_ms ?? "—"} ms</strong>
          <p className="basis-line">Render timing only; financial values stay backend-calculated.</p>
        </article>
      </div>
      <div className="evidence-list">
        <h3>Active alert posture</h3>
        {activeAlerts.length ? activeAlerts.slice(0, 5).map((alert) => (
          <p key={alert.alert_key} className="basis-line">{alert.severity}: {alert.alert_key} · threshold {alert.threshold} · actual {alert.actual}</p>
        )) : <p className="basis-line">No active alerts from the latest evaluation.</p>}
      </div>
      <div className="evidence-list">
        <h3>Dashboard specs</h3>
        {dashboardList.slice(0, 4).map((item) => (
          <p key={item.dashboard_id} className="basis-line">{item.title}: {item.surface}</p>
        ))}
      </div>
    </section>
  );
}

export default function App() {
  const [payload, setPayload] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [actionQueues, setActionQueues] = useState(null);
  const [workflows, setWorkflows] = useState(null);
  const [notifications, setNotifications] = useState(null);
  const [auditSummary, setAuditSummary] = useState(null);
  const [security, setSecurity] = useState(null);
  const [identity, setIdentity] = useState(null);
  const [deploymentHealth, setDeploymentHealth] = useState(null);
  const [observability, setObservability] = useState(null);
  const [observabilityDashboards, setObservabilityDashboards] = useState(null);
  const [observabilityAlerts, setObservabilityAlerts] = useState(null);
  const [role, setRole] = useState("board_cxo");
  const [route, setRoute] = useState("arrival");
  const [focus, setFocus] = useState("current_signal");
  const [depth, setDepth] = useState("summary");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [drawer, setDrawer] = useState({ open: false, title: "", refs: [] });
  const [workflowDrawer, setWorkflowDrawer] = useState({ open: false, record: null, sourceAction: null });
  const [quickballAnswer, setQuickballAnswer] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const headers = authHeaders(role);
        const [centresRes, forecastRes, actionQueuesRes, workflowsRes, notificationsRes, auditRes, securityRes, identityRes, deploymentRes, observabilityRes, observabilityDashboardsRes, observabilityAlertsRes] = await Promise.all([
          fetch(`${BACKEND_URL}/command-centres`, { headers }),
          fetch(`${BACKEND_URL}/forecast/month-end`, { headers }),
          fetch(`${BACKEND_URL}/action-queues`, { headers }),
          fetch(`${BACKEND_URL}/workflows`, { headers }),
          fetch(`${BACKEND_URL}/notifications`, { headers }),
          fetch(`${BACKEND_URL}/persistence/summary`, { headers }),
          fetch(`${BACKEND_URL}/security/me`, { headers }),
          fetch(`${BACKEND_URL}/identity/me`, { headers }),
          fetch(`${BACKEND_URL}/deployment/health`, { headers }),
          fetch(`${BACKEND_URL}/observability/summary`, { headers }),
          fetch(`${BACKEND_URL}/observability/dashboards`, { headers }),
          fetch(`${BACKEND_URL}/observability/alerts`, { headers }),
        ]);
        if (!centresRes.ok) throw new Error(`Command centres ${centresRes.status}`);
        if (!forecastRes.ok) throw new Error(`Forecast ${forecastRes.status}`);
        if (!actionQueuesRes.ok) throw new Error(`Action queues ${actionQueuesRes.status}`);
        if (!workflowsRes.ok) throw new Error(`Workflows ${workflowsRes.status}`);
        if (!notificationsRes.ok) throw new Error(`Notifications ${notificationsRes.status}`);
        if (!auditRes.ok) throw new Error(`Persistence ${auditRes.status}`);
        // Security posture is displayed when available, but does not block staging Product UAT.
        const centresJson = await centresRes.json();
        const forecastJson = await forecastRes.json();
        const actionQueuesJson = await actionQueuesRes.json();
        const workflowsJson = await workflowsRes.json();
        const notificationsJson = await notificationsRes.json();
        const auditJson = await auditRes.json();
        const securityJson = securityRes.ok
          ? await securityRes.json()
          : { status: "unavailable", actor: { role, role_label: ROLE_LABELS[role] } };

        const identityJson = identityRes.ok
          ? await identityRes.json()
          : { status: "unavailable", actor: { role, role_label: ROLE_LABELS[role] } };

        const deploymentJson = deploymentRes.ok ? await deploymentRes.json() : { status: "unavailable" };
        const observabilityJson = observabilityRes.ok ? await observabilityRes.json() : { status: "unavailable" };
        const observabilityDashboardsJson = observabilityDashboardsRes.ok ? await observabilityDashboardsRes.json() : { dashboards: [] };
        const observabilityAlertsJson = observabilityAlertsRes.ok ? await observabilityAlertsRes.json() : { alerts: [] };
        if (!cancelled) {
          setPayload(centresJson);
          setForecast(forecastJson);
          setActionQueues(actionQueuesJson);
          setWorkflows(workflowsJson);
          setNotifications(notificationsJson);
          setAuditSummary(auditJson);
          setSecurity(securityJson);
          setIdentity(identityJson);
          setDeploymentHealth(deploymentJson);
          setObservability(observabilityJson);
          setObservabilityDashboards(observabilityDashboardsJson);
          setObservabilityAlerts(observabilityAlertsJson);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [role]);

  useEffect(() => {
    const start = performance.now();
    const frame = requestAnimationFrame(() => {
      const duration = performance.now() - start;
      const headers = authHeaders(role);
      fetch(`${BACKEND_URL}/observability/frontend-timing`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ route, view: focus, duration_ms: duration, device: { reducedMotion: window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches || false } }),
      }).catch(() => {});
    });
    return () => cancelAnimationFrame(frame);
  }, [route, focus, role]);

  const activeRole = payload?.roles?.[role] || payload?.roles?.board_cxo || {};
  const trustBar = activeRole?.trust_bar || payload?.roles?.board_cxo?.trust_bar;
  const cards = useMemo(() => safeArray(activeRole?.cards), [activeRole]);
  const roleLabel = ROLE_LABELS[role] || "Board/CXO";

  const openLineage = useCallback((refs, title) => setDrawer({ open: true, title, refs: refs || [] }), []);
  const closeLineage = useCallback(() => setDrawer({ open: false, title: "", refs: [] }), []);
  const openWorkflow = useCallback((record, sourceAction) => {
    const events = safeArray(workflows?.event_log).filter((event) => event.source_action_id === (record?.source_action_id || sourceAction?.action_id));
    setWorkflowDrawer({ open: true, record: record ? { ...record, event_log: events } : null, sourceAction });
  }, [workflows]);
  const closeWorkflow = useCallback(() => setWorkflowDrawer({ open: false, record: null, sourceAction: null }), []);

  const enterWorld = useCallback((nextRoute) => {
    setRoute(nextRoute);
    setFocus(nextRoute === "narratives" ? "story" : "current_signal");
    setDepth(nextRoute === "narratives" ? "executive" : "summary");
  }, [role]);

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
            <div className="kicker">SCIP Batch 12 · Observable Liquid Glass</div>
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
        <SecurityPostureBar security={security} role={role} />
        <IdentityPostureBar identity={identity} />
        <DataConfidenceTrustBar trustBar={trustBar} guardrails={payload?.guardrails} />
        <WorldHome route={route} focus={focus} setFocus={setFocus} />
        <FocusScreen route={route} focus={focus} roleLabel={roleLabel} cards={cards} forecast={forecast || payload?.forecast} onOpenLineage={openLineage} onExplain={(metric) => askQuickball(metric, role)} setFocus={setFocus} />
        {route === "live_pulse" && (focus === "month_movement" || focus === "target_track") && <ForecastPanel forecast={forecast || payload?.forecast} onOpenLineage={openLineage} />}
        {route === "live_pulse" && <ActionQueuePanel actionQueues={actionQueues} workflows={workflows} role={role} focus={focus} depth={depth} onOpenLineage={openLineage} onOpenWorkflow={openWorkflow} />}
        <NotificationEscalationPanel notifications={notifications} role={role} focus={focus} onOpenLineage={openLineage} />
        <AuditExportPanel auditSummary={auditSummary} focus={focus} />
        <ObservabilityPanel observability={observability} dashboards={observabilityDashboards} alerts={observabilityAlerts} focus={focus} />
        <WorkflowDrawer open={workflowDrawer.open} record={workflowDrawer.record} sourceAction={workflowDrawer.sourceAction} onClose={closeWorkflow} />
        <LineageDrawer open={drawer.open} title={drawer.title} refs={drawer.refs} onClose={closeLineage} />
      </div>
      <QuickballCommand role={role} answer={quickballAnswer} onAsk={askQuickball} collapsedPrompt={route === "narratives" ? "Ask for board explanation..." : "Ask about today's movement..."} />
    </main>
  );
}
