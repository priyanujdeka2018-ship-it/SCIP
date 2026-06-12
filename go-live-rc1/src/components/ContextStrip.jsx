/* SCIP ContextStrip — quiet meta line (no R-codes). Contract version comes
 * verbatim from /command-centres.contract_version. */
import { ROLE_LABELS } from "../api/client.js";
import { entityLabel } from "./Chrome.jsx";

const LIVE_PULSE_LABELS = {
  current_signal: "Current Signal",
  month_movement: "Month Movement",
  risk_action: "Risk & Action",
};

const NARRATIVE_LABELS = {
  story: "Story",
  portfolio: "Portfolio",
  dues: "Dues",
  advance: "Advance",
  roadmap: "Roadmap",
};

export default function ContextStrip({ route, focus, role, entity, contractVersion }) {
  const focusLabel = route === "narratives"
    ? (NARRATIVE_LABELS[focus] || "Story")
    : (LIVE_PULSE_LABELS[focus] || "Current Signal");
  return (
    <div className="context-strip glass--quiet" aria-label="Context">
      <span className="label">Reading</span>
      <span className="chip chip--accent">{focusLabel}</span>
      <span className="sep" />
      <span className="chip">{entityLabel(entity)}</span>
      <span className="sep" />
      <span className="chip">{ROLE_LABELS[role] || role}</span>
      <span style={{ flex: 1 }} />
      <span className="chip">
        <span className="dot dot--ok dot--pulse" /> Live{contractVersion ? ` · ${contractVersion}` : ""}
      </span>
    </div>
  );
}
