/* SCIP Chrome — top nav: brand, two-route nav, entity pill, role pill.
 * Layout/motion ported from the prototype; all data fields verbatim from
 * server payloads via SessionProvider. Entity scoping per accepted gap G8:
 * Group is the only server-scoped lens today — other entities render as
 * explicitly unavailable choices, never client-filtered figures.
 */
import { useEffect, useRef, useState } from "react";
import { ROLE_LABELS, ROLE_META, ROLE_ORDER } from "../api/client.js";
import { IconChevron } from "./icons.jsx";

export const ENTITIES = [
  { value: "group", label: "Group", scoped: true },
  { value: "sobha", label: "Sobha", scoped: false },
  { value: "sobha_dubai", label: "Sobha Dubai", scoped: false },
  { value: "sobha_auh", label: "Sobha AUH", scoped: false },
  { value: "uaq", label: "UAQ", scoped: false },
  { value: "siniya", label: "Siniya", scoped: false },
  { value: "downtown_uaq", label: "Downtown UAQ", scoped: false },
];

export function entityLabel(v) {
  return (ENTITIES.find((e) => e.value === v) || ENTITIES[0]).label;
}

export default function Chrome({ route, setRoute, role, setRole, roleKeys, entity, setEntity, dataDate, loadTimestamp }) {
  const [menu, setMenu] = useState(false);
  const [entMenu, setEntMenu] = useState(false);
  const ref = useRef(null);
  const entRef = useRef(null);

  useEffect(() => {
    function onClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setMenu(false);
      if (entRef.current && !entRef.current.contains(e.target)) setEntMenu(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const keys = (roleKeys && roleKeys.length ? ROLE_ORDER.filter((k) => roleKeys.includes(k)) : ROLE_ORDER);

  return (
    <header className="chrome" aria-label="SCIP top chrome">
      <div className="chrome-brand" onClick={() => setRoute("arrival")}>
        <div className="chrome-mark">S</div>
        <div>
          <div className="chrome-name">SCIP</div>
          <div className="chrome-sub">{dataDate || "snapshot unavailable"}{loadTimestamp ? ` · ${loadTimestamp}` : ""}</div>
        </div>
      </div>
      <nav className="chrome-nav" aria-label="Primary navigation">
        <button aria-current={route === "live_pulse"} onClick={() => setRoute("live_pulse")}>Live Pulse</button>
        <button aria-current={route === "narratives"} onClick={() => setRoute("narratives")}>Narratives</button>
      </nav>
      <div className="chrome-right">
        <div style={{ position: "relative" }} ref={entRef}>
          <button className="role-pill entity-pill" onClick={() => setEntMenu(!entMenu)} aria-haspopup="true" aria-expanded={entMenu} title="Entity scope">
            <span className="entity-glyph" aria-hidden="true">⌬</span>
            <span>{entityLabel(entity)}</span>
            <span className="caret"><IconChevron dir="down" /></span>
          </button>
          {entMenu && (
            <div className="role-menu glass" role="menu" style={{ width: 260 }}>
              <div style={{ padding: "8px 12px 4px", fontFamily: "var(--f-mono)", fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--text-mute)" }}>Entity scope</div>
              {ENTITIES.map((e) => (
                <button
                  key={e.value}
                  aria-current={entity === e.value}
                  aria-disabled={!e.scoped}
                  title={e.scoped ? e.label : "Server-side entity scoping is not available yet for this scope"}
                  style={e.scoped ? undefined : { opacity: 0.45 }}
                  onClick={() => { if (e.scoped) { setEntity(e.value); setEntMenu(false); } }}
                >
                  <div className="avatar-sm" style={{ background: entity === e.value ? "linear-gradient(135deg, var(--accent), var(--accent-hi))" : "rgba(255,255,255,0.08)", color: entity === e.value ? "#1a1407" : "var(--text)", fontSize: 11 }}>
                    {e.label[0]}
                  </div>
                  <div>
                    <div className="role-name">{e.label}</div>
                    {!e.scoped && <div className="role-desc">Unavailable · server scoping pending</div>}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
        <div style={{ position: "relative" }} ref={ref}>
          <button className="role-pill" onClick={() => setMenu(!menu)} aria-haspopup="true" aria-expanded={menu}>
            <span className="avatar">{ROLE_META[role]?.short || "??"}</span>
            <span>{ROLE_LABELS[role] || role}</span>
            <span className="caret"><IconChevron dir="down" /></span>
          </button>
          {menu && (
            <div className="role-menu glass" role="menu">
              {keys.map((k) => (
                <button key={k} aria-current={role === k} onClick={() => { setRole(k); setMenu(false); }}>
                  <div className="avatar-sm" style={{ background: role === k ? "linear-gradient(135deg, var(--accent), var(--accent-hi))" : "rgba(255,255,255,0.08)", color: role === k ? "#1a1407" : "var(--text)" }}>
                    {ROLE_META[k]?.short}
                  </div>
                  <div>
                    <div className="role-name">{ROLE_LABELS[k] || k}</div>
                    <div className="role-desc">{ROLE_META[k]?.desc}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
