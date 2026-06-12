/* SCIP Narratives — guided five-chapter briefing in LOCKED order:
 * Story → Portfolio → Dues → Advance → Roadmap.
 *
 * Accepted gap G3: no server narrative payload exists yet, so chapters render
 * as shells — the editorial title/lede/quote of the prototype is NOT shipped
 * as client prose. Each chapter shows its structural question plus stat slots
 * that resolve to verbatim server fields where a deterministic source exists
 * (metric-key card match or forecast display string); unresolved slots render
 * the shared Unavailable primitive. Basis labels come from the payload.
 */
import { safeArray, safeObject } from "../../contracts/guards.js";
import { cardByMetricKey } from "../../contracts/placement.js";
import CuriosityRail from "../../components/CuriosityRail.jsx";
import Unavailable from "../../components/Unavailable.jsx";
import { IconChevron } from "../../components/icons.jsx";

export const NARRATIVES = [
  { key: "story", num: "01", label: "Story", question: "What is the board-level story?", tone: "ok" },
  { key: "portfolio", num: "02", label: "Portfolio", question: "What is the portfolio position?", tone: "ok" },
  { key: "dues", num: "03", label: "Dues", question: "Where is OD / dues risk?", tone: "warn" },
  { key: "advance", num: "04", label: "Advance", question: "What is the advance opportunity?", tone: "ok" },
  { key: "roadmap", num: "05", label: "Roadmap", question: "What should leadership do next?", tone: "warn" },
];

/* Stat slots per chapter. `resolve` returns { val, delta } of verbatim server
 * strings, or null when the payload has no deterministic source (G3/G6). */
const CHAPTER_STATS = {
  story: [
    { label: "Projected landing", resolve: (s) => s.forecast?.status === "ok" && s.forecast.display?.projected_month_end_landing ? { val: s.forecast.display.projected_month_end_landing, delta: s.forecast.display.projected_achievement_pct || "", tone: "ok" } : null },
    { label: "MTD actual", resolve: (s) => s.forecast?.status === "ok" && s.forecast.display?.mtd_total_collections ? { val: s.forecast.display.mtd_total_collections, delta: "R04 Finance", tone: "ok" } : null },
    { label: "Month target", resolve: (s) => s.forecast?.status === "ok" && s.forecast.display?.may_total_collections_target ? { val: s.forecast.display.may_total_collections_target, delta: "R02 MDO", tone: "ok" } : null },
  ],
  portfolio: [
    { label: "Pipeline gross", resolve: (s) => fromCard(s, "PIPELINE_GROSS") },
    { label: "Group OD today", resolve: (s) => fromCard(s, "OD_TODAY") },
    { label: "Forward book", resolve: (s) => fromCard(s, "PIPELINE_FORWARD_BOOK") },
  ],
  dues: [
    { label: "Group OD today", resolve: (s) => fromCard(s, "OD_TODAY") },
    { label: "OD ageing pockets", resolve: () => null },
    { label: "Termination exposure", resolve: (s) => fromCard(s, "TERM_GAP_EXPOSURE") },
  ],
  advance: [
    { label: "CY advance mix", resolve: (s) => fromCard(s, "CY_ADV_MIX_YTD") },
    { label: "YTD advance", resolve: (s) => fromCard(s, "YTD_2026_ADVANCE") },
    { label: "Rebate-eligible", resolve: () => null },
  ],
  roadmap: [
    { label: "Actions from server", resolve: (s) => { const c = visibleActionCount(s); return c == null ? null : { val: String(c), delta: "this role lens", tone: c > 0 ? "warn" : "ok" }; } },
    { label: "Workflows queued", resolve: (s) => { const v = safeObject(s.workflows?.summary?.state_counts).queued; return v == null ? null : { val: String(v), delta: "workflow store", tone: "ok" }; } },
    { label: "Required run-rate", resolve: (s) => s.forecast?.status === "ok" && s.forecast.display?.required_daily_run_rate_remaining ? { val: s.forecast.display.required_daily_run_rate_remaining, delta: "remaining working days", tone: "warn" } : null },
  ],
};

function fromCard(session, metricKey) {
  const card = cardByMetricKey(session.cards, metricKey);
  if (!card || card.display_value == null) return null;
  return { val: card.display_value, delta: card.reporting_basis || "", tone: card.severity === "risk" ? "risk" : card.severity === "warn" ? "warn" : "ok" };
}

