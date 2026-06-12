/* SCIP TrustRail — calm bottom strip; details on click.
 * Per accepted gap G1 there is NO posture claim and no client-derived
 * "all verified" statement: every field below is verbatim from
 * roles[role].trust_bar. Missing fields render as unavailable.
 */
import { useState } from "react";
import { safeArray } from "../contracts/guards.js";
import { IconChevron } from "./icons.jsx";

export default function TrustRail({ trustBar, contractVersion }) {
  const [open, setOpen] = useState(false);
  const t = trustBar || {};
  const loaded = safeArray(t.sources_loaded);
  const missing = safeArray(t.sources_missing);
  const lineageCounts = t.critical_lineage_counts || {};

  return (
    <div className="trust-rail glass--quiet" aria-label="Data trust posture">
      <div className="group">
        <span className="dot dot--trust dot--pulse" />
        <span style={{ color: "var(--text)" }}>
          Lineage · {loaded.length} sources loaded{missing.length ? ` · ${missing.length} missing` : ""}
        </span>
      </div>
      <div className="group">
        <span>Snapshot {t.snapshot_date || "unavailable"}</span>
        <span style={{ color: "var(--text-faint)" }}>·</span>
        <span>Tolerance {t.tolerance_pct != null ? `${t.tolerance_pct}%` : "unavailable"}</span>
        <button
          className="btn btn--sm btn--ghost"
          style={{ height: 26, padding: "0 11px", fontSize: 11, letterSpacing: "0.06em" }}
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
        >
          {open ? "Hide" : "Details"} <IconChevron dir={open ? "up" : "down"} size={10} />
        </button>
      </div>
      {open && (
        <div className="trust-details" role="region" aria-label="Source manifest">
          <div className="trust-details-grid">
            <div>
              <div className="trust-details-label">Snapshot</div>
              <div className="trust-details-val">{t.snapshot_date || "unavailable"}{t.load_timestamp ? ` · ${t.load_timestamp}` : ""}</div>
            </div>
            <div>
              <div className="trust-details-label">Contract</div>
              <div className="trust-details-val">{contractVersion || "unavailable"}</div>
            </div>
            <div>
              <div className="trust-details-label">Sources lineaged</div>
              <div className="trust-details-val">{loaded.length} of {loaded.length + missing.length}</div>
            </div>
            <div>
              <div className="trust-details-label">Tolerance</div>
              <div className="trust-details-val">{t.tolerance_pct != null ? `${t.tolerance_pct}% locked` : "unavailable"}</div>
            </div>
          </div>
          <div style={{ marginTop: 14, display: "flex", flexWrap: "wrap", gap: 6 }}>
            {loaded.map((s) => (
              <span key={s} className="pill ok">
                {s}{lineageCounts[s] != null ? ` · ${lineageCounts[s]}` : ""}
              </span>
            ))}
            {missing.map((s) => <span key={s} className="pill warn">{s} missing</span>)}
          </div>
        </div>
      )}
    </div>
  );
}
