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
import Tile from "./components/Tile.jsx";
import Arrival from "./screens/Arrival.jsx";
import LivePulseHome from "./screens/livepulse/LivePulseHome.jsx";
import FocusScreen from "./screens/livepulse/FocusScreen.jsx";
import RunwayPanel from "./screens/livepulse/RunwayPanel.jsx";
import ActionQueues from "./screens/livepulse/ActionQueues.jsx";
import { NarrativesHome, NarrativeChapter } from "./screens/narratives/Narratives.jsx";
import Quickball from "./quickball/Quickball.jsx";
import LineageDrawer from "./drawers/LineageDrawer.jsx";
import WorkflowDrawer from "./drawers/WorkflowDrawer.jsx";
import { ROLE_LABELS } from "./api/client.js";

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

      {nav.route === "live_pulse" && (
        <>
          <LivePulseHome focus={nav.focus} setFocus={nav.setFocus} session={session} />
          <FocusScreen
            focus={nav.focus}
            setFocus={nav.setFocus}
            session={session}
            onOpenLineage={nav.openLineage}
            onAskQuickball={nav.askQuickball}
          />
          {nav.focus === "month_movement" && (
            <RunwayPanel forecast={session.forecast} onOpenLineage={nav.openLineage} />
          )}
          <section aria-label="Lineaged command tiles" style={{ marginTop: 4 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 14 }}>
              <div>
                <span className="eyebrow">Lineaged tiles · {ROLE_LABELS[session.role] || session.role}</span>
                <h3 className="display h3" style={{ marginTop: 6 }}>The numbers that earn their place.</h3>
              </div>
              <span className="chip">Tap a tile for evidence</span>
            </div>
            <div className="tiles">
              {session.cards.map((card) => (
                <Tile key={card.card_id || card.title} card={card} onOpenLineage={nav.openLineage} />
              ))}
            </div>
          </section>
          {nav.focus === "risk_action" && (
            <ActionQueues session={session} onOpenLineage={nav.openLineage} onOpenWorkflow={nav.openWorkflow} />
          )}
        </>
      )}

      {nav.route === "narratives" && (
        <>
          <NarrativesHome focus={nav.focus} setFocus={nav.setFocus} onPresent={() => nav.setPresent(true)} />
          <NarrativeChapter
            focus={nav.focus}
            setFocus={nav.setFocus}
            session={session}
            onOpenLineage={nav.openLineage}
            onAskQuickball={nav.askQuickball}
          />
          {nav.focus === "roadmap" && (
            <ActionQueues session={session} onOpenLineage={nav.openLineage} onOpenWorkflow={nav.openWorkflow} />
          )}
        </>
      )}

      <TrustRail trustBar={session.trustBar} contractVersion={session.contractVersion} />

      <Quickball role={session.role} visible={true} />

      <LineageDrawer open={nav.lineage.open} refs={nav.lineage.refs} title={nav.lineage.title} onClose={nav.closeLineage} />
      <WorkflowDrawer
        open={nav.workflow.open}
        record={nav.workflow.record}
        sourceAction={nav.workflow.sourceAction}
        role={session.role}
        eventLog={session.workflows?.event_log}
        onClose={nav.closeWorkflow}
        onOpenLineage={nav.openLineage}
      />
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
