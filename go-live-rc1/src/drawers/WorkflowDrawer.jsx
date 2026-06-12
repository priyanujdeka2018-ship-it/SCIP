/* SCIP WorkflowDrawer — L5 action output.
 * State changes are SERVER operations (POST /workflows/*); the drawer never
 * mutates workflow state locally. Record fields, immutable event timeline and
 * lineage hashes render verbatim. Every action requires the source action's
 * lineage gate to have passed (enforced upstream and by the server again).
 */
import { useEffect, useMemo, useState } from "react";
import { safeArray } from "../contracts/guards.js";
import { workflowAssign, workflowClose, workflowDisposition, workflowDueDate, workflowEvidence, workflowReassign } from "../api/endpoints.js";
import { IconClose } from "../components/icons.jsx";

const ACTIONS = [
  { key: "reassign", label: "Reassign", run: (id, role) => workflowReassign({ action_id: id, assignee: "reassignment_review" }, { role }) },
  { key: "due-date", label: "Set due date (+7d)", run: (id, role) => workflowDueDate({ action_id: id, due_date: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10) }, { role }) },
  { key: "disposition", label: "Log PTP", run: (id, role) => workflowDisposition({ action_id: id, disposition: "promise_to_pay" }, { role }) },
  { key: "evidence", label: "Attach evidence ref", run: (id, role) => workflowEvidence({ action_id: id, evidence_type: "note", evidence_ref: "uat-evidence-ref" }, { role }) },
  { key: "close", label: "Close action", primary: true, run: (id, role) => workflowClose({ action_id: id, closure_reason: "resolved_in_uat_review" }, { role }) },
];

export default function WorkflowDrawer({ open, record: recordProp, sourceAction, role, eventLog, onClose, onOpenLineage }) {
  const [record, setRecord] = useState(recordProp);
  const [busy, setBusy] = useState(null);
  const [serverNote, setServerNote] = useState(null);

  useEffect(() => {
    setRecord(recordProp);
    setServerNote(null);
    setBusy(null);
  }, [recordProp, open]);

  useEffect(() => {
    if (!open) return undefined;
    function onKey(e) { if (e.key === "Escape") onClose(); }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const actionId = record?.source_action_id || sourceAction?.action_id;
  const timeline = useMemo(() => {
    const own = safeArray(record?.event_log || record?.events);
    if (own.length) return own;
    return safeArray(eventLog).filter((e) => e.source_action_id === actionId);
  }, [record, eventLog, actionId]);

  if (!open) return null;
  const source = record?.source_snapshot || sourceAction || {};
  const refs = safeArray(record?.immutable_lineage_refs).length
    ? record.immutable_lineage_refs
    : safeArray(sourceAction?.lineage_refs);

  async function run(action) {
    if (!actionId || busy) return;
    setBusy(action.key);
    setServerNote(null);
    try {
      const result = await action.run(actionId, role);
      if (result?.error || result?.status === "unavailable") {
        setServerNote({ tone: "warn", text: `Server declined: ${result.error || result.reason || "operation unavailable"}` });
      } else {
        const updated = result?.record || result;
        if (updated?.workflow_state) setRecord((r) => ({ ...(r || {}), ...updated }));
        setServerNote({ tone: "ok", text: `${action.label} posted — server event appended${updated?.workflow_state ? ` · state ${updated.workflow_state}` : ""}` });
      }
    } catch (err) {
      setServerNote({ tone: "warn", text: `Server error: ${err.message}` });
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <div className="scrim" onClick={onClose} aria-hidden="true" />
      <aside className="drawer workflow-drawer" role="dialog" aria-modal="true" aria-label="Workflow drawer">
        <div className="drawer-head">
          <div>
            <span className="eyebrow">L5 action output · Workflow</span>
            <h2 className="display h2 title">{record?.title || sourceAction?.title || "Workflow action"}</h2>
            <p className="sub">State changes are server operations with immutable lineage hashes. Source lineage is never mutated here.</p>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close drawer"><IconClose /></button>
        </div>
        <div className="drawer-body">
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <span className="workflow-pill">
              <span className="dot dot--ok dot--pulse" /> {(record?.workflow_state || "unavailable").replace("_", " ")}
            </span>
            <span className="chip">Due {record?.due_date || "not set"}</span>
            {refs.length > 0
              ? <span className="chip chip--accent"><span className="shield" /> Lineaged</span>
              : <span className="chip">Lineage unavailable</span>}
          </div>

          <div className="workflow-fields">
            <div className="workflow-field"><div className="k">Owner</div><div className="v">{record?.assigned_owner || source.collector_rm_owner || "Unavailable"}</div></div>
            <div className="workflow-field"><div className="k">Account</div><div className="v">{source.account_id || "Unavailable"}</div></div>
            <div className="workflow-field"><div className="k">Unit</div><div className="v">{source.unit || "Unavailable"}</div></div>
            <div className="workflow-field"><div className="k">Amount / status</div><div className="v">{source.display_amount || source.pr_status || "Unavailable"}</div></div>
            <div className="workflow-field"><div className="k">Basis</div><div className="v">{source.reporting_basis || sourceAction?.reporting_basis || "Unavailable"}</div></div>
            <div className="workflow-field"><div className="k">Ageing</div><div className="v">{source.ageing_bucket || "—"}</div></div>
          </div>

          {refs.length > 0 ? (
            <div className="workflow-actions">
              <span className="label">Allowed transitions · audit-logged on the server</span>
              {ACTIONS.map((a) => (
                <button
                  key={a.key}
                  className={`btn btn--sm ${a.primary ? "btn--primary" : "btn--ghost"}`}
                  disabled={!!busy || !record}
                  title={record ? undefined : "No workflow record loaded for this action"}
                  onClick={() => run(a)}
                >
                  {busy === a.key ? "…" : a.label}
                </button>
              ))}
              <button className="btn btn--sm btn--ghost" onClick={() => onOpenLineage(refs, record?.title || sourceAction?.title)}>Source evidence</button>
            </div>
          ) : (
            <div className="provenance solid" role="status">
              <span className="eyebrow eyebrow--mute"><span className="dot dot--warn" /> Actions blocked</span>
              <p className="small" style={{ marginTop: 8, color: "var(--text-mute)" }}>
                This action carries no complete lineage reference, so no workflow transition is offered (locked rule).
              </p>
            </div>
          )}

          {serverNote && (
            <div className="provenance solid edge-accent" role="status">
              <div className="eyebrow eyebrow--mute">Server response</div>
              <div className="small" style={{ marginTop: 6, color: serverNote.tone === "warn" ? "var(--status-warn)" : "var(--text)" }}>{serverNote.text}</div>
            </div>
          )}

          <div style={{ marginTop: 20 }}>
            <span className="eyebrow">Workflow timeline · immutable</span>
            <div className="timeline" style={{ marginTop: 14 }}>
              {timeline.length === 0 && (
                <div className="small" style={{ color: "var(--text-mute)" }}>No events loaded for this record.</div>
              )}
              {timeline.map((ev) => (
                <div key={ev.event_id} className="timeline-event done">
                  <div className="timeline-time">{ev.created_at || ""}</div>
                  <div className="timeline-bullet" />
                  <div className="timeline-content">
                    <div className="ttl">{ev.event_type} · {ev.from_state} → {ev.to_state}</div>
                    <div className="note">{ev.actor_role || ev.actor || ""} · hash {String(ev.lineage_hash || "").slice(0, 10)}…</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
