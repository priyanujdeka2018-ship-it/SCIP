/**
 * SCIP api endpoints — one function per backend route.
 * Components never fetch directly; everything flows endpoint -> guard ->
 * provider -> props. Postures (blocking vs optional) follow the approved
 * contract register: /persistence/summary is optional (gap G11 accepted).
 */
import { fetchJson } from "./client.js";

// ---- blocking core (startup gate) ----
export const getCommandCentres = (opts) => fetchJson("/command-centres", { ...opts, required: true });
export const getForecastMonthEnd = (opts) => fetchJson("/forecast/month-end", { ...opts, required: true });
export const getActionQueues = (opts) => fetchJson("/action-queues", { ...opts, required: true });
export const getWorkflows = (opts) => fetchJson("/workflows", { ...opts, required: true });

// ---- on demand ----
export const getQuickballExplain = (metric, role, opts) =>
  fetchJson(`/quickball/explain?${new URLSearchParams({ metric, role })}`, { ...opts, role, required: false, fallback: { status: "unavailable" } });

// ---- optional UAT surfaces (never block startup; clean unavailable states) ----
export const getNotifications = (role, opts) =>
  fetchJson(role === "board_cxo" ? "/notifications/digests" : "/notifications", {
    ...opts,
    role,
    required: false,
    fallback: {
      status: "unavailable",
      notifications: [],
      digests: {},
      reason: "Notifications are unavailable or blocked for this role in staging.",
    },
  });

export const getPersistenceSummary = (opts) =>
  fetchJson("/persistence/summary", {
    ...opts,
    required: false,
    fallback: {
      status: "unavailable",
      table_counts: {},
      validations: { checks: {} },
      reason: "Persistence/audit summary is unavailable in staging UAT. Production gate unchanged.",
    },
  });

export const getSecurityMe = (role, opts) =>
  fetchJson("/security/me", { ...opts, role, required: false, fallback: { status: "unavailable", actor: { role } } });

export const getIdentityMe = (opts) =>
  fetchJson("/identity/me", { ...opts, required: false, fallback: { status: "unavailable" } });

export const getDeploymentHealth = (opts) =>
  fetchJson("/deployment/health", { ...opts, required: false, fallback: { status: "unavailable" } });

export const getObservabilitySummary = (opts) =>
  fetchJson("/observability/summary", { ...opts, required: false, fallback: { status: "unavailable" } });

export const getObservabilityAlerts = (opts) =>
  fetchJson("/observability/alerts", { ...opts, required: false, fallback: { alerts: [] } });

export const getObservabilityDashboards = (opts) =>
  fetchJson("/observability/dashboards", { ...opts, required: false, fallback: { dashboards: [] } });

export const getHealth = (opts) =>
  fetchJson("/health", { ...opts, required: false, fallback: { status: "unavailable" } });

// ---- workflow actions (server operations; UI never mutates state locally) ----
const postWorkflow = (action, body, opts) =>
  fetchJson(`/workflows/${action}`, { ...opts, method: "POST", body, required: false, fallback: { status: "unavailable" } });

export const workflowAssign = (body, opts) => postWorkflow("assign", body, opts);
export const workflowReassign = (body, opts) => postWorkflow("reassign", body, opts);
export const workflowDueDate = (body, opts) => postWorkflow("due-date", body, opts);
export const workflowDisposition = (body, opts) => postWorkflow("disposition", body, opts);
export const workflowEvidence = (body, opts) => postWorkflow("evidence", body, opts);
export const workflowClose = (body, opts) => postWorkflow("close", body, opts);
