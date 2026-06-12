/* SCIP TweaksPanel — user-visible in UAT via a quiet chrome entry (decided).
 * Theme, accent, default lens, forecast layout, autoLineage (default OFF).
 * Choices persist locally only — presentation preferences, never data
 * behavior. Flag for the production-gate review whether it stays user-facing.
 */
import { ROLE_LABELS, ROLE_ORDER } from "../api/client.js";
import { IconClose } from "../components/icons.jsx";

const THEMES = [
  { value: "navy", color: "#0a1020", outer: "#c9a55b" },
  { value: "midnight", color: "#04060d", outer: "#5fb3a8" },
  { value: "mahogany", color: "#1a0e0c", outer: "#c8705e" },
  { value: "porcelain", color: "#efe8d8", outer: "#7a623c" },
];
const ACCENTS = [
  { value: "gold", color: "#c9a55b" },
  { value: "pearl", color: "#e7dcc4" },
  { value: "steel", color: "#7ba6c7" },
  { value: "teal", color: "#5fb3a8" },
];
const LAYOUTS = [
  { value: "default", label: "Default" },
  { value: "split", label: "Split" },
  { value: "stacked", label: "Tall" },
];

function Row({ label, children }) {
  return (
    <div style={{ marginTop: 14 }}>
      <div className="eyebrow eyebrow--mute" style={{ marginBottom: 8 }}>{label}</div>
      {children}
    </div>
  );
}

function Swatches({ options, current, onPick, ring = false }) {
  return (
    <div style={{ display: "flex", gap: 8 }} role="radiogroup">
      {options.map((s) => {
        const on = current === s.value;
        return (
          <button
            key={s.value}
            type="button"
            role="radio"
            aria-checked={on}
            aria-label={s.value}
            title={s.value}
            onClick={() => onPick(s.value)}
            style={{
              width: 38, height: 30, borderRadius: 8, background: s.color, cursor: "pointer",
              boxShadow: on
                ? `0 0 0 2px ${ring ? s.outer : "var(--accent)"}`
                : `inset 0 0 0 1px ${ring ? `${s.outer}66` : "var(--line-strong)"}`,
            }}
          />
        );
      })}
    </div>
  );
}

export default function TweaksPanel({ open, tweaks, setTweak, onClose }) {
  if (!open) return null;
  return (
    <aside
      className="glass"
      role="dialog"
      aria-label="Tweaks"
      style={{
        position: "fixed", right: 18, bottom: 64, zIndex: 60, width: 280,
        padding: 18, borderRadius: "var(--r-md)", border: "1px solid var(--line-glass)",
        background: "var(--bg-card)", boxShadow: "var(--depth-2)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span className="eyebrow">Tweaks · presentation only</span>
        <button className="btn btn--sm btn--icon btn--ghost" onClick={onClose} aria-label="Close tweaks"><IconClose size={12} /></button>
      </div>

      <Row label="Theme">
        <Swatches options={THEMES} current={tweaks.theme} onPick={(v) => setTweak("theme", v)} ring />
      </Row>
      <Row label="Accent">
        <Swatches options={ACCENTS} current={tweaks.accent} onPick={(v) => setTweak("accent", v)} />
      </Row>
      <Row label="Default lens">
        <select
          value={tweaks.defaultRole}
          onChange={(e) => setTweak("defaultRole", e.target.value)}
          style={{ width: "100%", height: 30, borderRadius: 8, background: "var(--bg-rise)", border: "1px solid var(--line-strong)", padding: "0 8px" }}
          aria-label="Default lens"
        >
          {ROLE_ORDER.map((k) => <option key={k} value={k}>{ROLE_LABELS[k]}</option>)}
        </select>
      </Row>
      <Row label="Runway layout">
        <div style={{ display: "flex", gap: 6 }} role="radiogroup">
          {LAYOUTS.map((l) => (
            <button
              key={l.value}
              role="radio"
              aria-checked={tweaks.forecastLayout === l.value}
              className={`btn btn--sm ${tweaks.forecastLayout === l.value ? "btn--primary" : "btn--ghost"}`}
              onClick={() => setTweak("forecastLayout", l.value)}
            >
              {l.label}
            </button>
          ))}
        </div>
      </Row>
      <Row label="Lineage behaviour">
        <button
          className={`btn btn--sm ${tweaks.autoLineage ? "btn--primary" : "btn--ghost"}`}
          role="switch"
          aria-checked={tweaks.autoLineage}
          onClick={() => setTweak("autoLineage", !tweaks.autoLineage)}
        >
          Auto-show lineage on tile hover · {tweaks.autoLineage ? "On" : "Off (default)"}
        </button>
      </Row>
      <p className="small" style={{ marginTop: 14, color: "var(--text-faint)" }}>
        Stored locally on this device. Never changes data behavior.
      </p>
    </aside>
  );
}
