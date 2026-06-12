/**
 * SCIP — Liquid Glass rebuild shell (new UI).
 *
 * Phase 0: scaffold only. Applies the locked token/theme system and renders
 * an empty Arrival frame with zero data dependency. The legacy monolith stays
 * reachable via ?legacy=1 (see main.jsx); its module graph and CSS never load
 * when this shell is active, and vice versa.
 */
import { useEffect } from "react";
import "./styles/tokens.css";
import "./styles/glass.css";

const THEME = "navy";
const ACCENT = "gold";

export default function AppNext() {
  useEffect(() => {
    document.body.className = `scip-next theme-${THEME} accent-${ACCENT}`;
    return () => {
      document.body.className = "";
    };
  }, []);

  return (
    <div className={`scip-root theme-${THEME} accent-${ACCENT}`} data-screen-label="01 Arrival">
      <main className="arrival" aria-label="SCIP arrival">
        <div className="arrival-inner">
          <div className="arrival-mark">S</div>
          <div className="eyebrow arrival-eyebrow">Sobha Collections Intelligence Platform</div>
          <h1 className="arrival-title display">Begin with the signal.</h1>
          <p className="arrival-sub">
            An intelligent briefing that can go as deep as you ask. Two doors. No dashboards waiting for you.
          </p>
        </div>
      </main>
    </div>
  );
}
