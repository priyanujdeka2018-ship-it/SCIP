/**
 * SCIP staging diagnostics panel (UAT hardening behavior, preserved).
 * Shown when a blocking endpoint fails at startup: backend URL, endpoint,
 * failure class/status, role, bypass mode, correlation id — plus any
 * contract-guard problems. Hidden before production polish (hardening notes).
 */
import { BACKEND_URL, LOCAL_DEV_BYPASS } from "../api/client.js";

export default function StartupDiagnostics({ diagnostic, contractProblems = [], role, onRetry }) {
  const d = diagnostic || {};
  return (
    <main className="arrival" aria-label="SCIP startup diagnostics" role="alert">
      <div className="arrival-inner" style={{ maxWidth: 720 }}>
        <div className="arrival-mark">S</div>
        <div className="eyebrow arrival-eyebrow">Staging UAT diagnostic</div>
        <h1 className="display h2" style={{ marginTop: 10 }}>SCIP could not load a required surface.</h1>
        <p className="arrival-sub" style={{ marginTop: 10 }}>
          No fallback figures are shown. Backend data must be live and lineaged.
        </p>
        <div className="solid" style={{ textAlign: "left", marginTop: 22, padding: 18, borderRadius: "var(--r-md)", border: "1px solid var(--line-strong)" }}>
          <div className="mono small" style={{ display: "grid", gridTemplateColumns: "150px 1fr", rowGap: 8, columnGap: 14 }}>
            <span style={{ color: "var(--text-mute)" }}>Classification</span><span>{d.classification || "required-core-endpoint"}</span>
            <span style={{ color: "var(--text-mute)" }}>Backend URL</span><span>{d.backendUrl || BACKEND_URL}</span>
            <span style={{ color: "var(--text-mute)" }}>Endpoint</span><span>{d.endpoint || "not captured"}</span>
            <span style={{ color: "var(--text-mute)" }}>Status</span><span style={{ overflowWrap: "anywhere" }}>{d.status || "unknown"}</span>
            <span style={{ color: "var(--text-mute)" }}>Role</span><span>{d.role || role}</span>
            <span style={{ color: "var(--text-mute)" }}>Bypass</span><span>{(d.bypass ?? LOCAL_DEV_BYPASS) ? "staging local-dev bypass" : "jwt"}</span>
            <span style={{ color: "var(--text-mute)" }}>Correlation</span><span>{d.correlationId || "per-request"}</span>
          </div>
          {contractProblems.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <div className="eyebrow eyebrow--mute">Contract drift observed</div>
              <ul className="mono small" style={{ marginTop: 8, paddingLeft: 18 }}>
                {contractProblems.map((p) => <li key={p}>{p}</li>)}
              </ul>
            </div>
          )}
        </div>
        {onRetry && (
          <button className="btn btn--primary" style={{ marginTop: 20 }} onClick={onRetry}>Retry startup</button>
        )}
      </div>
    </main>
  );
}
