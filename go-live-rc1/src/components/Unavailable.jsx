/**
 * SCIP shared unavailable-state primitive. The ONLY way any surface renders
 * a missing value: explicit, labelled, never a blank, never a zero, never a
 * fabricated figure. (Locked rule: no silent fallback.)
 */
export default function Unavailable({ reason, confidence = "unavailable", compact = false }) {
  if (compact) {
    return (
      <span className="chip" data-confidence={confidence} title={reason || "No lineaged value from the server"}>
        Unavailable
      </span>
    );
  }
  return (
    <div className="solid" data-confidence={confidence} role="status"
      style={{ padding: "14px 16px", borderRadius: "var(--r-sm)", border: "1px solid var(--line-strong)" }}>
      <div className="eyebrow eyebrow--mute">
        <span className="dot dot--warn" /> Unavailable · {confidence}
      </div>
      <div className="small" style={{ marginTop: 6, color: "var(--text-mute)" }}>
        {reason || "The server did not provide this value. No fallback figure is shown."}
      </div>
    </div>
  );
}
