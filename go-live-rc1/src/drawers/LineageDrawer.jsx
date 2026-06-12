/* SCIP LineageDrawer — evidence on request only (never inline by default).
 * Renders the critical-metric lineage contract VERBATIM from the server refs:
 * source file, sheet, cell/range, validation status, confidence state,
 * reporting basis, value. Fields the payload does not carry today
 * (per-metric snapshot date, lineage hash — accepted gap G6) render as
 * explicit unavailable rows, never guessed.
 */
import { useEffect } from "react";
import { LINEAGE_REF_FIELDS, lineageRefIsComplete, safeArray } from "../contracts/guards.js";
import { IconClose } from "../components/icons.jsx";

const G6_FIELDS = [
  ["snapshot_date", "Snapshot date"],
  ["lineage_hash", "Lineage ref / hash"],
];

function RefChain({ refData, index }) {
  const complete = lineageRefIsComplete(refData);
  const rows = [...LINEAGE_REF_FIELDS, ...G6_FIELDS];
  return (
    <div className="provenance solid" style={index > 0 ? { marginTop: 14 } : undefined}>
      <div className="provenance-metric">
        <span className={`dot ${complete ? "dot--trust" : "dot--warn"}`} />
        <span className="name">{refData.metric_key || "Metric"}</span>
        <span className="val num">{refData.value != null ? String(refData.value) : "—"}</span>
      </div>
      <div className="chain">
        {rows.map(([key, label], i) => {
          const value = refData[key];
          const present = value != null && value !== "";
          return (
            <div key={key} className={`chain-node ${present ? "verified" : ""}`}>
              <div className="chain-bullet">{String(i + 1).padStart(2, "0")}</div>
              <div className="chain-content">
                <div className="chain-label">{label}</div>
                <div className="chain-value">{present ? String(value) : "Unavailable"}</div>
                {present ? (
                  <div className="chain-status"><span className="dot dot--ok" /> Server-provided · verbatim</div>
                ) : (
                  <div className="chain-note">Not in this payload — no fallback shown{key === "lineage_hash" || key === "snapshot_date" ? " (contract gap G6)" : ""}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      {!complete && (
        <div className="small" style={{ marginTop: 10, color: "var(--status-warn)" }}>
          Lineage incomplete — this metric fails the critical-metric gate.
        </div>
      )}
    </div>
  );
}

export default function LineageDrawer({ open, refs, title, onClose }) {
  useEffect(() => {
    if (!open) return undefined;
    function onKey(e) { if (e.key === "Escape") onClose(); }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  const refList = safeArray(refs);

  return (
    <>
      <div className="scrim" onClick={onClose} aria-hidden="true" />
      <aside className="drawer" role="dialog" aria-modal="true" aria-label="Lineage drawer">
        <div className="drawer-head">
          <div>
            <span className="eyebrow">Evidence on request</span>
            <h2 className="display h2 title">{title || "Evidence"}</h2>
            <p className="sub">Source file, sheet, range, validation, confidence and reporting basis. Shown only after explicit ask.</p>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close drawer"><IconClose /></button>
        </div>
        <div className="drawer-body">
          {refList.length === 0 && (
            <div className="provenance solid">
              <span className="eyebrow eyebrow--mute"><span className="dot dot--warn" /> No lineage reference</span>
              <p className="small" style={{ marginTop: 10, color: "var(--text-mute)" }}>
                The server supplied no lineage reference for this item. Per the locked rule, no evidence is fabricated.
              </p>
            </div>
          )}
          {refList.map((refData, i) => (
            <RefChain key={`${refData.metric_key || "ref"}-${i}`} refData={refData} index={i} />
          ))}
        </div>
      </aside>
    </>
  );
}
