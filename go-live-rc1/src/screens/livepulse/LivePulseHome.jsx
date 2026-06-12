/* SCIP Live Pulse home — exactly three choices (locked count).
 * Per accepted gap G4 the role-scoped door copy is not server-provided yet,
 * so the doors use neutral fixed copy; the metric chip on each door is shown
 * ONLY when a confidently-mapped server value exists, otherwise it renders
 * an unavailable chip. No value is ever computed client-side; the action
 * count states how many actions the server sent for this role.
 */
import { useMemo } from "react";
import { safeArray, safeObject } from "../../contracts/guards.js";
import { cardByMetricKey } from "../../contracts/placement.js";

const CHOICES = [
  {
    key: "current_signal",
    eyebrow: "Are we okay today?",
    title: "Current Signal",
    desc: "A calm reading of what needs attention now, anchored on OD, collections and confidence.",
  },
  {
    key: "month_movement",
    eyebrow: "How is the month moving?",
    title: "Month Movement",
    desc: "MTD movement, run-rate and target gap. The forecast discloses its basis.",
  },
  {
    key: "risk_action",
    eyebrow: "Where should we act?",
    title: "Risk & Action",
    desc: "Lineaged action queues with owners, due dates and immutable workflow events.",
  },
];

export default function LivePulseHome({ focus, setFocus, session }) {
  const metrics = useMemo(() => {
    const odCard = cardByMetricKey(session.cards, "OD_TODAY");
    const forecast = session.forecast;
    const queueRole = safeObject(session.actionQueues?.roles)[session.role];
    const actionCount = queueRole
      ? safeArray(queueRole.account_actions).length + safeArray(queueRole.process_actions).length + safeArray(queueRole.management_actions).length
      : null;
    return {
      current_signal: odCard?.display_value
        ? { metric: odCard.display_value, unit: odCard.reporting_basis || "", severity: odCard.severity }
        : null,
      month_movement: forecast?.status === "ok" && forecast?.display?.projected_achievement_pct
        ? { metric: forecast.display.projected_achievement_pct, unit: "projected achievement", severity: "ok" }
        : null,
      risk_action: actionCount != null
        ? { metric: String(actionCount), unit: "actions from server", severity: actionCount > 0 ? "warn" : "ok" }
        : null,
    };
  }, [session.cards, session.forecast, session.actionQueues, session.role]);

  return (
    <section className="world-hero glass" aria-label="Live Pulse home">
      <div className="world-hero-meta">
        <span className="eyebrow">Live Pulse</span>
        <span className="dot dot--ok dot--pulse" />
        <span className="small" style={{ color: "var(--text-mute)" }}>
          Backend live{session.trustBar?.load_timestamp ? ` · ${session.trustBar.load_timestamp}` : ""}
        </span>
      </div>
      <h2 className="world-hero-title display h2">Three choices. One signal at a time.</h2>
      <p className="world-hero-sub body-lg">Doors adapt to your lens — the count stays three by design. Deeper lenses remain follow-ups, never a fourth door.</p>

      <div className="choices">
        {CHOICES.map((c) => {
          const m = metrics[c.key];
          const sevDot = m?.severity === "risk" ? "dot--risk" : m?.severity === "warn" ? "dot--warn" : "dot--ok";
          return (
            <button key={c.key} className="choice glass--quiet" aria-pressed={focus === c.key} onClick={() => setFocus(c.key)}>
              <span className="eyebrow choice-q">{c.eyebrow}</span>
              <h3 className="choice-title">{c.title}</h3>
              <p className="choice-desc">{c.desc}</p>
              <div className="choice-foot">
                <span className="eyebrow eyebrow--mute"><span className={`dot ${sevDot}`} /> Read</span>
                <div className="right">
                  {m ? (
                    <>
                      <div className="choice-metric">{m.metric}</div>
                      <div className="choice-metric-unit">{m.unit}</div>
                    </>
                  ) : (
                    <div className="choice-metric-unit">value unavailable</div>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
