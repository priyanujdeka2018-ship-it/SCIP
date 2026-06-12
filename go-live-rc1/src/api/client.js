/**
 * SCIP api client — URL normalization, staging bypass, failure-class fetch.
 *
 * Merges the two monolith lineages (disclosed in src/contracts/README.md):
 * the UAT hardening (3 env names + trailing-slash strip, bypass aliases,
 * network/HTTP/JSON failure classes, rolling diagnostics) and the deployed
 * behavior set. Also classifies the W1 warming envelope (body-only,
 * scip_state = warming | warmup_failed) as a first-class non-error state.
 *
 * No business computation lives here. Responses pass through verbatim.
 */

// Permanent: accept all known Vite backend URL env names, then normalize to
// avoid double slashes.
export const BACKEND_URL = (
  import.meta?.env?.VITE_BACKEND_URL ||
  import.meta?.env?.VITE_SCIP_API_BASE_URL ||
  import.meta?.env?.VITE_API_BASE_URL ||
  "https://scip.onrender.com"
).replace(/\/$/, "");

// Permanent hardening: canonical staging bypass flag plus legacy aliases.
// Production must set all bypass flags false/unset and use real JWT/SSO.
export const LOCAL_DEV_BYPASS = [
  import.meta?.env?.VITE_SCIP_LOCAL_DEV_BYPASS,
  import.meta?.env?.VITE_LOCAL_DEV_BYPASS,
  import.meta?.env?.VITE_AUTH_BYPASS,
].some((value) => String(value || "").toLowerCase() === "true");

export const ROLE_ORDER = ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"];

export const ROLE_LABELS = {
  board_cxo: "Board / CXO",
  cco_gm_agm: "CCO / GM / AGM",
  finance: "Finance",
  mis_qcg_admin: "MIS / QCG / Admin",
  collector_rm: "Collector / RM",
};

export const ROLE_META = {
  board_cxo: { short: "BC", desc: "Board-safe story, risk, confidence." },
  cco_gm_agm: { short: "CG", desc: "Intervention control, run-rate, escalations." },
  finance: { short: "FN", desc: "Reconciliation, PR/SOA, audit." },
  mis_qcg_admin: { short: "MQ", desc: "Data health, governance, refresh." },
  collector_rm: { short: "CR", desc: "Own queues, promise follow-up, accounts." },
};

const ACTOR_IDS = {
  board_cxo: "board_cxo_demo",
  cco_gm_agm: "cco_manager_demo",
  finance: "finance_demo",
  mis_qcg_admin: "mis_admin_demo",
  collector_rm: "collector_rm_demo",
};

function demoJwtForRole(role) {
  const envKey = `VITE_SCIP_JWT_${String(role || "").toUpperCase()}`;
  return import.meta?.env?.[envKey] || import.meta?.env?.VITE_SCIP_DEMO_JWT || "";
}

export function newCorrelationId() {
  return `scip-ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function authHeaders(role, correlationId = newCorrelationId()) {
  if (LOCAL_DEV_BYPASS) {
    return {
      "X-SCIP-Actor-ID": ACTOR_IDS[role] || "board_cxo_demo",
      "X-SCIP-Actor-Name": ROLE_LABELS[role] || "Board / CXO",
      "X-SCIP-Role": role,
      "X-SCIP-Entity-Scope": role === "collector_rm" ? "Sobha Dubai" : "Group",
      "X-SCIP-Collector-ID": role === "collector_rm" ? "collector_rm_demo" : "",
      "X-SCIP-Environment": "local",
      "X-SCIP-Correlation-ID": correlationId,
    };
  }
  const token = demoJwtForRole(role);
  return {
    Authorization: token ? `Bearer ${token}` : "",
    "X-SCIP-Correlation-ID": correlationId,
  };
}

/** W1 warming envelope detection (body-only contract; HTTP is 200). */
export function warmingStateOf(body) {
  const state = body?.scip_state;
  if (state === "warming" || state === "warmup_failed") {
    return {
      state,
      stage: body.stage,
      startedAt: body.started_at,
      detail: body.detail,
      reason: body.reason || null,
      retryAfterSeconds: Number(body.retry_after_seconds) || 4,
    };
  }
  return null;
}

/**
 * fetchJson with explicit failure classes:
 *   network/CORS failure · HTTP status failure (with body snippet) · invalid JSON.
 * required=true throws on failure; required=false returns the fallback with
 * the error message attached. onDiagnostic receives every state transition.
 */
export async function fetchJson(path, {
  role,
  required = true,
  fallback = { status: "unavailable" },
  method = "GET",
  body = undefined,
  headers = undefined,
  onDiagnostic = () => {},
} = {}) {
  const requestHeaders = headers || authHeaders(role);
  const correlationId = requestHeaders["X-SCIP-Correlation-ID"];
  const classification = required ? "required-core-endpoint" : "optional-uat-surface";
  const report = (status) => onDiagnostic({
    classification,
    endpoint: path,
    status,
    role,
    backendUrl: BACKEND_URL,
    bypass: LOCAL_DEV_BYPASS,
    correlationId,
  });

  let res;
  try {
    report("requesting");
    res = await fetch(`${BACKEND_URL}${path}`, {
      method,
      mode: "cors",
      cache: "no-store",
      headers: body !== undefined
        ? { ...requestHeaders, "Content-Type": "application/json" }
        : requestHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    const message = `${path} network/CORS: ${err?.message || "Load failed"}`;
    report(message);
    if (required) throw new Error(message);
    return { ...fallback, error: message };
  }

  if (!res.ok) {
    let detail = "";
    try {
      const text = await res.text();
      detail = text ? ` · ${text.slice(0, 220)}` : "";
    } catch {
      detail = "";
    }
    const message = `${path} ${res.status}${detail}`;
    report(message);
    if (required) throw new Error(message);
    return { ...fallback, error: message };
  }

  try {
    const json = await res.json();
    report("ok");
    return json;
  } catch (err) {
    const message = `${path} invalid JSON: ${err?.message || "Parse failed"}`;
    report(message);
    if (required) throw new Error(message);
    return { ...fallback, error: message };
  }
}
