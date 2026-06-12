# SCIP Frontend Contracts — Observed Shapes, Mapping & Gap Register

**Step 0 artifact for the Liquid Glass UI rebuild. Nothing here is guessed; every shape below was captured from the running backend.**

## Provenance (disclosed)

- Captured 2026-06-12 by running the `release`-lineage backend (branch `claude/cool-johnson-mfytir`, behavior-identical flag-off) **in-process** via FastAPI TestClient with the staging local-dev bypass headers, against the real 13-file R-series source set fetched from the production Google Drive folder.
- The live staging URL (`scip.onrender.com`) is not reachable from the capture environment (network allowlist), so shapes are observed from the same code + same data rather than over the wire. Differences vs live staging would only come from env/seed state, two of which were observed and recorded below (persistence 500, notifications 401).
- Role used: `mis_qcg_admin` (widest visibility); `/notifications/digests` probed as `board_cxo` per the RBAC model.

## Endpoint posture (observed)

| Endpoint | HTTP | Posture in rebuild |
|---|---|---|
| `/command-centres` | 200 | Blocking at startup |
| `/forecast/month-end` | 200 | Blocking |
| `/action-queues` | 200 | Blocking |
| `/workflows` | 200 | Blocking |
| `/persistence/summary` | **500** `{"detail":"required_demo_record_not_found"}` | Listed blocking in hardening notes, but the deployed monolith treats it optional-with-fallback and it 500s unseeded — **decision needed (gap G11)** |
| `/quickball/explain` | 200 | On demand |
| `/notifications`, `/notifications/digests` | **401** `authentication_failed` under staging bypass | Non-blocking, unavailable state (observed reality matches hardening notes) |
| `/identity/me`, `/security/me`, `/deployment/health`, `/observability/*` | 200 | Non-blocking |
| `/health`, `/cache/status` | 200 | Diagnostics / keep-alive |

W1 note: when `SCIP_CONCURRENT_BOOT=true` is flipped on Render, the five core endpoints can also return the warming envelope (`{"scip_state":"warming"|"warmup_failed", "stage", "started_at", "confidence_state":"unavailable", "detail", "retry_after_seconds"}`, HTTP 200) until `/health.warmup.state == "warm"`. The rebuilt client must treat that envelope as a first-class state.

## Mock-field mapping (prototype `data.js` → server)

Disposition legend: `server:<path>` (render verbatim from payload) · `unavailable-state` (render the shared Unavailable primitive) · `contract-gap` (Gn — needs an explicit decision before dependent UI is built).

| Prototype key | Disposition |
|---|---|
| `ROLE_KEYS` / role set | server:`/command-centres.roles` keys (labels are presentational client constants) |
| `TRUST.snapshot_date`, `load_timestamp`, `tolerance_pct` | server:`roles[role].trust_bar.*` |
| `TRUST.sources_loaded`, `sources_missing`, `critical_lineage` | server:`trust_bar.sources_loaded/.sources_missing/.critical_lineage_counts` |
| `TRUST.contract` | server:`/command-centres.contract_version` |
| `TRUST.posture` (ok/warn/risk) | **contract-gap G1** (not server-provided; the deployed monolith derives "all critical lineaged" client-side, which is itself a derivation to retire) |
| `SIGNALS.*.hero`, `SIGNALS.*.side` (figures, deltas, bases) | server:`roles[role].cards[*].{display_value,reporting_basis,severity,lineage_refs}` (+ `resolved_insights` when insight cutover goes live) |
| `SIGNALS.*.question/answer/copy` (editorial sentences carrying figures) | **contract-gap G2** |
| `NARRATIVES[*].title/lede/quote` | **contract-gap G3** |
| `NARRATIVES[*].stats` | server:`forecast.display.*` / `cards[*]` where the metric exists; otherwise unavailable-state |
| `FORECAST.basis` | server:`/forecast/month-end.reporting_basis` + `.basis_disclosure` |
| `FORECAST.working_days.{elapsed,remaining,total}` | server:`.working_days.{elapsed_working_days,remaining_working_days,total_working_days}` |
| `FORECAST.display.*` (7 fields) | server:`.display.{mtd_total_collections,may_total_collections_target,current_daily_run_rate,required_daily_run_rate_remaining,projected_month_end_landing,projected_achievement_pct,gap_to_may_mdo_target}` |
| `FORECAST.runway.{actual_pct,projected_pct,target_pct}` | **contract-gap G12** (track geometry is not server-provided; see register) |
| `FORECAST.assumptions` | server:`.assumptions` |
| `TILES[role][*]` | server:`roles[role].cards[*]` (title, display_value, reporting_basis, severity, lineage) |
| per-focus tile selection | **contract-gap G5** (today a client keyword heuristic; placement payload exists backend-side but is shadow-mode) |
| `QUEUES[role][*]` | server:`/action-queues.roles[role].{account_actions,process_actions,management_actions,blocked_actions}[*]` (`entity_display`, `collector_rm_owner`, `display_amount`, `account_id`, `ageing_bucket`/`pr_status`, `reporting_basis`, `lineage_refs`) |
| queue header counts (ready/stale) | server:`/workflows.summary.state_counts` |
| `WORKFLOWS.q1.timeline` | server:`/workflows.records[*]` + `event_log[*].{event_type,actor_role,from_state,to_state,lineage_hash,created_at}` |
| `LINEAGE.*` (drawer chains) | server:`lineage_refs[*].{metric_key,source_file,sheet,cell_or_range,validation_status,confidence_state,reporting_basis,value,has_lineage}`; missing per-ref `snapshot_date` and lineage ref/hash → **contract-gap G6** |
| `LIVE_PULSE_BY_ROLE` (role-scoped doors) | **contract-gap G4** |
| `QUICKBALL_SUGGEST` | nav-intent suggestions stay client (navigation, no data); metric suggestions from quickball contract |
| `QUICKBALL_ANSWERS` | **deleted** — server:`/quickball/explain` (`status`, `answer`, `metric_key`, lineage, `blocked_untrusted_metric` envelope); free-text→metric resolution is **contract-gap G7** (refusal path applies) |
| `BLOCKED_ANSWER` | server:`/quickball/explain` blocked envelope |
| Entity selector (ContextStrip / Chrome) | **contract-gap G8** (no endpoint accepts an entity-scope parameter; client filtering is forbidden) |

## Contract-gap register (decisions required before Phase 2)

