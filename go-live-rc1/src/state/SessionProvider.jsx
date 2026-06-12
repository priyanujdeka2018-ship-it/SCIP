/**
 * SCIP SessionProvider — role, entity scope, startup loading gate.
 *
 * Startup gate: the four blocking endpoints (/command-centres,
 * /forecast/month-end, /action-queues, /workflows) load together; any failure
 * surfaces the staging diagnostics panel. Optional surfaces are fully lazy
 * (fetched by the surface that needs them). /persistence/summary is optional
 * per accepted gap G11.
 *
 * W1 awareness: if a blocking endpoint answers with the warming envelope the
 * session enters status "warming" and re-polls after retry_after_seconds —
 * an honest trust state, never a fabricated payload.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { warmingStateOf } from "../api/client.js";
import { getActionQueues, getCommandCentres, getForecastMonthEnd, getWorkflows } from "../api/endpoints.js";
import { guardActionQueues, guardCommandCentres, guardForecast, guardWorkflows, safeArray, safeObject } from "../contracts/guards.js";

const SessionContext = createContext(null);

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession outside SessionProvider");
  return ctx;
}

export default function SessionProvider({ children, initialRole = "cco_gm_agm" }) {
  const [role, setRole] = useState(initialRole);
  const [entity, setEntity] = useState("group"); // gap G8: only group is server-scoped today
  const [status, setStatus] = useState("loading"); // loading | warming | ready | error
  const [warming, setWarming] = useState(null);
  const [diagnostic, setDiagnostic] = useState(null);
  const [contractProblems, setContractProblems] = useState([]);
  const [data, setData] = useState({ commandCentres: null, forecast: null, actionQueues: null, workflows: null });
  const [roleRefreshing, setRoleRefreshing] = useState(false);
  const retryTimer = useRef(null);
  const generation = useRef(0);

  const load = useCallback(async (activeRole, { background = false } = {}) => {
    const gen = ++generation.current;
    if (!background) setStatus((s) => (s === "ready" ? s : "loading"));
    setRoleRefreshing(background);
    const onDiagnostic = (d) => { if (gen === generation.current) setDiagnostic(d); };
    const opts = { role: activeRole, onDiagnostic };

    try {
      const [commandCentres, forecast, actionQueues, workflows] = await Promise.all([
        getCommandCentres(opts),
        getForecastMonthEnd(opts),
        getActionQueues(opts),
        getWorkflows(opts),
      ]);
      if (gen !== generation.current) return;

      const warmingHit = [commandCentres, forecast, actionQueues, workflows]
        .map(warmingStateOf)
        .find(Boolean);
      if (warmingHit) {
        setWarming(warmingHit);
        setStatus("warming");
        if (warmingHit.state === "warming") {
          clearTimeout(retryTimer.current);
          retryTimer.current = setTimeout(() => load(activeRole, { background }), warmingHit.retryAfterSeconds * 1000);
        }
        return;
      }

      const problems = [
        ...guardCommandCentres(commandCentres).problems.map((p) => `command-centres: ${p}`),
        ...guardForecast(forecast).problems.map((p) => `forecast: ${p}`),
        ...guardActionQueues(actionQueues).problems.map((p) => `action-queues: ${p}`),
        ...guardWorkflows(workflows).problems.map((p) => `workflows: ${p}`),
      ];
      setContractProblems(problems);
      setWarming(null);
      setData({ commandCentres, forecast, actionQueues, workflows });
      setStatus("ready");
      setDiagnostic(null);
    } catch (err) {
      if (gen !== generation.current) return;
      setStatus("error");
      setDiagnostic((d) => d && d.status !== "requesting" && d.status !== "ok"
        ? d
        : { classification: "required-core-endpoint", endpoint: "startup", status: err.message, role: activeRole });
    } finally {
      if (gen === generation.current) setRoleRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load(role, { background: status === "ready" });
    return () => clearTimeout(retryTimer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role]);

  const value = useMemo(() => {
    const roles = safeObject(data.commandCentres?.roles);
    const activeRoleBlock = safeObject(roles[role]);
    return {
      role,
      setRole,
      entity,
      setEntity,
      status,
      warming,
      diagnostic,
      contractProblems,
      roleRefreshing,
      retry: () => load(role),
      commandCentres: data.commandCentres,
      forecast: data.forecast,
      actionQueues: data.actionQueues,
      workflows: data.workflows,
      roleKeys: Object.keys(roles),
      activeRoleBlock,
      cards: safeArray(activeRoleBlock.cards),
      trustBar: safeObject(activeRoleBlock.trust_bar),
      contractVersion: data.commandCentres?.contract_version || null,
      guardrails: safeObject(data.commandCentres?.guardrails),
    };
  }, [role, entity, status, warming, diagnostic, contractProblems, roleRefreshing, data, load]);

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}
