/* SCIP ActionQueues — Risk & Action / Roadmap L5 output.
 * Renders /action-queues.roles[role] verbatim: account, process and
 * management actions plus the server's blocked list. Locked rule: an item
 * renders its lineage refs or is shown blocked — never actionable without
 * lineage. Workflow buttons open the drawer with the matching /workflows
 * record (matched by source_action_id; matching is identity, not computation).
 */
import { useMemo } from "react";
import { safeArray, safeObject } from "../../contracts/guards.js";
import Unavailable from "../../components/Unavailable.jsx";

function QueueCard({ item, onOpenLineage, onOpenWorkflow, workflowRecord }) {
  const refs = safeArray(item.lineage_refs);
  const lineaged = refs.length > 0 && refs.every((ref) => ref.has_lineage !== false);
  const severity = item.severity === "risk" ? "risk" : item.severity === "warn" || item.severity === "attention" ? "warn" : "ok";
  return (
    <article className={`queue-card solid queue-card--${severity}`}>
      <div className="queue-meta">
        <span>{item.action_type || "action"}</span>
        <span className="sep" />
        <span>{item.entity_display || "entity unavailable"}</span>
      </div>
      <h3 className="queue-title">{item.title || "Untitled action"}</h3>
      <p className="queue-summary">{item.summary || ""}</p>
      <div className="queue-key">
        <div className="queue-key-item"><div className="k">Owner</div><div className="v">{item.collector_rm_owner || "Unavailable"}</div></div>
        <div className="queue-key-item"><div className="k">Amount</div><div className="v">{item.display_amount || "Unavailable"}</div></div>
        <div className="queue-key-item"><div className="k">Account</div><div className="v">{item.account_id || "—"}</div></div>
        <div className="queue-key-item"><div className="k">Ageing</div><div className="v">{item.ageing_bucket || item.pr_status || "—"}</div></div>
      </div>
      <div className="queue-foot">
        <span className="basis">Basis {item.reporting_basis || "unavailable"}</span>
        <div className="queue-actions">
          {lineaged ? (
            <>
              <button className="btn btn--sm btn--ghost" onClick={() => onOpenLineage(refs, item.title)}>Evidence</button>
              <button className="btn btn--sm btn--primary" onClick={() => onOpenWorkflow(workflowRecord, item)}>Workflow</button>
            </>
          ) : (
            <span className="chip" title="Locked rule: no unlineaged action is actionable">Blocked · lineage incomplete</span>
          )}
        </div>
      </div>
    </article>
  );
}

export default function ActionQueues({ session, onOpenLineage, onOpenWorkflow }) {
  const role = session.role;
  const queues = session.actionQueues;
  const queueRole = safeObject(queues?.roles)[role];
  const workflowByActionId = useMemo(() => {
    const records = safeArray(session.workflows?.records);
    return new Map(records.map((record) => [record.source_action_id, record]));
  }, [session.workflows]);

  if (!queues || !queueRole) {
    return (
      <section className="queue-section" data-anchor="action-queues" aria-label="Action queues">
        <div className="section-head">
          <div>
            <span className="eyebrow">Risk & Action · L5 output</span>
            <h2 className="display h2 title">No action queue for this role</h2>
            <p className="sub">The server returned no queue for this lens. No fallback actions are shown.</p>
          </div>
        </div>
      </section>
    );
  }

  const account = safeArray(queueRole.account_actions);
  const process = safeArray(queueRole.process_actions);
  const management = safeArray(queueRole.management_actions);
  const blocked = safeArray(queueRole.blocked_actions);
  const visible = [...account, ...process, ...management];
  const stateCounts = safeObject(session.workflows?.summary?.state_counts);

  return (
    <section className="queue-section" data-anchor="action-queues" aria-label="Action queues">
      <div className="section-head">
        <div>
          <span className="eyebrow">Risk & Action · L5 output</span>
          <h2 className="display h2 title">Action queues</h2>
          <p className="sub">{queueRole.headline || "Each card is gated by lineage and maps to a workflow record with an immutable event log."}</p>
          {(queueRole.disclosure || queues?.data_grain_disclosure?.rule) && (
            <p className="sub" style={{ marginTop: 6 }}>{queueRole.disclosure || queues.data_grain_disclosure.rule}</p>
          )}
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span className="chip chip--ok"><span className="dot dot--ok" /> {visible.length} from server</span>
          {stateCounts.queued != null && <span className="chip">{stateCounts.queued} queued</span>}
          {stateCounts.assigned != null && <span className="chip">{stateCounts.assigned} assigned</span>}
          {stateCounts.stale != null && <span className="chip">{stateCounts.stale} stale</span>}
        </div>
      </div>

      {visible.length === 0 && (
        <Unavailable reason="The server returned no actionable items for this role in this snapshot." />
      )}

      <div className="queue-grid">
        {visible.map((item) => (
          <QueueCard
            key={item.action_id}
            item={item}
            onOpenLineage={onOpenLineage}
            onOpenWorkflow={onOpenWorkflow}
            workflowRecord={workflowByActionId.get(item.action_id) || null}
          />
        ))}
      </div>

      {blocked.length > 0 && (
        <div style={{ marginTop: 18 }}>
          <span className="eyebrow eyebrow--mute">Blocked by the server's lineage gate</span>
          <div className="queue-grid" style={{ marginTop: 10 }}>
            {blocked.map((item) => (
              <article key={item.action_id} className="queue-card solid queue-card--warn">
                <div className="queue-meta"><span>{item.severity || "blocked"}</span></div>
                <h3 className="queue-title">{item.title || "Blocked action"}</h3>
                <p className="queue-summary">{item.blocked_reason || "Source lineage incomplete; the server blocked this action."}</p>
                <div className="queue-foot">
                  <span className="basis">Not actionable</span>
                  {safeArray(item.lineage_refs).length > 0 && (
                    <button className="btn btn--sm btn--ghost" onClick={() => onOpenLineage(item.lineage_refs, item.title)}>View source evidence</button>
                  )}
                </div>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