- **G1 — Trust posture**: `trust_bar` has no `ok/warn/risk` posture field and no "all critical lineaged" boolean. Options: (a) backend adds posture to `trust_bar`, (b) TrustRail renders only the raw server fields (counts, lists, dates) with no posture chip.
- **G2 — Live Pulse editorial**: the prototype's focus headers state figures in prose ("Calm on the surface, two pockets…"). No server payload carries this on `release`; `resolved_insights` (insight engine) is the intended carrier but ships in shadow mode. Options: (a) flip insight cutover for Live Pulse, (b) render structural questions only (no figure-bearing prose) until then, (c) add a narrative payload.
- **G3 — Narratives chapters**: no `/narratives` content endpoint exists. Without one, Story→Roadmap render as chapter shells: server-mappable stats verbatim + explicit unavailable-states for title/lede/quote. This is the biggest visual delta vs the prototype.
- **G4 — Role-scoped Live Pulse doors**: the three-door copy/metric per role (`LIVE_PULSE_BY_ROLE`) is not in `/command-centres`. Options: backend addition vs neutral fixed door copy with server metrics where mappable.
- **G5 — Per-focus card placement**: which cards belong to Current Signal vs Month Movement vs Risk & Action is today a client keyword heuristic. The backend placement engine (`section_placement.json`, placement_shadow) exists but is shadow-mode.
- **G6 — Lineage ref completeness**: metric lineage refs lack `snapshot_date` and a lineage reference/hash (workflow events do carry `lineage_hash`). The drawer renders what exists verbatim; missing fields render as unavailable rows unless the backend adds them.
- **G7 — Quickball free-text**: `/quickball/explain` answers by metric key. Mapping free text to metric keys client-side risks wrong-metric answers; per the locked rule the rebuild ships nav intents + explicit refusal for unmapped numeric questions.
- **G8 — Entity scoping**: no API accepts entity scope. The selector ships visually with Group active and non-group scopes explicitly marked unavailable (never client-filtered) until a server parameter exists.
- **G11 — `/persistence/summary` posture**: hardening notes list it blocking; the deployed monolith treats it optional; observed unseeded behavior is HTTP 500. Decide blocking vs optional for the rebuild startup gate.
- **G12 — Runway geometry**: track positions (`actual_pct` etc.) are not in the forecast payload. Either the backend adds display geometry, or the panel positions markers from server-provided working-day integers/achievement percentages as pure chart rendering (figures shown remain verbatim `display.*` strings) — needs an explicit call because it touches the no-client-arithmetic rule.

## Repo findings (disclosed)

- Two diverged monoliths exist: root `/src/App.jsx` carries the UAT hardening (URL normalization across 3 env names, bypass aliases, failure-class diagnostics, staging diagnostic panel, board→digests routing) while deployed `go-live-rc1/src/App.jsx` carries newer product surfaces (Quickball disk v3, Wave B insights) **without** the hardening. The rebuild's api/client layer merges both.
- `/notifications*` rejects the staging bypass actors (401 `authentication_failed`) — consistent with the hardening notes' "unavailable or blocked in staging".
- `/persistence/summary` 500s when demo records are unseeded (`required_demo_record_not_found`).


---

# Observed response shapes

Dict keys are real; values are reduced to type names. String samples are included only when they contain no digits, so no financial value, date, account id or amount is recorded here.

## `GET /command-centres` — HTTP 200

