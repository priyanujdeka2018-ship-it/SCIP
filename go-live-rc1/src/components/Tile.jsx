/* SCIP Tile — lineaged KPI tile (calm). Prototype layout; server card data
 * verbatim: title, display_value, reporting_basis, severity, lineage refs.
 * Tap opens the evidence drawer with the card's own refs (no key guessing). */
import { safeArray } from "../contracts/guards.js";
import { IconChevron } from "./icons.jsx";
import Unavailable from "./Unavailable.jsx";

export default function Tile({ card, onOpenLineage, autoLineage = false }) {
  const refs = safeArray(card?.lineage_display).length ? card.lineage_display : safeArray(card?.lineage_refs);
  const lineaged = refs.length > 0 && refs.every((ref) => ref.has_lineage !== false);
  const sev = card?.severity || "info";
  const sevDot = sev === "risk" ? "dot--risk" : (sev === "warn" || sev === "attention") ? "dot--warn" : "dot--ok";
  const value = card?.display_value || card?.display || null;
  const open = () => onOpenLineage(refs, card?.title);

  return (
    <article
      className="tile solid"
      onClick={open}
      onMouseEnter={autoLineage ? () => { open(); } : undefined}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter") open(); }}
    >
      <div className="tile-head">
        <span className="eyebrow eyebrow--mute"><span className={`dot ${sevDot}`} /> &nbsp;{sev === "risk" ? "Risk" : (sev === "warn" || sev === "attention") ? "Attention" : "On track"}</span>
        <span className="tile-trust">
          {lineaged ? <><span className="shield" /> Lineaged</> : "Lineage warning"}
        </span>
      </div>
      <div>
        <h4 className="tile-title">{card?.title || "Untitled card"}</h4>
        {value != null
          ? <div className="tile-value">{value}</div>
          : <Unavailable compact reason="Server card carried no display value" />}
      </div>
      <div className="tile-foot">
        <span>{card?.reporting_basis || "basis unavailable"}</span>
        <span className="arrow"><IconChevron /></span>
      </div>
    </article>
  );
}
