/* SCIP icons — SVG primitives only, ported verbatim from the prototype. */

export function IconChevron({ size = 14, dir = "right" }) {
  const r = { right: 0, left: 180, down: 90, up: -90 }[dir] || 0;
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" style={{ transform: `rotate(${r}deg)` }} aria-hidden="true">
      <path d="M6 3 L11 8 L6 13" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
export function IconClose({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
      <path d="M4 4 L12 12 M12 4 L4 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
export function IconBolt({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
      <path d="M9 1 L3 9 L7 9 L7 15 L13 7 L9 7 Z" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinejoin="round" />
    </svg>
  );
}
export function IconPulse({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
      <path d="M1 8 H5 L7 4 L9 12 L11 8 H15" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
export function IconBook({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
      <rect x="2.5" y="2.5" width="11" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.2" fill="none" />
      <path d="M5 6 H11 M5 8.5 H11 M5 11 H9" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
    </svg>
  );
}
export function IconSearch({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="7" cy="7" r="4" stroke="currentColor" strokeWidth="1.4" fill="none" />
      <path d="M10 10 L14 14" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}