```json
{
 "status": "str \"ok\"",
 "contract_version": "str",
 "roles": {
  "board_cxo": {
   "role_label": "str \"Board/CXO\"",
   "purpose": "str",
   "trust_bar": {
    "snapshot_date": "str",
    "load_timestamp": "str",
    "platform_version": "str",
    "sources_loaded": [
     "str",
     "<12 item(s), shape of first shown>"
    ],
    "sources_missing": [
     "str",
     "<14 item(s), shape of first shown>"
    ],
    "critical_sources": [
     "str",
     "<5 item(s), shape of first shown>"
    ],
    "critical_lineage_counts": {
     "R18": "int",
     "R04": "int",
     "R02": "int",
     "R08": "int",
     "R36": "int"
    },
    "critical_validation_counts": {
     "R18": "int",
     "R04": "int",
     "R02": "int",
     "R08": "int",
     "R36": "int"
    },
    "no_silent_fallback": "bool",
    "tolerance_pct": "float"
   },
   "cards": [
    {
     "card_id": "str \"board_od_exposure\"",
     "title": "str \"Current OD exposure\"",
     "value": "float",
     "display_value": "str",
     "reporting_basis": "str",
     "action": "str",
     "severity": "str \"risk\"",
     "lineage_refs": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "lineage_bucket": "str \"OD_LINEAGE\"",
       "lineage_key": "str \"OD_TODAY\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "null"
      }
     ],
     "trust_state": "str \"lineaged\"",
     "lineage_display": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str",
       "has_lineage": "bool"
      }
     ]
    },
    "<5 item(s), shape of first shown>"
   ]
  },
  "cco_gm_agm": {
   "role_label": "str \"CCO/GM/AGM\"",
   "purpose": "str",
   "trust_bar": {
    "snapshot_date": "str",
    "load_timestamp": "str",
    "platform_version": "str",
    "sources_loaded": [
     "str",
     "<12 item(s), shape of first shown>"
    ],
    "sources_missing": [
     "str",
     "<14 item(s), shape of first shown>"
    ],
    "critical_sources": [
     "str",
     "<5 item(s), shape of first shown>"
    ],
    "critical_lineage_counts": {
     "R18": "int",
     "R04": "int",
     "R02": "int",
     "R08": "int",
     "R36": "int"
    },
    "critical_validation_counts": {
     "R18": "int",
     "R04": "int",
     "R02": "int",
     "R08": "int",
     "R36": "int"
    },
    "no_silent_fallback": "bool",
    "tolerance_pct": "float"
   },
   "cards": [
    {
     "card_id": "str \"ops_mtd_vs_may_target\"",
     "title": "str \"MTD collections vs May MDO target\"",
     "value": "float",
     "display_value": "str",
     "reporting_basis": "str \"Finance actual vs MDO target\"",
     "action": "str",
     "severity": "str \"risk\"",
     "lineage_refs": [
      {
       "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
       "lineage_bucket": "str",
       "lineage_key": "str \"mtd_total_collections\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str \"daily\"",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Finance\""
      },
      "<2 item(s), shape of first shown>"
     ],
     "trust_state": "str \"lineaged\"",
     "lineage_display": [
      {
       "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
       "source_file": "str",
       "sheet": "str \"daily\"",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Finance\"",
       "has_lineage": "bool"
      },
      "<2 item(s), shape of first shown>"
     ]
    },
    "<5 item(s), shape of first shown>"
   ]
  },
  "finance": {
   "role_label": "str \"Finance\"",
   "purpose": "str",
   "trust_bar": {
    "snapshot_date": "str",
    "load_timestamp": "str",
    "platform_version": "str",
    "sources_loaded": [
     "str",
     "<12 item(s), shape of first shown>"
    ],
    "sources_missing": [
     "str",
     "<14 item(s), shape of first shown>"
    ],
    "critical_sources": [
     "str",
     "<5 item(s), shape of first shown>"
    ],
    "critical_lineage_counts": {
     "R18": "int",
     "R04": "int",
     "R02": "int",
     "R08": "int",
     "R36": "int"
    },
    "critical_validation_counts": {
     "R18": "int",
     "R04": "int",
     "R02": "int",
     "R08": "int",
     "R36": "int"
    },
    "no_silent_fallback": "bool",
    "tolerance_pct": "float"
   },
   "cards": [
    {
     "card_id": "str \"finance_basis_control\"",
     "title": "str \"Finance actual vs MDO target basis\"",
     "value": "null",
     "display_value": "str \"Finance actuals / MDO targets\"",
     "reporting_basis": "str \"Finance + MDO\"",
     "action": "str",
     "severity": "str \"control\"",
     "lineage_refs": [
      {
       "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
       "lineage_bucket": "str",
       "lineage_key": "str \"mtd_total_collections\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str \"daily\"",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Finance\""
      },
      "<2 item(s), shape of first shown>"
     ],
     "trust_state": "str \"lineaged\"",
     "lineage_display": [
      {
       "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
       "source_file": "str",
       "sheet": "str \"daily\"",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Finance\"",
       "has_lineage": "bool"
      },
      "<2 item(s), shape of first shown>"
     ]
    },
    "<4 item(s), shape of first shown>"
   ]
  },
  "mis_qcg_admin": {
   "role_label": "str \"MIS/QCG/Admin\"",
   "purpose": "str",
   "trust_bar": {
    "snapshot_date": "str",
    "load_timestamp": "str",
    "platform_version": "str",
    "sources_loaded": [
     "str",
     "<12 item(s), shape of first shown>"
    ],
    "sources_missing": [
     "str",
     "<14 item(s), shape of first shown>"
    ],
    "critical_sources": [
     "str",
     "<5 item(s), shape of first shown>"
    ],
    "critical_lineage_counts": {
     "R18": "int",
     "R04": "int",
     "R02": "int",
     "R08": "int",
     "R36": "int"
    },
    "critical_validation_counts": {
     "R18": "int",
     "R04": "int",
     "R02": "int",
     "R08": "int",
     "R36": "int"
    },
    "no_silent_fallback": "bool",
    "tolerance_pct": "float"
   },
   "cards": [
    {
     "card_id": "str \"mis_lineage_coverage\"",
     "title": "str \"Critical lineage coverage\"",
     "value": {
      "R18": "int",
      "R04": "int",
      "R02": "int",
      "R08": "int",
      "R36": "int"
     },
     "display_value": "str",
     "reporting_basis": "str \"Data governance\"",
     "action": "str",
     "severity": "str \"control\"",
     "lineage_refs": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "lineage_bucket": "str \"OD_LINEAGE\"",
       "lineage_key": "str \"OD_TODAY\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "null",
       "contract_note": "str"
      }
     ],
     "trust_state": "str \"lineaged\"",
     "lineage_display": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Data governance\"",
       "has_lineage": "bool"
      }
     ]
    },
    "<2 item(s), shape of first shown>"
   ]
  },
  "collector_rm": {
   "role_label": "str \"Collector/RM\"",
   "purpose": "str",
   "trust_bar": {
    "snapshot_date": "str",
    "load_timestamp": "str",
    "platform_version": "str",
    "sources_loaded": [
     "str",
     "<12 item(s), shape of first shown>"
    ],
    "sources_missing": [
     "str",
     "<14 item(s), shape of first shown>"
    ],
    "critical_sources": [
     "str",
     "<5 item(s), shape of first shown>"
    ],
    "critical_lineage_counts": {
     "R18": "int",
     "R04": "int",
     "R02": "int",
     "R08": "int",
     "R36": "int"
    },
    "critical_validation_counts": {
     "R18": "int",
     "R04": "int",
     "R02": "int",
     "R08": "int",
     "R36": "int"
    },
    "no_silent_fallback": "bool",
    "tolerance_pct": "float"
   },
   "cards": [
    {
     "card_id": "str \"collector_od_priority\"",
     "title": "str \"OD follow-up pool\"",
     "value": "float",
     "display_value": "str",
     "reporting_basis": "str",
     "action": "str",
     "severity": "str \"risk\"",
     "lineage_refs": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "lineage_bucket": "str \"OD_LINEAGE\"",
       "lineage_key": "str \"OD_TODAY\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "null"
      }
     ],
     "trust_state": "str \"lineaged\"",
     "lineage_display": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str",
       "has_lineage": "bool"
      }
     ]
    },
    "<2 item(s), shape of first shown>"
   ]
  }
 },
 "role_order": [
  "str \"board_cxo\"",
  "<5 item(s), shape of first shown>"
 ],
 "guardrails": {
  "no_silent_fallback": "bool",
  "critical_cards_require_lineage_refs": "bool",
  "finance_vs_mdo_label_required": "bool",
  "entity_head_removed": "bool",
  "every_card_requires_reporting_basis": "bool",
  "every_card_requires_lineage_display": "bool",
  "month_end_forecast_assumptions_required": "bool",
  "resolved_insights_attached": "bool",
  "insight_cutover_mode": "str \"shadow\"",
  "placement_shadow_attached": "bool"
 },
 "forecast": {
  "status": "str \"ok\"",
  "contract_version": "str",
  "forecast_date": "str",
  "forecast_name": "str \"May month-end landing forecast\"",
  "reporting_basis": "str",
  "basis_disclosure": "str",
  "tolerance_pct": "float",
  "inputs": {
   "mtd_total_collections": "float",
   "mtd_da_total": "float",
   "mtd_new_sales_total": "float",
   "may_total_collections_target": "float",
   "may_da_target": "float",
   "may_new_sales_target": "float"
  },
  "working_days": {
   "status": "str",
   "elapsed_working_days": "int",
   "total_working_days": "int",
   "remaining_working_days": "int",
   "source": "str",
   "ratio": "float",
   "fraction_error": "float",
   "basis": "str",
   "lineage_refs": [
    {
     "metric_key": "str \"MONTH_TARGET_TOTAL\"",
     "lineage_bucket": "str",
     "lineage_key": "str \"month_target_total\"",
     "has_lineage": "bool",
     "source_file": "str",
     "sheet": "str \"daily\"",
     "cell_or_range": "str",
     "validation_status": "str \"passed\"",
     "confidence_state": "str \"live_validated\"",
     "reporting_basis": "str \"Finance\"",
     "value": "float"
    },
    "<2 item(s), shape of first shown>"
   ]
  },
  "outputs": {
   "current_daily_run_rate": "float",
   "required_daily_run_rate_remaining": "float",
   "projected_month_end_landing": "float",
   "gap_to_may_mdo_target": "float",
   "mtd_achievement_pct": "float",
   "projected_achievement_pct": "float",
   "mdo_prorata_target_as_of_snapshot": "float",
   "mdo_prorata_gap_as_of_snapshot": "float",
   "da_daily_run_rate": "float",
   "new_sales_daily_run_rate": "float"
  },
  "display": {
   "mtd_total_collections": "str",
   "may_total_collections_target": "str",
   "current_daily_run_rate": "str",
   "required_daily_run_rate_remaining": "str",
   "projected_month_end_landing": "str",
   "gap_to_may_mdo_target": "str",
   "mtd_achievement_pct": "str",
   "projected_achievement_pct": "str"
  },
  "assumptions": [
   "str",
   "<5 item(s), shape of first shown>"
  ],
  "lineage_refs": [
   {
    "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
    "lineage_bucket": "str",
    "lineage_key": "str \"mtd_total_collections\"",
    "has_lineage": "bool",
    "source_file": "str",
    "sheet": "str \"daily\"",
    "cell_or_range": "str",
    "validation_status": "str \"passed\"",
    "confidence_state": "str \"live_validated\"",
    "reporting_basis": "str \"Finance\"",
    "value": "float"
   },
   "<8 item(s), shape of first shown>"
  ],
  "guardrails": {
   "no_silent_fallback": "bool",
   "critical_forecasts_require_lineage": "bool",
   "forecast_assumptions_required": "bool",
   "finance_vs_mdo_label_required": "bool"
  }
 },
 "resolved_insights": {
  "status": "str \"ok\"",
  "mode": "str \"shadow\"",
  "registry_version": "str",
  "cutover": {
   "wave": "str \"B\"",
   "default_mode": "str \"shadow\"",
   "live_surfaces": [
    {
     "route": "str \"live_pulse\"",
     "focus": "str \"current_signal\""
    },
    "<3 item(s), shape of first shown>"
   ],
   "gate_note": "str"
  },
  "roles": {
   "board_cxo": [
    {
     "card_id": "str \"board_od_exposure\"",
     "title": "str \"Current OD exposure\"",
     "reporting_basis": "str",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "lineage_bucket": "str \"OD_LINEAGE\"",
       "lineage_key": "str \"OD_TODAY\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "null"
      }
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"critical\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"current_signal\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"Current OD exposure\"",
     "value": "float",
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"risk\"",
     "outcome": "null"
    },
    "<4 item(s), shape of first shown>"
   ],
   "cco_gm_agm": [
    {
     "card_id": "str \"ops_mtd_vs_may_target\"",
     "title": "str \"MTD collections vs May MDO target\"",
     "reporting_basis": "str \"Finance actual vs MDO target\"",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
       "lineage_bucket": "str",
       "lineage_key": "str \"mtd_total_collections\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str \"daily\"",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Finance\""
      },
      "<2 item(s), shape of first shown>"
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"critical\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"risk_action\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"MTD collections vs May MDO target\"",
     "value": "float",
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"risk\"",
     "outcome": "null"
    },
    "<4 item(s), shape of first shown>"
   ],
   "finance": [
    {
     "card_id": "str \"finance_basis_control\"",
     "title": "str \"Finance actual vs MDO target basis\"",
     "reporting_basis": "str \"Finance + MDO\"",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
       "lineage_bucket": "str",
       "lineage_key": "str \"mtd_total_collections\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str \"daily\"",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Finance\""
      },
      "<2 item(s), shape of first shown>"
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"standard\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"narratives\"",
      "focus": "str \"story\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"Finance actual vs MDO target basis\"",
     "value": "null",
     "value_display": "str \"Finance actuals / MDO targets\"",
     "display_value": "str \"Finance actuals / MDO targets\"",
     "severity": "str \"control\"",
     "outcome": "null"
    },
    "<3 item(s), shape of first shown>"
   ],
   "mis_qcg_admin": [
    {
     "card_id": "str \"mis_lineage_coverage\"",
     "title": "str \"Critical lineage coverage\"",
     "reporting_basis": "str \"Data governance\"",
     "action": "str",
     "lineage_refs": [
      "<empty>"
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"standard\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"current_signal\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"Critical lineage coverage\"",
     "value": {
      "R18": "int",
      "R04": "int",
      "R02": "int",
      "R08": "int",
      "R36": "int"
     },
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"control\"",
     "outcome": "null"
    },
    "<2 item(s), shape of first shown>"
   ],
   "collector_rm": [
    {
     "card_id": "str \"collector_od_priority\"",
     "title": "str \"OD follow-up pool\"",
     "reporting_basis": "str",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "lineage_bucket": "str \"OD_LINEAGE\"",
       "lineage_key": "str \"OD_TODAY\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "null"
      }
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"critical\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"risk_action\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"OD follow-up pool\"",
     "value": "float",
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"risk\"",
     "outcome": "null"
    },
    "<2 item(s), shape of first shown>"
   ]
  },
  "guardrails": {
   "no_silent_fallback": "bool",
   "critical_requires_lineage": "bool",
   "frames_never_originate_numbers": "bool",
   "delta_requires_prior_else_neutral": "bool"
  },
  "blocked_live": [
   "<empty>"
  ],
  "wave_b_blocked_preview": [
   "<empty>"
  ]
 },
 "shadow_insights": {
  "status": "str \"ok\"",
  "mode": "str \"shadow\"",
  "registry_version": "str",
  "cutover": {
   "wave": "str \"B\"",
   "default_mode": "str \"shadow\"",
   "live_surfaces": [
    {
     "route": "str \"live_pulse\"",
     "focus": "str \"current_signal\""
    },
    "<3 item(s), shape of first shown>"
   ],
   "gate_note": "str"
  },
  "roles": {
   "board_cxo": [
    {
     "card_id": "str \"board_od_exposure\"",
     "title": "str \"Current OD exposure\"",
     "reporting_basis": "str",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "lineage_bucket": "str \"OD_LINEAGE\"",
       "lineage_key": "str \"OD_TODAY\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "null"
      }
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"critical\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"current_signal\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"Current OD exposure\"",
     "value": "float",
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"risk\"",
     "outcome": "null"
    },
    "<4 item(s), shape of first shown>"
   ],
   "cco_gm_agm": [
    {
     "card_id": "str \"ops_mtd_vs_may_target\"",
     "title": "str \"MTD collections vs May MDO target\"",
     "reporting_basis": "str \"Finance actual vs MDO target\"",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
       "lineage_bucket": "str",
       "lineage_key": "str \"mtd_total_collections\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str \"daily\"",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Finance\""
      },
      "<2 item(s), shape of first shown>"
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"critical\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"risk_action\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"MTD collections vs May MDO target\"",
     "value": "float",
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"risk\"",
     "outcome": "null"
    },
    "<4 item(s), shape of first shown>"
   ],
   "finance": [
    {
     "card_id": "str \"finance_basis_control\"",
     "title": "str \"Finance actual vs MDO target basis\"",
     "reporting_basis": "str \"Finance + MDO\"",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
       "lineage_bucket": "str",
       "lineage_key": "str \"mtd_total_collections\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str \"daily\"",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Finance\""
      },
      "<2 item(s), shape of first shown>"
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"standard\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"narratives\"",
      "focus": "str \"story\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"Finance actual vs MDO target basis\"",
     "value": "null",
     "value_display": "str \"Finance actuals / MDO targets\"",
     "display_value": "str \"Finance actuals / MDO targets\"",
     "severity": "str \"control\"",
     "outcome": "null"
    },
    "<3 item(s), shape of first shown>"
   ],
   "mis_qcg_admin": [
    {
     "card_id": "str \"mis_lineage_coverage\"",
     "title": "str \"Critical lineage coverage\"",
     "reporting_basis": "str \"Data governance\"",
     "action": "str",
     "lineage_refs": [
      "<empty>"
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"standard\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"current_signal\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"Critical lineage coverage\"",
     "value": {
      "R18": "int",
      "R04": "int",
      "R02": "int",
      "R08": "int",
      "R36": "int"
     },
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"control\"",
     "outcome": "null"
    },
    "<2 item(s), shape of first shown>"
   ],
   "collector_rm": [
    {
     "card_id": "str \"collector_od_priority\"",
     "title": "str \"OD follow-up pool\"",
     "reporting_basis": "str",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "lineage_bucket": "str \"OD_LINEAGE\"",
       "lineage_key": "str \"OD_TODAY\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "null"
      }
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"critical\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"risk_action\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"OD follow-up pool\"",
     "value": "float",
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"risk\"",
     "outcome": "null"
    },
    "<2 item(s), shape of first shown>"
   ]
  },
  "guardrails": {
   "no_silent_fallback": "bool",
   "critical_requires_lineage": "bool",
   "frames_never_originate_numbers": "bool",
   "delta_requires_prior_else_neutral": "bool"
  },
  "blocked_live": [
   "<empty>"
  ],
  "wave_b_blocked_preview": [
   "<empty>"
  ]
 },
 "placement_shadow": {
  "status": "str \"ok\"",
  "mode": "str \"shadow\"",
  "roles": {
   "board_cxo": [
    {
     "card_id": "str \"board_od_exposure\"",
     "title": "str \"Current OD exposure\"",
     "reporting_basis": "str",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "lineage_bucket": "str \"OD_LINEAGE\"",
       "lineage_key": "str \"OD_TODAY\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "null"
      }
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"critical\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"current_signal\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"Current OD exposure\"",
     "value": "float",
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"risk\"",
     "outcome": "null"
    },
    "<4 item(s), shape of first shown>"
   ],
   "cco_gm_agm": [
    {
     "card_id": "str \"ops_mtd_vs_may_target\"",
     "title": "str \"MTD collections vs May MDO target\"",
     "reporting_basis": "str \"Finance actual vs MDO target\"",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
       "lineage_bucket": "str",
       "lineage_key": "str \"mtd_total_collections\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str \"daily\"",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Finance\""
      },
      "<2 item(s), shape of first shown>"
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"critical\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"risk_action\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"MTD collections vs May MDO target\"",
     "value": "float",
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"risk\"",
     "outcome": "null"
    },
    "<4 item(s), shape of first shown>"
   ],
   "finance": [
    {
     "card_id": "str \"finance_basis_control\"",
     "title": "str \"Finance actual vs MDO target basis\"",
     "reporting_basis": "str \"Finance + MDO\"",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
       "lineage_bucket": "str",
       "lineage_key": "str \"mtd_total_collections\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str \"daily\"",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str \"Finance\""
      },
      "<2 item(s), shape of first shown>"
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"standard\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"narratives\"",
      "focus": "str \"story\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"Finance actual vs MDO target basis\"",
     "value": "null",
     "value_display": "str \"Finance actuals / MDO targets\"",
     "display_value": "str \"Finance actuals / MDO targets\"",
     "severity": "str \"control\"",
     "outcome": "null"
    },
    "<3 item(s), shape of first shown>"
   ],
   "mis_qcg_admin": [
    {
     "card_id": "str \"mis_lineage_coverage\"",
     "title": "str \"Critical lineage coverage\"",
     "reporting_basis": "str \"Data governance\"",
     "action": "str",
     "lineage_refs": [
      "<empty>"
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"standard\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"current_signal\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"Critical lineage coverage\"",
     "value": {
      "R18": "int",
      "R04": "int",
      "R02": "int",
      "R08": "int",
      "R36": "int"
     },
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"control\"",
     "outcome": "null"
    },
    "<2 item(s), shape of first shown>"
   ],
   "collector_rm": [
    {
     "card_id": "str \"collector_od_priority\"",
     "title": "str \"OD follow-up pool\"",
     "reporting_basis": "str",
     "action": "str",
     "lineage_refs": [
      {
       "metric_key": "str \"OD_TODAY\"",
       "lineage_bucket": "str \"OD_LINEAGE\"",
       "lineage_key": "str \"OD_TODAY\"",
       "has_lineage": "bool",
       "source_file": "str",
       "sheet": "str",
       "cell_or_range": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "null"
      }
     ],
     "trust_state": "str \"lineaged\"",
     "criticality": "str \"critical\"",
     "governance_state": "str \"governed\"",
     "surface_placement": {
      "route": "str \"live_pulse\"",
      "focus": "str \"risk_action\"",
      "submodule": "null",
      "slot": "int",
      "priority": "int"
     },
     "target_state": "str \"resolved\"",
     "blocked_reason": "null",
     "render_mode": "str \"shadow\"",
     "status": "str \"shadow\"",
     "headline": "str \"OD follow-up pool\"",
     "value": "float",
     "value_display": "str",
     "display_value": "str",
     "severity": "str \"risk\"",
     "outcome": "null"
    },
    "<2 item(s), shape of first shown>"
   ]
  },
  "violations": [
   "<empty>"
  ],
  "single_source_constants": [
   "str \"CY_ADV_MIX_YTD\"",
   "<9 item(s), shape of first shown>"
  ],
  "rules_enforced": [
   "str",
   "<5 item(s), shape of first shown>"
  ],
  "binder_version": "str"
 }
}
```

