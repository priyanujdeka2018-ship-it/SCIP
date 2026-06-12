/* SCIP Arrival — exactly two doors (locked). Layout/copy ported from the
 * prototype; the footer facts are verbatim server trust fields. */
import { safeArray } from "../contracts/guards.js";
import { IconBook, IconChevron, IconPulse } from "../components/icons.jsx";

export default function Arrival({ onEnter, trustBar, contractVersion }) {
  const t = trustBar || {};
  const loaded = safeArray(t.sources_loaded);
  return (
    <main className="arrival" aria-label="SCIP arrival">
      <div className="arrival-inner">
        <div className="arrival-mark">S</div>
        <div className="eyebrow arrival-eyebrow">Sobha Collections Intelligence Platform</div>
        <h1 className="arrival-title display">Begin with the signal.</h1>
        <p className="arrival-sub">
          An intelligent briefing that can go as deep as you ask. Two doors. No dashboards waiting for you.
        </p>

        <div className="doors" aria-label="Primary entry choices">
          <button className="door glass edge-accent" onClick={() => onEnter("live_pulse")}>
            <div className="door-poster door-poster--pulse" aria-hidden="true" />
            <div className="door-top">
              <div className="door-icon"><IconPulse size={18} /></div>
              <div className="door-meta">Door 01 · Operational</div>
            </div>
            <div className="door-spacer" />
            <h2 className="door-title">Live Pulse</h2>
            <p className="door-desc">What needs attention today. Current signal, month movement, risk and action — three doors, no menus.</p>
            <div className="door-cta">Enter Live Pulse <span className="arrow"><IconChevron size={14} /></span></div>
          </button>

          <button className="door glass" onClick={() => onEnter("narratives")}>
            <div className="door-poster door-poster--narr" aria-hidden="true" />
            <div className="door-top">
              <div className="door-icon"><IconBook size={18} /></div>
              <div className="door-meta">Door 02 · Executive</div>
            </div>
            <div className="door-spacer" />
            <h2 className="door-title">Narratives</h2>
            <p className="door-desc">The story behind the numbers. A guided five-chapter briefing — Story, Portfolio, Dues, Advance, Roadmap.</p>
            <div className="door-cta">Enter Narratives <span className="arrow"><IconChevron size={14} /></span></div>
          </button>
        </div>

        <div className="arrival-foot">
          <span>Data {t.snapshot_date || "unavailable"}</span>
          <span className="sep" />
          <span>{t.load_timestamp || "load time unavailable"}</span>
          <span className="sep" />
          <span>{loaded.length} sources lineaged</span>
          <span className="sep" />
          <span>Contract {contractVersion || "unavailable"}</span>
        </div>
      </div>
    </main>
  );
}
