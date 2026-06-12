/**
 * Per-focus card placement — accepted gap G5: the backend placement engine
 * is shadow-mode, so the deployed monolith's keyword heuristic is kept
 * TEMPORARILY and labelled wherever used ("placement: heuristic"). It only
 * SELECTS which server cards appear on a focus; it never alters a value.
 * Retire at placement cutover.
 */
import { safeArray } from "./guards.js";

const FOCUS_KEYWORDS = {
  current_signal: ["od", "today", "confidence", "lineage"],
  month_movement: ["mtd", "month", "forecast", "target", "run-rate", "collections"],
  risk_action: ["risk", "action", "gap", "overdue", "attention"],
  story: ["story", "board", "forecast", "pipeline"],
  portfolio: ["portfolio", "group", "pipeline", "achievement"],
  dues: ["dues", "od", "overdue", "ageing"],
  advance: ["advance", "rebate", "cy", "fy"],
  roadmap: ["roadmap", "action", "risk", "next"],
};

export const PLACEMENT_MODE = "heuristic"; // until server placement cutover (G5)

export function cardsForFocus(cards, focus, limit = 4) {
  const all = safeArray(cards);
  if (all.length <= limit) return all;
  const lowered = (text) => String(text || "").toLowerCase();
  const keywords = FOCUS_KEYWORDS[focus] || [];
  const scored = all.map((card, index) => {
    const haystack = [card.title, card.card_id, card.reporting_basis, card.action, card.severity].map(lowered).join(" ");
    const score = keywords.filter((keyword) => haystack.includes(keyword)).length;
    return { card, score, index };
  });
  const selected = scored
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .slice(0, limit)
    .map((item) => item.card);
  return selected.length ? selected : all.slice(0, limit);
}

/** Find the card whose lineage refs carry a given metric_key (verbatim pick). */
export function cardByMetricKey(cards, metricKey) {
  return safeArray(cards).find((card) =>
    safeArray(card?.lineage_refs).some((ref) => ref?.metric_key === metricKey) ||
    safeArray(card?.lineage_display).some((ref) => ref?.metric_key === metricKey)
  ) || null;
}