## `GET /forecast/month-end` — HTTP 200

```json
{
 "status": "str \"ok\"",
 "contract_version": "str",
 "forecast_date": "str",
 "forecast_name": "str \"May month-end landing forecast\"",
 "reporting_basis": "str",
 "basis_disclosure": "str",
 "tolerance_pct": "float",
 "inputs": {
  "mtd_total_collections": "float",
  "mtd_da_total": "float",
  "mtd_new_sales_total": "float",
  "may_total_collections_target": "float",
  "may_da_target": "float",
  "may_new_sales_target": "float"
 },
 "working_days": {
  "status": "str",
  "elapsed_working_days": "int",
  "total_working_days": "int",
  "remaining_working_days": "int",
  "source": "str",
  "ratio": "float",
  "fraction_error": "float",
  "basis": "str",
  "lineage_refs": [
   {
    "metric_key": "str \"MONTH_TARGET_TOTAL\"",
    "lineage_bucket": "str",
    "lineage_key": "str \"month_target_total\"",
    "has_lineage": "bool",
    "source_file": "str",
    "sheet": "str \"daily\"",
    "cell_or_range": "str",
    "validation_status": "str \"passed\"",
    "confidence_state": "str \"live_validated\"",
    "reporting_basis": "str \"Finance\"",
    "value": "float"
   },
   "<2 item(s), shape of first shown>"
  ]
 },
 "outputs": {
  "current_daily_run_rate": "float",
  "required_daily_run_rate_remaining": "float",
  "projected_month_end_landing": "float",
  "gap_to_may_mdo_target": "float",
  "mtd_achievement_pct": "float",
  "projected_achievement_pct": "float",
  "mdo_prorata_target_as_of_snapshot": "float",
  "mdo_prorata_gap_as_of_snapshot": "float",
  "da_daily_run_rate": "float",
  "new_sales_daily_run_rate": "float"
 },
 "display": {
  "mtd_total_collections": "str",
  "may_total_collections_target": "str",
  "current_daily_run_rate": "str",
  "required_daily_run_rate_remaining": "str",
  "projected_month_end_landing": "str",
  "gap_to_may_mdo_target": "str",
  "mtd_achievement_pct": "str",
  "projected_achievement_pct": "str"
 },
 "assumptions": [
  "str",
  "<5 item(s), shape of first shown>"
 ],
 "lineage_refs": [
  {
   "metric_key": "str \"MTD_TOTAL_COLLECTIONS\"",
   "lineage_bucket": "str",
   "lineage_key": "str \"mtd_total_collections\"",
   "has_lineage": "bool",
   "source_file": "str",
   "sheet": "str \"daily\"",
   "cell_or_range": "str",
   "validation_status": "str \"passed\"",
   "confidence_state": "str \"live_validated\"",
   "reporting_basis": "str \"Finance\"",
   "value": "float"
  },
  "<8 item(s), shape of first shown>"
 ],
 "guardrails": {
  "no_silent_fallback": "bool",
  "critical_forecasts_require_lineage": "bool",
  "forecast_assumptions_required": "bool",
  "finance_vs_mdo_label_required": "bool"
 }
}
```

