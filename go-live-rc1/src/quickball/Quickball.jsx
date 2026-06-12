/* SCIP Quickball — quiet, contextual, draggable disk (⌘K).
 *
 * Locked rules: Quickball MAY navigate (route/focus/entity intents) but
 * NEVER answers with client-side or mock numbers. The prototype's mock
 * QUICKBALL_ANSWERS map is gone. Numeric questions resolve to an explicit
 * metric key and are answered by GET /quickball/explain (lineaged or
 * server-blocked); anything else gets the standard refusal (accepted gap G7):
 * "I can take you to the surface, but I won't quote a number without lineage."
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { getQuickballExplain } from "../api/endpoints.js";
import { IconClose, IconSearch } from "../components/icons.jsx";

const NAV_TARGETS = [
  { match: /\b(risk|act|action|queue)/, nav: { route: "live_pulse", focus: "risk_action" }, label: "Risk & Action" },
  { match: /\b(month|movement|run.?rate|forecast|landing)/, nav: { route: "live_pulse", focus: "month_movement" }, label: "Month Movement" },
  { match: /\b(signal|today|current)/, nav: { route: "live_pulse", focus: "current_signal" }, label: "Current Signal" },
  { match: /\b(story|board.?level)/, nav: { route: "narratives", focus: "story" }, label: "Narratives · Story" },
  { match: /\bportfolio/, nav: { route: "narratives", focus: "portfolio" }, label: "Narratives · Portfolio" },
  { match: /\b(dues?|overdue|ageing)/, nav: { route: "narratives", focus: "dues" }, label: "Narratives · Dues" },
  { match: /\b(advance|rebate)/, nav: { route: "narratives", focus: "advance" }, label: "Narratives · Advance" },
  { match: /\broadmap/, nav: { route: "narratives", focus: "roadmap" }, label: "Narratives · Roadmap" },
  { match: /\bnarrative/, nav: { route: "narratives" }, label: "Narratives" },
  { match: /\b(live ?pulse|pulse)/, nav: { route: "live_pulse" }, label: "Live Pulse" },
];

/* Explicit metric intents — a question is answered by the server ONLY when
 * it maps unambiguously to a known metric key. No regex-extracted numbers. */
const METRIC_INTENTS = [
  { match: /\b(group )?od\b|\boverdue today\b/, metric: "OD_TODAY", label: "Group OD today" },
  { match: /\bmtd\b|\bmonth.to.date\b|\btotal collections\b/, metric: "MTD_TOTAL_COLLECTIONS", label: "MTD total collections" },
];

const REFUSAL =
  "I can take you to the surface, but I won't quote a number without lineage. " +
  "Ask about a lineaged metric (e.g. Group OD today) or tell me where to go.";

const SUGGESTIONS = [
  "Explain Group OD today",
  "Take me to Risk & Action",
  "Show me Month Movement",
  "Open the roadmap",
  "Start Present mode",
];

function parseNavIntent(norm) {
  if (/\b(present|briefing mode|board mode|slideshow)\b/.test(norm)) {
    return { nav: { present: true }, label: "Present mode" };
  }
  const isNavPhrase = /(take me|go to|open|show me|switch to|navigate|jump to|move to|start)/.test(norm);
  if (!isNavPhrase) return null;
  const target = NAV_TARGETS.find((t) => t.match.test(norm));
  if (target) return { nav: { ...target.nav }, label: target.label };
  return null;
}

