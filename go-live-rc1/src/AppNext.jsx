/**
 * SCIP — Liquid Glass rebuild shell (new UI).
 *
 * Thin shell only: providers + startup gate + chrome/screens/drawers as the
 * phases land. The legacy monolith stays reachable via ?legacy=1 (main.jsx);
 * the two module graphs and stylesheets never load together.
 */
import { useEffect, useState } from "react";
import "./styles/tokens.css";
import "./styles/glass.css";
import SessionProvider, { useSession } from "./state/SessionProvider.jsx";
import NavProvider from "./state/NavProvider.jsx";
import StartupDiagnostics from "./diagnostics/StartupDiagnostics.jsx";

const THEME = "navy";
const ACCENT = "gold";

function LoadingShell({ warming }) {
  return (
    <main className="arrival" aria-label="SCIP loading">
      <div className="arrival-inner">
        <div className="arrival-mark">S</div>
        <div className="eyebrow arrival-eyebrow">Sobha Collections Intelligence Platform</div>
        <h1 className="arrival-title display">Begin with the signal.</h1>
        <p className="arrival-sub">
          {warming
            ? `Sources warming · ${warming.stage || "loading"} · no figures are served until the lineage-backed payload is ready.`
            : "Connecting to the lineage-backed backend…"}
        </p>
        {warming?.state === "warmup_failed" && (
          <p className="arrival-sub" role="alert" style={{ color: "var(--status-warn)" }}>
            Source warmup failed: {warming.reason || "see /health"} · no values are shown.
          </p>
        )}
      </div>
    </main>
  );
}

function Shell() {
  const session = useSession();
  const { status, warming, diagnostic, contractProblems, role, retry } = session;

  if (status === "loading" || status === "warming") return <LoadingShell warming={warming} />;
  if (status === "error") {
    return <StartupDiagnostics diagnostic={diagnostic} contractProblems={contractProblems} role={role} onRetry={retry} />;
  }

  // Phase 2 replaces this with the real Arrival + worlds.
  return (
    <main className="arrival" aria-label="SCIP arrival">
      <div className="arrival-inner">
        <div className="arrival-mark">S</div>
        <div className="eyebrow arrival-eyebrow">Sobha Collections Intelligence Platform</div>
        <h1 className="arrival-title display">Begin with the signal.</h1>
        <p className="arrival-sub">Backend ready · {session.trustBar?.snapshot_date || "snapshot unavailable"}</p>
      </div>
    </main>
  );
}

export default function AppNext() {
  const [theme] = useState(THEME);
  const [accent] = useState(ACCENT);

  useEffect(() => {
    document.body.className = `scip-next theme-${theme} accent-${accent}`;
    return () => {
      document.body.className = "";
    };
  }, [theme, accent]);

  return (
    <div className={`scip-root theme-${theme} accent-${accent}`}>
      <SessionProvider>
        <NavProvider>
          <Shell />
        </NavProvider>
      </SessionProvider>
    </div>
  );
}