## `GET /action-queues` — HTTP 200

```json
{
 "contract_version": "str",
 "status": "str \"ready_account_level_guarded\"",
 "generated_at": "str",
 "guardrails": {
  "tolerance_pct": "float",
  "no_silent_fallback": "bool",
  "locked_hierarchy": "str",
  "role_model": [
   "str \"Board/CXO\"",
   "<5 item(s), shape of first shown>"
  ],
  "removed_role": "str \"Entity Head\"",
  "account_action_gate": "str",
  "liquid_glass_gate": "str"
 },
 "source_availability": {
  "R10": "str \"loaded\"",
  "R17": "str \"loaded\"",
  "R20": "str \"loaded\"",
  "R30": "str \"loaded\"",
  "R31": "str \"loaded\"",
  "R32": "str \"loaded\"",
  "R34": "str \"missing\"",
  "R38": "str \"loaded\"",
  "R09": "str \"loaded\""
 },
 "data_grain_disclosure": {
  "current_grain": "str \"account_unit_with_project_process_enrichment\"",
  "true_account_level_available": "bool",
  "rule": "str"
 },
 "facts_summary": {
  "r10_allocations": "int",
  "r10_ptp_facts": "int",
  "r34_termination_facts": "int",
  "r31_pr_issues": "int",
  "r32_collector_metrics": "int",
  "r32_receipt_facts": "int",
  "r30_collector_feedback": "int",
  "r17_spa_project_facts": "int",
  "r09_project_collection_facts": "int",
  "r20_tat_facts": "int",
  "r38_risk_facts": "int",
  "collector_account_actions_ready": "int",
  "termination_review_actions_ready": "int",
  "finance_pr_actions_ready": "int",
  "process_actions_ready": "int"
 },
 "roles": {
  "mis_qcg_admin": {
   "role": "str \"mis_qcg_admin\"",
   "status": "str \"ready\"",
   "headline": "str",
   "disclosure": "str",
   "account_actions": [
    {
     "action_id": "str",
     "action_type": "str \"finance_pr_quality_exception\"",
     "grain": "str \"payment_request_account_unit\"",
     "role_visibility": [
      "str \"finance\"",
      "<2 item(s), shape of first shown>"
     ],
     "status": "str \"ready\"",
     "title": "str",
     "summary": "str",
     "recommended_action": "str",
     "severity": "str \"risk\"",
     "account_id": "str",
     "unit": "str",
     "customer_name": "null",
     "collector_rm_owner": "str \"Hussein\"",
     "entity_code": "str \"sobha_dubai\"",
     "entity_display": "str \"Sobha Dubai\"",
     "amount_aed": "float",
     "display_amount": "str",
     "ageing_bucket": "str \"process_exception\"",
     "pr_status": "str \"Pending for Accounts Approval\"",
     "receipt_status": "str",
     "project": "str \"Sobha\"",
     "reporting_basis": "str",
     "confidence_state": "str \"live_validated_pr_exception_lineaged\"",
     "lineage_refs": [
      {
       "metric_key": "str",
       "metric_label": "str \"Payment request quality issue\"",
       "has_lineage": "bool",
       "source_code": "str",
       "source_file": "str",
       "sheet": "str \"PR Data\"",
       "cell_or_range": "str",
       "snapshot_date": "str",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str"
      }
     ]
    },
    "<15 item(s), shape of first shown>"
   ],
   "process_actions": [
    {
     "action_id": "str \"coverage::Total\"",
     "action_type": "str \"coverage_gap_review\"",
     "grain": "str \"collector\"",
     "role_visibility": [
      "str \"cco_gm_agm\"",
      "<2 item(s), shape of first shown>"
     ],
     "status": "str \"ready\"",
     "title": "str \"Coverage gap \u00b7 Total\"",
     "summary": "str",
     "recommended_action": "str",
     "severity": "str \"risk\"",
     "collector_rm_owner": "str \"Total\"",
     "amount_aed": "float",
     "display_amount": "str",
     "ageing_bucket": "str \"coverage_gap\"",
     "reporting_basis": "str",
     "confidence_state": "str \"live_validated_collector_coverage_lineaged\"",
     "lineage_refs": [
      {
       "metric_key": "str \"COVERAGE_Total\"",
       "metric_label": "str \"Collector not-worked coverage\"",
       "has_lineage": "bool",
       "source_code": "str",
       "source_file": "str",
       "sheet": "str \"Agent - Coverage\"",
       "cell_or_range": "str",
       "snapshot_date": "null",
       "validation_status": "str \"passed\"",
       "confidence_state": "str \"live_validated\"",
       "reporting_basis": "str"
      }
     ]
    },
    "<17 item(s), shape of first shown>"
   ],
   "management_actions": [
    "<empty>"
   ],
   "required_source_fields": [
    "str \"source_lineage\"",
    "<3 item(s), shape of first shown>"
   ],
   "reporting_basis": "str"
  }
 },
 "validations": {
  "passed": "bool",
  "checks": {
   "all_visible_actions_have_lineage": "bool",
   "account_actions_have_owner_entity_amount_ageing_or_process_status": "bool",
   "collector_role_has_only_collector_visible_account_actions": "bool",
   "finance_role_has_no_collector_call_ptp_actions": "bool",
   "entity_head_removed": "bool",
   "reporting_basis_present": "bool"
  },
  "checked_action_count": "int",
  "checked_account_action_count": "int"
 },
 "lineage_sample": [
  {
   "metric_key": "str",
   "metric_label": "str \"Payment request quality issue\"",
   "has_lineage": "bool",
   "source_code": "str",
   "source_file": "str",
   "sheet": "str \"PR Data\"",
   "cell_or_range": "str",
   "snapshot_date": "str",
   "validation_status": "str \"passed\"",
   "confidence_state": "str \"live_validated\"",
   "reporting_basis": "str"
  },
  "<4 item(s), shape of first shown>"
 ],
 "source_notes": {
  "R17": "str",
  "R38": "str",
  "R09": "str",
  "R30_R32": "str"
 },
 "rbac": {
  "actor": {
   "actor_id": "str \"mis_admin_demo\"",
   "actor_name": "str \"MIS/QCG/Admin\"",
   "role": "str \"mis_qcg_admin\"",
   "role_label": "str \"MIS/QCG/Admin\"",
   "entity_scope": [
    "str \"Group\""
   ],
   "collector_id": "null",
   "environment": "str \"local\"",
   "permissions": [
    "str \"read:action_queues\"",
    "<16 item(s), shape of first shown>"
   ]
  },
  "filtered": "bool",
  "visible_roles": [
   "str \"mis_qcg_admin\"",
   "<4 item(s), shape of first shown>"
  ]
 }
}
```