function visibleActionCount(session) {
  const queueRole = safeObject(session.actionQueues?.roles)[session.role];
  if (!queueRole) return null;
  return safeArray(queueRole.account_actions).length + safeArray(queueRole.process_actions).length + safeArray(queueRole.management_actions).length;
}

export function NarrativesHome({ focus, setFocus, onPresent }) {
  return (
    <section className="world-hero glass" aria-label="Narratives home">
      <div className="world-hero-meta">
        <span className="eyebrow">Narratives</span>
        <span className="small" style={{ color: "var(--text-mute)" }}>A guided five-chapter briefing</span>
        <span style={{ flex: 1 }} />
        <button className="btn btn--primary" onClick={onPresent}>
          <span style={{ display: "inline-flex", width: 0, height: 0, borderTop: "5px solid transparent", borderBottom: "5px solid transparent", borderLeft: "8px solid currentColor" }} />
          Present
        </button>
      </div>
      <h2 className="world-hero-title display h2">A boardroom journey, not a dashboard menu.</h2>
      <p className="world-hero-sub body-lg">
        Move through Story, Portfolio, Dues, Advance and Roadmap. Evidence stays one click deeper — the surface remains calm.
      </p>
      <nav className="narrative-rail" aria-label="Narrative steps">
        {NARRATIVES.map((n) => (
          <button key={n.key} aria-current={focus === n.key ? "step" : undefined} onClick={() => setFocus(n.key)}>
            <span className="num">{n.num}</span>{n.label}
          </button>
        ))}
      </nav>
    </section>
  );
}

export function NarrativeChapter({ focus, setFocus, session, onOpenLineage, onAskQuickball }) {
  const n = NARRATIVES.find((s) => s.key === focus) || NARRATIVES[0];
  const idx = NARRATIVES.indexOf(n);
  const prev = idx > 0 ? NARRATIVES[idx - 1] : null;
  const next = idx < NARRATIVES.length - 1 ? NARRATIVES[idx + 1] : null;
  const stats = (CHAPTER_STATS[n.key] || []).map((slot) => ({ label: slot.label, value: slot.resolve(session) }));
  const heroCard = cardByMetricKey(session.cards, "OD_TODAY");

  return (
    <section className="story glass" aria-label="Narrative chapter">
      <div className={`focus-poster focus-poster--${n.tone || "ok"}`} aria-hidden="true" style={{ opacity: 0.4 }} />
      <span className="story-num">CHAPTER {n.num} · {n.label.toUpperCase()}</span>
      <h2 className="story-title display h1">{n.question}</h2>
      <div style={{ marginTop: 14, maxWidth: 660 }}>
        <Unavailable
          reason="Narrative editorial is not yet server-provided (contract gap G3). Chapter figures below are verbatim server values; no prose is invented."
          confidence="unavailable"
        />
      </div>

      <div className="story-stats">
        {stats.map((s) => (
          <div key={s.label} className="story-stat solid">
            <div className="label">{s.label}</div>
            {s.value ? (
              <>
                <div className="val num">{s.value.val}</div>
                <div className={`delta ${s.value.tone}`}>{s.value.delta}</div>
              </>
            ) : (
              <div style={{ marginTop: 6 }}><Unavailable compact reason="No deterministic server source for this slot yet" /></div>
            )}
          </div>
        ))}
      </div>

      <CuriosityRail
        items={[
          { k: "evidence", label: "Show evidence" },
          { k: "ask", label: "Ask Quickball" },
          { k: "next", label: `Continue to ${next ? next.label : "—"} →` },
        ]}
        onChoose={(k) => {
          if (k === "evidence") {
            const refs = safeArray(heroCard?.lineage_display).length ? heroCard.lineage_display : safeArray(heroCard?.lineage_refs);
            onOpenLineage(refs, n.label);
          } else if (k === "ask") {
            onAskQuickball("OD_TODAY");
          } else if (k === "next" && next) {
            setFocus(next.key);
          }
        }}
      />

      <div className="story-nav">
        <button className="btn btn--ghost" disabled={!prev} onClick={() => prev && setFocus(prev.key)}>
          <IconChevron dir="left" /> {prev ? prev.label : "Start"}
        </button>
        <button className="btn btn--primary" disabled={!next} onClick={() => next && setFocus(next.key)}>
          {next ? next.label : "End"} <IconChevron />
        </button>
      </div>
    </section>
  );
}
