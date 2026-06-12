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
import NavProvider, { useNav } from "./state/NavProvider.jsx";
import StartupDiagnostics from "./diagnostics/StartupDiagnostics.jsx";
import Chrome from "./components/Chrome.jsx";
import ContextStrip from "./components/ContextStrip.jsx";
import TrustRail from "./components/TrustRail.jsx";
import Arrival from "./screens/Arrival.jsx";

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
  const nav = useNav();
  const { status, warming, diagnostic, contractProblems, role, retry } = session;

  if (status === "loading" || status === "warming") return <LoadingShell warming={warming} />;
  if (status === "error") {
    return <StartupDiagnostics diagnostic={diagnostic} contractProblems={contractProblems} role={role} onRetry={retry} />;
  }

  if (nav.route === "arrival") {
    return <Arrival onEnter={nav.enterWorld} trustBar={session.trustBar} contractVersion={session.contractVersion} />;
  }

  return (
    <main className="page">
      <Chrome
        route={nav.route}
        setRoute={(r) => (r === "arrival" ? nav.setRoute("arrival") : nav.enterWorld(r))}
        role={session.role}
        setRole={session.setRole}
        roleKeys={session.roleKeys}
        entity={session.entity}
        setEntity={session.setEntity}
        dataDate={session.trustBar?.snapshot_date}
        loadTimestamp={session.trustBar?.load_timestamp}
      />
      <ContextStrip route={nav.route} focus={nav.focus} role={session.role} entity={session.entity} contractVersion={session.contractVersion} />
      {session.roleRefreshing && (
        <div className="context-strip glass--quiet" role="status" aria-label="Role refresh">
          <span className="chip"><span className="dot dot--ok dot--pulse" /> Refreshing role lens…</span>
        </div>
      )}

      {/* Worlds land in Phase 3 (Live Pulse) and Phase 4 (Narratives). */}

      <TrustRail trustBar={session.trustBar} contractVersion={session.contractVersion} />
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