## `GET /workflows` — HTTP 200

```json
{
 "contract_version": "str",
 "status": "str \"ready_workflow_tracking_guarded\"",
 "generated_at": "str",
 "workflow_states": [
  "str \"queued\"",
  "<8 item(s), shape of first shown>"
 ],
 "guardrails": {
  "tolerance_pct": "float",
  "no_silent_fallback": "bool",
  "role_model": [
   "str \"Board/CXO\"",
   "<5 item(s), shape of first shown>"
  ],
  "removed_role": "str \"Entity Head\"",
  "account_action_gate": "str",
  "lineage_rule": "str",
  "liquid_glass_rule": "str"
 },
 "permission_model": {
  "collector_rm": {
   "can_assign": "bool",
   "can_reassign": "bool",
   "can_set_due_date": "bool",
   "can_update_disposition": "bool",
   "can_attach_evidence": "bool",
   "can_close": "bool",
   "allowed_action_visibility": "str",
   "closure_requires_evidence": "bool"
  },
  "cco_gm_agm": {
   "can_assign": "bool",
   "can_reassign": "bool",
   "can_set_due_date": "bool",
   "can_update_disposition": "bool",
   "can_attach_evidence": "bool",
   "can_close": "bool",
   "allowed_action_visibility": "str",
   "closure_requires_evidence": "bool"
  },
  "finance": {
   "can_assign": "bool",
   "can_reassign": "bool",
   "can_set_due_date": "bool",
   "can_update_disposition": "bool",
   "can_attach_evidence": "bool",
   "can_close": "bool",
   "allowed_action_visibility": "str",
   "closure_requires_evidence": "bool"
  },
  "mis_qcg_admin": {
   "can_assign": "bool",
   "can_reassign": "bool",
   "can_set_due_date": "bool",
   "can_update_disposition": "bool",
   "can_attach_evidence": "bool",
   "can_close": "bool",
   "allowed_action_visibility": "str",
   "closure_requires_evidence": "bool"
  }
 },
 "summary": {
  "workflow_count": "int",
  "event_count": "int",
  "state_counts": {
   "queued": "int",
   "assigned": "int",
   "in_progress": "int",
   "promised": "int",
   "escalated": "int",
   "closed": "int",
   "stale": "int",
   "blocked": "int"
  },
  "lineaged_event_count": "int"
 },
 "records": [
  {
   "workflow_id": "str \"wf::coverage::Total\"",
   "source_action_id": "str \"coverage::Total\"",
   "action_type": "str \"coverage_gap_review\"",
   "grain": "str \"collector\"",
   "title": "str \"Coverage gap \u00b7 Total\"",
   "summary": "str",
   "recommended_action": "str",
   "role_visibility": [
    "str \"cco_gm_agm\"",
    "<2 item(s), shape of first shown>"
   ],
   "workflow_state": "str \"blocked\"",
   "assigned_owner": "str \"Total\"",
   "original_owner": "str \"Total\"",
   "due_date": "null",
   "disposition": "null",
   "closure_reason": "null",
   "closed_at": "null",
   "stale_reason": "null",
   "blocked_reason": "str \"missing_owner_entity_amount_or_ageing_status\"",
   "evidence_attachments": [
    "<empty>"
   ],
   "event_count": "int",
   "source_snapshot": {
    "account_id": "null",
    "unit": "null",
    "customer_name": "null",
    "project": "null",
    "sub_project": "null",
    "collector_rm_owner": "str \"Total\"",
    "manager_name": "null",
    "entity_code": "null",
    "entity_display": "null",
    "parent_entity_code": "null",
    "parent_entity_display": "null",
    "amount_aed": "float",
    "display_amount": "str",
    "ageing_bucket": "str \"coverage_gap\"",
    "ptp_date": "null",
    "ptp_amount_aed": "null",
    "ptp_status": "null",
    "pr_status": "null",
    "escalation_status": "null",
    "reporting_basis": "str",
    "confidence_state": "str \"live_validated_collector_coverage_lineaged\""
   },
   "immutable_lineage_refs": [
    {
     "metric_key": "str \"COVERAGE_Total\"",
     "metric_label": "str \"Collector not-worked coverage\"",
     "has_lineage": "bool",
     "source_code": "str",
     "source_file": "str",
     "sheet": "str \"Agent - Coverage\"",
     "cell_or_range": "str",
     "snapshot_date": "null",
     "validation_status": "str \"passed\"",
     "confidence_state": "str \"live_validated\"",
     "reporting_basis": "str"
    }
   ],
   "lineage_hash": "str",
   "source_gate": {
    "assignable": "bool",
    "failures": [
     "str \"missing_owner_entity_amount_or_ageing_status\""
    ],
    "rule": "str"
   },
   "created_at": "str",
   "updated_at": "str"
  },
  "<42 item(s), shape of first shown>"
 ],
 "event_log": [
  {
   "event_id": "str",
   "workflow_id": "str \"wf::coverage::Total\"",
   "source_action_id": "str \"coverage::Total\"",
   "event_type": "str \"blocked\"",
   "actor_role": "str \"system\"",
   "actor": "str",
   "from_state": "str \"none\"",
   "to_state": "str \"blocked\"",
   "event_payload": {
    "source_action_title": "str \"Coverage gap \u00b7 Total\""
   },
   "immutable_lineage_refs": [
    {
     "metric_key": "str \"COVERAGE_Total\"",
     "metric_label": "str \"Collector not-worked coverage\"",
     "has_lineage": "bool",
     "source_code": "str",
     "source_file": "str",
     "sheet": "str \"Agent - Coverage\"",
     "cell_or_range": "str",
     "snapshot_date": "null",
     "validation_status": "str \"passed\"",
     "confidence_state": "str \"live_validated\"",
     "reporting_basis": "str"
    }
   ],
   "lineage_hash": "str",
   "created_at": "str"
  },
  "<42 item(s), shape of first shown>"
 ],
 "validations": {
  "passed": "bool",
  "checks": {
   "all_records_have_immutable_lineage": "bool",
   "all_assignable_records_pass_source_gate": "bool",
   "all_queued_or_active_records_have_owner_entity_amount_status": "bool",
   "all_events_have_immutable_lineage_hash": "bool",
   "all_states_are_allowed": "bool",
   "entity_head_removed": "bool",
   "closed_records_have_closure_reason": "bool"
  },
  "checked_record_count": "int",
  "checked_event_count": "int"
 },
 "rbac": {
  "actor": {
   "actor_id": "str \"mis_admin_demo\"",
   "actor_name": "str \"MIS/QCG/Admin\"",
   "role": "str \"mis_qcg_admin\"",
   "role_label": "str \"MIS/QCG/Admin\"",
   "entity_scope": [
    "str \"Group\""
   ],
   "collector_id": "null",
   "environment": "str \"local\"",
   "permissions": [
    "str \"read:action_queues\"",
    "<16 item(s), shape of first shown>"
   ]
  },
  "filtered": "bool",
  "visible_workflow_count": "int"
 }
}
```

