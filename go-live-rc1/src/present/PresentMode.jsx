/* SCIP Present mode — board-safe full-screen chapter walk.
 * No chrome, no drawers, no depth (locked). Slides carry the same verbatim
 * server values as the Narratives chapters (gap G3 posture: structural
 * questions + server stats; no invented prose). ← → / click / Esc.
 */
import { useEffect, useState } from "react";
import { NARRATIVES, chapterStats } from "../screens/narratives/Narratives.jsx";
import { IconClose } from "../components/icons.jsx";

export default function PresentMode({ open, onClose, session }) {
  const chapters = NARRATIVES;
  const slideCount = chapters.length + 2; // cover + chapters + close
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    if (!open) return undefined;
    setIdx(0);
    function onKey(e) {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowRight" || e.key === " " || e.key === "Enter") setIdx((i) => Math.min(i + 1, slideCount - 1));
      else if (e.key === "ArrowLeft") setIdx((i) => Math.max(i - 1, 0));
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose, slideCount]);

  if (!open) return null;

  const snapshot = session.trustBar?.snapshot_date || "snapshot unavailable";
  const isCover = idx === 0;
  const isClose = idx === slideCount - 1;
  const chapter = !isCover && !isClose ? chapters[idx - 1] : null;
  const stats = chapter ? chapterStats(chapter.key, session) : [];

  function advance(e) {
    const x = e.clientX / window.innerWidth;
    if (x < 0.3) setIdx((i) => Math.max(i - 1, 0));
    else setIdx((i) => Math.min(i + 1, slideCount - 1));
  }

  return (
    <div className="present" role="dialog" aria-modal="true" aria-label="Present mode" onClick={advance}>
      <div className="present-bg" aria-hidden="true" />

      <div className="present-progress" aria-hidden="true">
        {Array.from({ length: slideCount }).map((_, i) => (
          <span key={i} className={i <= idx ? "on" : ""} />
        ))}
      </div>

      {isCover && (
        <section className="present-slide present-cover" key="cover">
          <div className="present-mark">S</div>
          <div className="eyebrow" style={{ marginTop: 26 }}>Sobha Collections Intelligence Platform</div>
          <h1 className="present-title display">Collections<br />Briefing</h1>
          <p className="present-sub">Board-safe narrative · all figures server-lineaged · {snapshot}</p>
          <div className="present-hint">Click or press → to begin</div>
        </section>
      )}

      {chapter && (
        <section className="present-slide" key={chapter.key}>
          <div className="present-chapter-meta">
            <span className="present-chapter-num">{chapter.num}</span>
            <span className="eyebrow">{chapter.label}</span>
          </div>
          <h2 className="present-chapter-title display">{chapter.question}</h2>
          <p className="present-lede">Figures below are verbatim server values for this lens. Narrative prose arrives with the server narrative payload (gap G3).</p>
          <div className="present-stats">
            {stats.map((s) => (
              <div key={s.label} className="present-stat">
                <div className="label">{s.label}</div>
                {s.value ? (
                  <>
                    <div className="val num">{s.value.val}</div>
                    <div className={`delta ${s.value.tone}`}>{s.value.delta}</div>
                  </>
                ) : (
                  <div className="delta warn">Unavailable · no server source</div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {isClose && (
        <section className="present-slide present-cover" key="close">
          <div className="eyebrow">End of briefing</div>
          <h2 className="present-title display" style={{ fontSize: "clamp(40px, 6vw, 80px)" }}>Evidence stays<br />one ask away.</h2>
          <p className="present-sub">Every figure shown is lineage-backed · {snapshot}</p>
          <div className="present-hint">Press Esc to exit</div>
        </section>
      )}

      <div className="present-foot" aria-hidden="true">
        <span>SCIP · Present</span>
        <span>{isCover ? "Cover" : isClose ? "Close" : `Chapter ${chapter.num} of 05`}</span>
        <span>{snapshot} · server-lineaged</span>
      </div>

      <button className="present-exit" onClick={(e) => { e.stopPropagation(); onClose(); }} aria-label="Exit present mode">
        <IconClose size={16} />
      </button>
    </div>
  );
}