export default function Quickball({ role, visible = true }) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const [answer, setAnswer] = useState(null);
  const [asking, setAsking] = useState(false);
  const [pos, setPos] = useState(() => {
    try {
      const raw = localStorage.getItem("scip:qb:pos");
      if (raw) return JSON.parse(raw);
    } catch { /* ignore */ }
    return { x: window.innerWidth - 88, y: window.innerHeight - 88 };
  });
  const [dragging, setDragging] = useState(false);
  const dragState = useRef({ active: false, moved: false, dx: 0, dy: 0 });
  const inputRef = useRef(null);
  const diskRef = useRef(null);

  useEffect(() => {
    try { localStorage.setItem("scip:qb:pos", JSON.stringify(pos)); } catch { /* ignore */ }
  }, [pos]);

  useEffect(() => {
    function onResize() {
      setPos((p) => ({
        x: Math.min(Math.max(8, p.x), window.innerWidth - 64),
        y: Math.min(Math.max(8, p.y), window.innerHeight - 64),
      }));
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    function onKey(e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
        setTimeout(() => inputRef.current?.focus(), 50);
      } else if (e.key === "Escape" && open) {
        setOpen(false);
      }
    }
    function onExternalAsk(e) {
      const q = e.detail;
      if (!q) return;
      setOpen(true);
      setTimeout(() => { setValue(q); ask(q); }, 40);
    }
    document.addEventListener("keydown", onKey);
    window.addEventListener("scip:quickball:ask", onExternalAsk);
    return () => {
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scip:quickball:ask", onExternalAsk);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, role]);

  useEffect(() => {
    if (!open) return undefined;
    function onClickOutside(e) {
      if (diskRef.current && diskRef.current.contains(e.target)) return;
      const panel = document.querySelector(".quickball-panel");
      if (panel && panel.contains(e.target)) return;
      setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  async function ask(q) {
    const norm = (q || "").toLowerCase().trim();
    if (!norm) return;
    setValue(q);

    // 0) a raw metric key (from a curiosity chip) is an explicit intent
    if (/^[A-Z][A-Z0-9_]{2,}$/.test((q || "").trim())) {
      await answerMetric((q || "").trim(), (q || "").trim());
      return;
    }

    // 1) navigation intent — move, don't explain
    const intent = parseNavIntent(norm);
    if (intent) {
      window.dispatchEvent(new CustomEvent("scip:nav", { detail: intent.nav }));
      setAnswer({
        kind: "nav",
        heading: `Navigating · ${intent.label}`,
        body: `Taking you to ${intent.label}. Quickball can move you anywhere — it will still never invent a number.`,
        basis: "Navigation intent · no data asserted",
      });
      setTimeout(() => { setOpen(false); setAnswer(null); setValue(""); }, 1600);
      return;
    }

    // 2) explicit metric intent — server answer only
    const metricIntent = METRIC_INTENTS.find((m) => m.match.test(norm));
    if (metricIntent) {
      await answerMetric(metricIntent.metric, metricIntent.label);
      return;
    }

    // 3) everything else — explicit refusal (locked rule, gap G7)
    setAnswer({
      kind: "blocked",
      heading: "No lineaged answer",
      body: REFUSAL,
      basis: "Trust gate · no silent fallback",
    });
  }

  async function answerMetric(metric, label) {
    setAsking(true);
    try {
      const json = await getQuickballExplain(metric, role);
      const blocked = json?.status === "blocked_untrusted_metric" || json?.status === "unavailable" || json?.error;
      setAnswer(blocked ? {
        kind: "blocked",
        heading: "Quickball blocked an untrusted answer",
        body: json?.reason || json?.error || "The server declined to answer without complete lineage.",
        basis: "Server trust gate · no silent fallback",
      } : {
        kind: "server",
        heading: `${json.metric_label || json.metric_key || label}`,
        body: json.answer || "The server returned no answer text.",
        basis: json.reporting_basis || json.basis || "Server-lineaged answer",
        refs: json.lineage_refs || json.lineage || null,
      });
    } finally {
      setAsking(false);
    }
  }

  function onPointerDown(e) {
    const rect = diskRef.current.getBoundingClientRect();
    dragState.current = {
      active: true, moved: false,
      dx: e.clientX - rect.left, dy: e.clientY - rect.top,
      startX: e.clientX, startY: e.clientY,
    };
    diskRef.current.setPointerCapture(e.pointerId);
  }
  function onPointerMove(e) {
    const st = dragState.current;
    if (!st.active) return;
    if (!st.moved && Math.abs(e.clientX - st.startX) + Math.abs(e.clientY - st.startY) > 4) {
      st.moved = true;
      setDragging(true);
    }
    if (st.moved) {
      setPos({
        x: Math.min(Math.max(8, e.clientX - st.dx), window.innerWidth - 64),
        y: Math.min(Math.max(8, e.clientY - st.dy), window.innerHeight - 64),
      });
    }
  }
  function onPointerUp(e) {
    const moved = dragState.current.moved;
    dragState.current = { active: false, moved: false, dx: 0, dy: 0 };
    setDragging(false);
    try { diskRef.current.releasePointerCapture(e.pointerId); } catch { /* ignore */ }
    if (!moved) {
      setOpen((o) => {
        const next = !o;
        if (next) setTimeout(() => inputRef.current?.focus(), 50);
        return next;
      });
    }
  }

  const panelAnchor = useMemo(() => {
    const right = pos.x > window.innerWidth / 2;
    const bottom = pos.y > window.innerHeight / 2;
    const style = {};
    if (right) style.right = window.innerWidth - pos.x - 56; else style.left = pos.x;
    if (bottom) style.bottom = window.innerHeight - pos.y + 14; else style.top = pos.y + 70;
    return style;
  }, [pos]);

  if (!visible) return null;

  return (
    <>
      <div
        ref={diskRef}
        className={`quickball-disk ${dragging ? "dragging" : ""}`}
        style={{ left: pos.x, top: pos.y }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        role="button"
        tabIndex={0}
        aria-label="Quickball — drag to move, tap to ask"
      >
        <IconSearch size={18} />
        <span className="kbd-tip">DRAG · TAP · ⌘K</span>
      </div>

      {open && (
        <div className="quickball-panel" style={panelAnchor} role="dialog" aria-label="Quickball">
          <div className="quickball-row">
            <div className="quickball-mark"><IconSearch /></div>
            <input
              ref={inputRef}
              className="quickball-input"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") ask(value); }}
              placeholder="Ask Quickball — explain a number, or tell it where to go…"
              aria-label="Ask Quickball"
              autoFocus
            />
            <button className="btn btn--sm btn--primary" disabled={asking} onClick={() => ask(value)}>{asking ? "…" : "Ask"}</button>
            <button className="btn btn--sm btn--icon btn--ghost" onClick={() => { setOpen(false); setAnswer(null); setValue(""); }} aria-label="Collapse"><IconClose /></button>
          </div>

          {!answer && (
            <div className="quickball-suggest" style={{ marginTop: 0, paddingTop: 0, borderTop: 0 }}>
              <div className="heading">Try one</div>
              <div className="row">
                {SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => ask(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}

          {answer && (
            <div className={`quickball-answer ${answer.kind === "blocked" ? "blocked" : ""}`} role="status">
              <div className="label">{answer.heading}</div>
              <p className="answer">{answer.body}</p>
              <div className="basis">Basis · {answer.basis}</div>
              {answer.kind !== "nav" && (
                <div style={{ marginTop: 12, display: "flex", gap: 6 }}>
                  <button className="btn btn--sm btn--ghost" onClick={() => { setAnswer(null); setValue(""); inputRef.current?.focus(); }}>Ask another</button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </>
  );
}
