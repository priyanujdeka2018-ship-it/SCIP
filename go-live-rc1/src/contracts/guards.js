/**
 * SCIP contract guards — zod-free runtime checks built from the OBSERVED
 * shapes in src/contracts/README.md. Guards never throw and never repair
 * values: they return { ok, problems[] } so the diagnostics surface can
 * disclose contract drift, while rendering stays verbatim-from-payload.
 */

export function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

export function safeObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

/** Backend contracts may return entity scope as array or string (hardening note). */
export function formatEntityScope(scope) {
  if (Array.isArray(scope)) return scope.filter(Boolean).join(", ") || "none";
  if (typeof scope === "string" && scope.trim()) return scope;
  return "none";
}

function check(problems, condition, message) {
  if (!condition) problems.push(message);
}

export function guardCommandCentres(payload) {
  const problems = [];
  const roles = safeObject(payload?.roles);
  check(problems, payload && typeof payload === "object", "payload is not an object");
  check(problems, Object.keys(roles).length > 0, "roles map is empty");
  check(problems, !("entity_head" in roles), "entity_head present in roles (locked-out role)");
  for (const [role, block] of Object.entries(roles)) {
    check(problems, Array.isArray(block?.cards), `roles.${role}.cards is not an array`);
    check(problems, block?.trust_bar && typeof block.trust_bar === "object", `roles.${role}.trust_bar missing`);
  }
  return { ok: problems.length === 0, problems };
}

export function guardForecast(payload) {
  const problems = [];
  check(problems, typeof payload?.status === "string", "forecast.status missing");
  if (payload?.status === "ok") {
    check(problems, payload?.display && typeof payload.display === "object", "forecast.display missing");
    check(problems, payload?.working_days && typeof payload.working_days === "object", "forecast.working_days missing");
    check(problems, Array.isArray(payload?.assumptions), "forecast.assumptions missing");
    check(problems, Array.isArray(payload?.lineage_refs), "forecast.lineage_refs missing");
  } else {
    check(problems, typeof payload?.reason === "string" || payload?.status === "blocked_untrusted_forecast",
      "non-ok forecast without reason");
  }
  return { ok: problems.length === 0, problems };
}

export function guardActionQueues(payload) {
  const problems = [];
  const roles = safeObject(payload?.roles);
  check(problems, Object.keys(roles).length > 0, "action-queue roles map is empty");
  check(problems, !("entity_head" in roles), "entity_head present in action-queue roles");
  return { ok: problems.length === 0, problems };
}

export function guardWorkflows(payload) {
  const problems = [];
  check(problems, Array.isArray(payload?.records), "workflows.records is not an array");
  check(problems, Array.isArray(payload?.event_log), "workflows.event_log is not an array");
  return { ok: problems.length === 0, problems };
}

/**
 * Critical-metric lineage contract (drawer fields). Per accepted gap G6 the
 * refs lack snapshot_date and a per-metric hash today; the drawer renders
 * whatever exists verbatim and shows unavailable rows for the rest.
 */
export const LINEAGE_REF_FIELDS = [
  ["source_file", "Source file"],
  ["sheet", "Sheet"],
  ["cell_or_range", "Cell / range"],
  ["validation_status", "Validation"],
  ["confidence_state", "Confidence"],
  ["reporting_basis", "Reporting basis"],
];

export function lineageRefIsComplete(ref) {
  return Boolean(ref) && LINEAGE_REF_FIELDS.every(([key]) => ref[key] != null && ref[key] !== "");
}
