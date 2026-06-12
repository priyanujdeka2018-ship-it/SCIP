/* SCIP Live Pulse focus screen.
 * Per accepted gap G2 the figure-bearing editorial prose is NOT rendered
 * (no server carrier yet): the screen keeps the structural question, then
 * leads with the hero figure — a verbatim server card (or forecast display
 * field for Month Movement) — and side tiles from the same payload.
 * Card selection per accepted gap G5 (labelled heuristic).
 */
import { useMemo } from "react";
import { safeArray } from "../../contracts/guards.js";
import { cardsForFocus, PLACEMENT_MODE } from "../../contracts/placement.js";
import CuriosityRail from "../../components/CuriosityRail.jsx";
import Unavailable from "../../components/Unavailable.jsx";

const FOCUS_META = {
  current_signal: { question: "Are we okay today?", poster: "ok" },
  month_movement: { question: "How is the month moving?", poster: "warn" },
  risk_action: { question: "Where should we act?", poster: "risk" },
};

export default function FocusScreen({ focus, setFocus, session, onOpenLineage, onAskQuickball }) {
  const meta = FOCUS_META[focus] || FOCUS_META.current_signal;
  const selected = useMemo(() => cardsForFocus(session.cards, focus, 4), [session.cards, focus]);
  const hero = selected[0] || null;
  const side = selected.slice(1, 3);
  const heroRefs = hero ? (safeArray(hero.lineage_display).length ? hero.lineage_display : safeArray(hero.lineage_refs)) : [];
  const heroMetricKey = heroRefs[0]?.metric_key;

  const curiosities = focus === "current_signal" ? [
    { k: "show_evidence", label: "Show source evidence" },
    { k: "ask", label: "Ask about this number" },
    { k: "open_runway", label: "Open Month Movement →" },
  ] : focus === "month_movement" ? [
    { k: "show_evidence", label: "Show forecast lineage" },
    { k: "ask", label: "Ask about the run-rate" },
    { k: "what_should_we_do", label: "What should we do? →" },
  ] : [
    { k: "show_evidence", label: "Show action lineage" },
    { k: "ask", label: "Ask about a risk pocket" },
    { k: "open_queues", label: "Open action queues ↓" },
  ];

  function handleCuriosity(k) {
    if (k === "show_evidence") {
      if (focus === "month_movement" && session.forecast?.lineage_refs) {
        onOpenLineage(session.forecast.lineage_refs, "Forecast lineage");
      } else {
        onOpenLineage(heroRefs, hero?.title || "Evidence");
      }
    } else if (k === "ask") {
      onAskQuickball(heroMetricKey || "OD_TODAY");
    } else if (k === "open_runway") {
      setFocus("month_movement");
    } else if (k === "what_should_we_do") {
      setFocus("risk_action");
    } else if (k === "open_queues") {
      const el = document.querySelector("[data-anchor=action-queues]");
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  return (
    <section className="focus glass" aria-label="Focus screen">
      <div className={`focus-poster focus-poster--${meta.poster}`} aria-hidden="true" />
      <span className="eyebrow">Live · {session.trustBar?.snapshot_date || "snapshot unavailable"}</span>
      <p className="focus-q small" style={{ marginTop: 14 }}>{meta.question}</p>

      <div className="hero-numeric" style={{ marginTop: 18 }}>
        <div className="hero-figure solid edge-accent">
          <div className="hero-figure-top">
            <span className="eyebrow">{hero?.title || "Primary figure"}</span>
            {heroRefs.length > 0 && heroRefs.every((r) => r.has_lineage !== false)
              ? <span className="chip chip--accent"><span className="shield" /> Lineaged</span>
              : <span className="chip">Lineage warning</span>}
          </div>
          <div>
            {hero?.display_value != null
              ? <div className="hero-figure-value num">{hero.display_value}</div>
              : <Unavailable reason="No server card mapped to this focus carries a display value" />}
            <div className="hero-figure-cap">{hero?.reporting_basis || "basis unavailable"}</div>
          </div>
        </div>
        <div className="hero-side">
          {side.length === 0 && <Unavailable reason="No further server cards for this focus" />}
          {side.map((card) => (
            <div key={card.card_id || card.title} className="hero-side-tile solid">
              <div>
                <div className="label">{card.title}</div>
                <div className="val">{card.display_value != null ? card.display_value : "Unavailable"}</div>
              </div>
              <div className="basis">{card.reporting_basis || "basis unavailable"}</div>
            </div>
          ))}
        </div>
      </div>

      {hero?.basis_disclosure && <p className="focus-copy" style={{ marginTop: 14 }}>{hero.basis_disclosure}</p>}

      <CuriosityRail items={curiosities} onChoose={handleCuriosity} />
      <div className="small mono" style={{ marginTop: 10, color: "var(--text-faint)" }} title="Accepted gap G5">
        placement: {PLACEMENT_MODE}
      </div>
    </section>
  );
}
