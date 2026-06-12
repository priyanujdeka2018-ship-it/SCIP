/* SCIP tweaks store — presentation preferences ONLY, persisted locally.
 * Locked posture: tweaks never alter data behavior; autoLineage defaults
 * OFF; user-facing in UAT (revisit at the production-gate review). */
const KEY = "scip:tweaks";

export const TWEAK_DEFAULTS = {
  theme: "navy",
  accent: "gold",
  forecastLayout: "default",
  autoLineage: false,
  defaultRole: "cco_gm_agm",
};

export function loadTweaks() {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return { ...TWEAK_DEFAULTS, ...JSON.parse(raw) };
  } catch { /* ignore */ }
  return { ...TWEAK_DEFAULTS };
}

export function saveTweaks(tweaks) {
  try { localStorage.setItem(KEY, JSON.stringify(tweaks)); } catch { /* ignore */ }
}