## `GET /quickball/explain` — HTTP 200

```json
{
 "status": "str \"answered\"",
 "role": {
  "label": "str \"Board/CXO\"",
  "purpose": "str",
  "tone": "str \"executive\"",
  "focus": [
   "str \"variance\"",
   "<4 item(s), shape of first shown>"
  ]
 },
 "metric_key": "str \"OD_TODAY\"",
 "metric_label": "str \"Group overdue today\"",
 "value": "float",
 "display_value": "str",
 "unit": "str \"AED\"",
 "reporting_basis": "str",
 "source_code": "str",
 "business_definition": "str",
 "answer": "str",
 "role_interpretation": "str",
 "lineage": {
  "metric_key": "str \"OD_TODAY\"",
  "metric_label": "str",
  "value": "float",
  "unit": "str \"AED\"",
  "source_code": "str",
  "source_file": "str",
  "sheet": "str",
  "cell_or_range": "str",
  "snapshot_date": "str",
  "extraction_method": "str \"positional_row_scan\"",
  "entity_scope": "str \"group\"",
  "business_definition": "str",
  "validation_status": "str \"passed\"",
  "confidence_state": "str \"live_validated\"",
  "last_loaded_at": "str"
 },
 "guardrail": {
  "critical_metric": "bool",
  "no_silent_fallback": "bool",
  "requires_lineage": "bool",
  "lineage_gate_passed": "bool"
 }
}
```

## `GET /persistence/summary` — HTTP 500

