/* SCIP RunwayPanel — month-end landing forecast (Month Movement only).
 * Every figure shown is a verbatim string from forecast.display.*; basis and
 * assumptions come from the payload. Per accepted gap G12 the track geometry
 * positions markers from server-provided working-day integers and the
 * server's projected achievement percentage — pure chart rendering; no
 * financial value is created client-side. Blocked forecasts render the
 * server's reason, never a fallback.
 */
import { safeArray } from "../../contracts/guards.js";

function pct(numerator, denominator) {
  const n = Number(numerator);
  const d = Number(denominator);
  if (!Number.isFinite(n) || !Number.isFinite(d) || d <= 0) return null;
  return Math.max(0, Math.min(100, (n / d) * 100));
}

export default function RunwayPanel({ forecast, onOpenLineage, layout = "default" }) {
  const layoutClass = `runway-panel glass edge-accent layout-${layout}`;

  if (!forecast || forecast.status !== "ok") {
    return (
      <section className={layoutClass} aria-label="Month-end runway blocked" role="alert">
        <div className="runway-head">
          <div>
            <span className="eyebrow">Month-end landing forecast</span>
            <h2 className="display h3 title">Forecast blocked — no fallback shown.</h2>
            <p className="sub">{forecast?.reason || "The backend did not return a trusted forecast. No figures are invented."}</p>
          </div>
        </div>
        {safeArray(forecast?.lineage_refs).length > 0 && (
          <div>
            <button className="btn btn--ghost" onClick={() => onOpenLineage(forecast.lineage_refs, "Forecast lineage")}>Forecast lineage</button>
          </div>
        )}
      </section>
    );
  }

  const d = forecast.display || {};
  const wd = forecast.working_days || {};
  const elapsedPct = pct(wd.elapsed_working_days, wd.total_working_days);
  const projectedPct = (() => {
    const raw = String(d.projected_achievement_pct || "").replace("%", "").trim();
    const n = Number(raw);
    return Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : null;
  })();
  const assumptions = safeArray(forecast.assumptions);

  return (
    <section className={layoutClass} aria-label="Month-end runway">
      <div className="runway-head">
        <div>
          <span className="eyebrow">Landing forecast · {forecast.forecast_name || "month-end"}</span>
          <h2 className="display h3 title">
            {d.projected_month_end_landing
              ? `A glide to ${d.projected_month_end_landing}.`
              : "Projected landing unavailable."}
          </h2>
          <p className="sub">{forecast.basis_disclosure || forecast.reporting_basis || "Basis unavailable"}. Working-day arithmetic and projection live on the backend.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn--ghost" onClick={() => onOpenLineage(safeArray(forecast.lineage_refs), "Forecast lineage")}>Forecast lineage</button>
        </div>
      </div>

      <div>
        {elapsedPct != null && (
          <>
            <div className="runway" role="img" aria-label={`Elapsed ${wd.elapsed_working_days} of ${wd.total_working_days} working days`}>
              <div className="runway-grid" />
              <div className="runway-track" />
              <div className="runway-actual" style={{ left: 0, width: `${elapsedPct}%` }} />
              {projectedPct != null && projectedPct > elapsedPct && (
                <div className="runway-projected" style={{ left: `${elapsedPct}%`, width: `${projectedPct - elapsedPct}%` }} />
              )}
              <div className="runway-target" style={{ left: "100%" }} />
              <div className="runway-now" style={{ left: `${elapsedPct}%` }} />
              <div className="runway-marker" style={{ left: `${elapsedPct}%` }} />
            </div>
            <div className="runway-axis"><span>Month start</span><span>Today</span><span>Month end</span></div>
          </>
        )}

        <div className="runway-stats">
          <div className="runway-stat solid">
            <div className="label">MTD actual</div>
            <div className="value num">{d.mtd_total_collections || "Unavailable"}</div>
            <div className="basis">R04 Finance · {wd.elapsed_working_days ?? "?"} of {wd.total_working_days ?? "?"} working days</div>
          </div>
          <div className="runway-stat solid">
            <div className="label">Month target</div>
            <div className="value num">{d.may_total_collections_target || "Unavailable"}</div>
            <div className="basis">R02 MDO</div>
          </div>
          <div className="runway-stat solid">
            <div className="label">Required run-rate</div>
            <div className="value num">{d.required_daily_run_rate_remaining || "Unavailable"}</div>
            <div className="basis">For remaining {wd.remaining_working_days ?? "?"} working days</div>
          </div>
          <div className="runway-stat solid runway-stat--accent">
            <div className="label">Projected landing</div>
            <div className="value num">{d.projected_month_end_landing || "Unavailable"}</div>
            <div className="basis">{d.projected_achievement_pct || "—"} · {d.gap_to_may_mdo_target || "gap unavailable"}</div>
          </div>
        </div>
      </div>

      <div className="runway-foot">
        <ul>
          <li><span className="dot dot--trust" /> Actual to today (R04)</li>
          <li><span style={{ width: 12, height: 2, background: "var(--teal-2)", display: "inline-block" }} /> Projected glide</li>
          <li><span style={{ width: 2, height: 12, background: "var(--text-hi)", opacity: 0.4, display: "inline-block" }} /> Month target</li>
        </ul>
        <span className="mono small">Assumptions: {assumptions.length} · server-disclosed</span>
      </div>

      {assumptions.length > 0 && (
        <details className="small" style={{ marginTop: 10 }}>
          <summary className="mono" style={{ cursor: "pointer", color: "var(--text-mute)" }}>Forecast assumptions (server-disclosed)</summary>
          <ul style={{ marginTop: 8, paddingLeft: 18, color: "var(--text-mute)" }}>
            {assumptions.map((a) => <li key={a}>{a}</li>)}
          </ul>
        </details>
      )}
    </section>
  );
}
