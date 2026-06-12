/**
 * SCIP NavProvider — route/focus/present/drawer state + the scip:nav event
 * bus from the prototype. Quickball (and any surface) dispatches
 * `new CustomEvent("scip:nav", { detail: { route, focus, entity, present } })`
 * and navigation happens here — no component-to-component coupling.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const NavContext = createContext(null);

export function useNav() {
  const ctx = useContext(NavContext);
  if (!ctx) throw new Error("useNav outside NavProvider");
  return ctx;
}

export default function NavProvider({ children, onEntity }) {
  const [route, setRoute] = useState("arrival"); // arrival | live_pulse | narratives
  const [focus, setFocus] = useState("current_signal");
  const [present, setPresent] = useState(false);
  const [lineage, setLineage] = useState({ open: false, refs: [], title: "" });
  const [workflow, setWorkflow] = useState({ open: false, record: null, sourceAction: null });

  const enterWorld = useCallback((next) => {
    setRoute(next);
    setFocus(next === "narratives" ? "story" : "current_signal");
  }, []);

  const openLineage = useCallback((refs, title) => setLineage({ open: true, refs: refs || [], title: title || "Evidence" }), []);
  const closeLineage = useCallback(() => setLineage({ open: false, refs: [], title: "" }), []);
  const openWorkflow = useCallback((record, sourceAction) => setWorkflow({ open: true, record, sourceAction }), []);
  const closeWorkflow = useCallback(() => setWorkflow({ open: false, record: null, sourceAction: null }), []);

  // Navigation bus — Quickball and future surfaces dispatch nav intents here.
  useEffect(() => {
    function onNav(e) {
      const d = e.detail || {};
      if (d.present) { setPresent(true); return; }
      if (d.entity && onEntity) onEntity(d.entity);
      if (d.route) {
        setRoute(d.route);
        if (d.focus) setFocus(d.focus);
        else setFocus(d.route === "narratives" ? "story" : "current_signal");
      } else if (d.focus) {
        setFocus(d.focus);
      }
    }
    window.addEventListener("scip:nav", onNav);
    return () => window.removeEventListener("scip:nav", onNav);
  }, [onEntity]);

  const askQuickball = useCallback((q) => {
    window.dispatchEvent(new CustomEvent("scip:quickball:ask", { detail: q }));
  }, []);

  const value = useMemo(() => ({
    route, setRoute, focus, setFocus, enterWorld,
    present, setPresent,
    lineage, openLineage, closeLineage,
    workflow, openWorkflow, closeWorkflow,
    askQuickball,
  }), [route, focus, enterWorld, present, lineage, openLineage, closeLineage, workflow, openWorkflow, closeWorkflow, askQuickball]);

  return <NavContext.Provider value={value}>{children}</NavContext.Provider>;
}