```json
{
 "detail": "str \"required_demo_record_not_found\""
}
```

## `GET /notifications` — HTTP 401

```json
{
 "status": "str \"denied\"",
 "reason": "str \"authentication_failed\""
}
```

## `GET /notifications/digests` — HTTP 401

```json
{
 "status": "str \"denied\"",
 "reason": "str \"authentication_failed\""
}
```

## `GET /identity/me` — HTTP 200

```json
{
 "contract_version": "str",
 "actor": {
  "actor_id": "str \"mis_admin_demo\"",
  "actor_name": "str \"MIS/QCG/Admin\"",
  "role": "str \"mis_qcg_admin\"",
  "role_label": "str \"MIS/QCG/Admin\"",
  "entity_scope": [
   "str \"Group\""
  ],
  "collector_id": "null",
  "environment": "str \"local\"",
  "permissions": [
   "str \"read:action_queues\"",
   "<16 item(s), shape of first shown>"
  ]
 },
 "auth_mode": "str \"local_dev\""
}
```

## `GET /security/me` — HTTP 200

```json
{
 "contract_version": "str",
 "actor": {
  "actor_id": "str \"mis_admin_demo\"",
  "actor_name": "str \"MIS/QCG/Admin\"",
  "role": "str \"mis_qcg_admin\"",
  "role_label": "str \"MIS/QCG/Admin\"",
  "entity_scope": [
   "str \"Group\""
  ],
  "collector_id": "null",
  "environment": "str \"local\"",
  "permissions": [
   "str \"read:action_queues\"",
   "<16 item(s), shape of first shown>"
  ]
 }
}
```

## `GET /deployment/health` — HTTP 200

```json
{
 "contract_version": "str",
 "status": "str \"needs_attention\"",
 "generated_at": "str",
 "environment_config": {
  "environment": "str \"local\"",
  "frontend_url": "str",
  "backend_url": "str",
  "audit_db": "str",
  "backup_dir": "str",
  "cors_allowed_origins": [
   "str"
  ],
  "auth_mode": "str \"local_dev\"",
  "secrets_expected": [
   "str \"SCIP_AUDIT_DB\""
  ],
  "secrets_present": [
   "<empty>"
  ],
  "secrets_missing": [
   "str \"SCIP_AUDIT_DB\""
  ],
  "debug_enabled": "bool"
 },
 "checks": {
  "environment_named": "bool",
  "cors_origins_configured": "bool",
  "no_wildcard_cors_in_nonlocal": "bool",
  "auth_mode_declared": "bool",
  "required_secrets_present": "bool",
  "debug_disabled_for_nonlocal": "bool",
  "migrations_ok": "bool",
  "security_tables_exist": "bool",
  "denial_audit_accessible": "bool",
  "backup_dir_configured": "bool"
 },
 "migration_status": "str \"ok\"",
 "table_count": "int",
 "denial_count": "int",
 "hardening_notes": [
  "str",
  "<3 item(s), shape of first shown>"
 ]
}
```

## `GET /observability/summary` — HTTP 200

```json
{
 "contract_version": "str",
 "generated_at": "str",
 "event_count": "int",
 "metrics_catalog": [
  "str \"ingestion_latency_ms\"",
  "<20 item(s), shape of first shown>"
 ],
 "counters": {},
 "timings": {
  "api_request_latency_ms": {
   "count": "int",
   "p50_ms": "float",
   "p95_ms": "float",
   "max_ms": "float"
  }
 },
 "api_error_rate_pct": "float",
 "cache_entries": "int",
 "active_alerts": [
  "<empty>"
 ],
 "actor_role": "str \"mis_qcg_admin\""
}
```

## `GET /observability/alerts` — HTTP 200

```json
{
 "contract_version": "str",
 "generated_at": "str",
 "alerts": [
  {
   "alert_key": "str",
   "severity": "str \"medium\"",
   "threshold": "int",
   "actual": "float"
  }
 ],
 "thresholds": {
  "stale_critical_source_hours": "int",
  "missing_critical_lineage_count": "int",
  "migration_failure_count": "int",
  "backup_failure_count": "int",
  "rbac_denials_per_15m_high": "int",
  "slow_endpoint_p95_ms": "int",
  "failed_export_count": "int",
  "api_error_rate_pct_high": "float",
  "adapter_failure_count_high": "int",
  "quickball_blocked_answers_per_hour_high": "int"
 }
}
```

## `GET /observability/dashboards` — HTTP 200

```json
{
 "contract_version": "str",
 "generated_at": "str",
 "dashboards": [
  {
   "dashboard_id": "str \"executive_reliability_overview\"",
   "title": "str \"SCIP Reliability Overview\"",
   "surface": "str",
   "panels": [
    "str",
    "<5 item(s), shape of first shown>"
   ]
  },
  "<4 item(s), shape of first shown>"
 ],
 "alert_thresholds": {
  "stale_critical_source_hours": "int",
  "missing_critical_lineage_count": "int",
  "migration_failure_count": "int",
  "backup_failure_count": "int",
  "rbac_denials_per_15m_high": "int",
  "slow_endpoint_p95_ms": "int",
  "failed_export_count": "int",
  "api_error_rate_pct_high": "float",
  "adapter_failure_count_high": "int",
  "quickball_blocked_answers_per_hour_high": "int"
 },
 "liquid_glass_placement": {
  "entry_model": "str \"unchanged: Live Pulse and Narratives only\"",
  "observability_visibility": "str",
  "financial_truth_surfaces": "str"
 }
}
```

## `GET /health` — HTTP 200

```json
{
 "status": "str \"ok\"",
 "service": "str \"scip-backend\"",
 "version": "str",
 "environment": "str \"local\"",
 "auth_mode": "str \"local_dev\"",
 "timestamp": "str",
 "warmup": {
  "state": "str \"disabled\"",
  "stage_started_at": "null",
  "elapsed_seconds": "null"
 }
}
```

## `GET /cache/status` — HTTP 200

```json
{
 "status": "str \"ok\"",
 "data_loader": {
  "status": "str \"warm\"",
  "data_dir": "str \"/tmp/scip/r-series\"",
  "loaded_at_epoch": "float",
  "age_seconds": "float",
  "ttl_seconds": "int",
  "hits": "int",
  "misses": "int",
  "last_load_duration_seconds": "float",
  "last_load_timings": {
   "total_ms": "float",
   "resolve_r_series_ms": "float",
   "build_computed_ms": "float",
   "build_summary_ms": "float",
   "slowest_sources": [
    {
     "source": "str",
     "ms": "float"
    },
    "<5 item(s), shape of first shown>"
   ]
  },
  "lineage_preserved": "bool",
  "no_silent_fallback": "bool"
 },
 "action_queues": {
  "status": "str \"warm\"",
  "ttl_seconds": "int",
  "entries": [
   {
    "data_dir": "str \"/tmp/scip/r-series\"",
    "role": "str \"mis_qcg_admin\"",
    "age_seconds": "float",
    "status": "str \"ready_account_level_guarded\""
   },
   "<3 item(s), shape of first shown>"
  ],
  "hits": "int",
  "misses": "int",
  "lineage_preserved": "bool",
  "no_silent_fallback": "bool"
 },
 "guardrails": {
  "lineage_preserved": "bool",
  "no_frontend_business_computation": "bool",
  "no_silent_fallback": "bool"
 }
}
```
