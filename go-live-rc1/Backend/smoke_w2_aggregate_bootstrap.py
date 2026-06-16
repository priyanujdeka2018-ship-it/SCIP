"""
SCIP W2 smoke — GZip compression + aggregate /bootstrap route.

Both behaviours ship behind default-OFF env flags (SCIP_ENABLE_GZIP,
SCIP_ENABLE_BOOTSTRAP_ROUTE). Three isolated scenarios, each in its own
subprocess so flag/env/module state never leaks between them:

  A. both flags OFF (default): GET /bootstrap is 404 (route absent); the four
     core endpoints serve full payloads exactly as before this wave; no
     Content-Encoding is added even when the client offers gzip.
  B. /bootstrap ON, gzip OFF: GET /bootstrap returns the four core payloads in
     one response. For every role, each sub-payload deep-equals the standalone
     endpoint's body (volatile timestamp keys normalized), and a sub-payload
     the standalone endpoint would deny with 403 appears as an explicit
     "denied" marker — aggregation never bypasses the URL-level RBAC the auth
     middleware enforces, and never fabricates a value.
  C. gzip ON, /bootstrap ON: a large response carries Content-Encoding: gzip
     and, once decompressed, deep-equals the uncompressed scenario-A body —
     compression is transport-only and transparent.

Additivity: the canonicalized core payloads captured with flags off (A) must
equal those captured with the flags on (B, C). W2 adds only gated code paths.

Run from Backend/ with real sources staged:
    SCIP_SOURCE_ROOT=/tmp/scip/r-series python smoke_w2_aggregate_bootstrap.py

Uses the staging local-dev bypass (header identity) — UAT posture only.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

# Bootstrap sub-payload key -> standalone endpoint path.
SUBS = [
    ("command_centres", "/command-centres"),
    ("forecast_month_end", "/forecast/month-end"),
    ("action_queues", "/action-queues"),
    ("workflows", "/workflows"),
]
# A full-access role (all four allowed) and a limited role (forecast denied).
ROLES = ["cco_gm_agm", "collector_rm"]

VOLATILE_KEYS = {
    "LOAD_TIMESTAMP", "load_timestamp", "forecast_date", "created_at", "updated_at",
    "last_loaded_at", "loaded_at_epoch", "age_seconds", "timestamp", "generated_at",
    "event_id", "last_load_duration_seconds", "last_load_timings",
}
SET_STRING_KEYS = {"allowed_action_visibility"}


def canonicalize(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in VOLATILE_KEYS:
                out[k] = "<VOLATILE>"
            elif k in SET_STRING_KEYS and isinstance(v, str) and v.startswith("{"):
                out[k] = "{" + ", ".join(sorted(p.strip() for p in v[1:-1].split(","))) + "}"
            else:
                out[k] = canonicalize(v)
        return out
    if isinstance(obj, list):
        return [canonicalize(v) for v in obj]
    return obj


def _headers(role: str) -> dict:
    return {
        "x-scip-role": role,
        "x-scip-actor-id": f"smoke_w2_{role}",
        "x-scip-actor-name": "Smoke W2",
        "x-scip-collector-id": "smoke_w2_collector" if role == "collector_rm" else "",
    }


def _client():
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)


# --------------------------------------------------------------------------- #
# Scenario A — both flags OFF (default behaviour).
# --------------------------------------------------------------------------- #
def scenario_a(out_path: str) -> None:
    with _client() as client:
        boot = client.get("/bootstrap", headers=_headers("cco_gm_agm"))
        assert boot.status_code == 404, f"/bootstrap must be absent with flag off, got {boot.status_code}"

        bodies = {}
        for name, path in SUBS:
            r = client.get(path, headers=_headers("cco_gm_agm"))
            assert r.status_code == 200, f"{path}: HTTP {r.status_code}: {r.text[:200]}"
            bodies[name] = canonicalize(r.json())

        # Offering gzip changes nothing while the flag is off.
        r = client.get("/command-centres", headers={**_headers("cco_gm_agm"), "accept-encoding": "gzip"})
        assert r.headers.get("content-encoding") != "gzip", "gzip must not be applied with SCIP_ENABLE_GZIP off"

        json.dump({"bodies": bodies}, open(out_path, "w"), default=str)
    print("[scenario A] flags-off OK: /bootstrap 404, core payloads served, no gzip")


# --------------------------------------------------------------------------- #
# Scenario B — /bootstrap ON, gzip OFF: parity + RBAC parity.
# --------------------------------------------------------------------------- #
def scenario_b(out_path: str) -> None:
    with _client() as client:
        captured = {}
        for role in ROLES:
            boot = client.get("/bootstrap", headers=_headers(role))
            assert boot.status_code == 200, f"/bootstrap[{role}]: HTTP {boot.status_code}: {boot.text[:200]}"
            body = boot.json()
            assert body.get("bootstrap_contract") == "scip.bootstrap.v1", f"contract: {body.get('bootstrap_contract')}"
            endpoints = body.get("endpoints", {})
            unavailable = body.get("unavailable", {})

            for name, path in SUBS:
                standalone = client.get(path, headers=_headers(role))
                if standalone.status_code == 200:
                    assert name in endpoints, f"{role}/{name}: allowed standalone but absent from /bootstrap"
                    a = canonicalize(endpoints[name])
                    b = canonicalize(standalone.json())
                    assert a == b, f"{role}/{name}: /bootstrap sub-payload differs from standalone endpoint"
                elif standalone.status_code == 403:
                    assert name in unavailable and unavailable[name].get("status") == "denied", \
                        f"{role}/{name}: standalone 403 but /bootstrap did not disclose a denial: {unavailable.get(name)}"
                    assert name not in endpoints, f"{role}/{name}: denied path must not appear in endpoints"
                else:
                    raise AssertionError(f"{role}/{path}: unexpected standalone status {standalone.status_code}")
            print(f"[scenario B] role={role}: /bootstrap parity + RBAC parity verified across {len(SUBS)} endpoints")

            if role == "cco_gm_agm":
                captured = {name: canonicalize(client.get(path, headers=_headers(role)).json()) for name, path in SUBS}

        json.dump({"bodies": captured}, open(out_path, "w"), default=str)
    print("[scenario B] aggregate parity captured")


# --------------------------------------------------------------------------- #
# Scenario C — gzip ON, /bootstrap ON: transparency.
# --------------------------------------------------------------------------- #
def scenario_c(out_path: str) -> None:
    with _client() as client:
        r = client.get("/command-centres", headers={**_headers("cco_gm_agm"), "accept-encoding": "gzip"})
        assert r.status_code == 200, f"/command-centres: HTTP {r.status_code}"
        assert r.headers.get("content-encoding") == "gzip", \
            f"large response must be gzip-encoded, content-encoding={r.headers.get('content-encoding')}"
        decoded = r.json()  # httpx transparently decompresses

        boot = client.get("/bootstrap", headers={**_headers("cco_gm_agm"), "accept-encoding": "gzip"})
        assert boot.status_code == 200, f"/bootstrap: HTTP {boot.status_code}"
        assert boot.headers.get("content-encoding") == "gzip", "aggregate response must be gzip-encoded"
        boot_cc = boot.json().get("endpoints", {}).get("command_centres")
        assert boot_cc is not None, "command_centres missing from compressed /bootstrap"

        bodies = {"command_centres": canonicalize(decoded), "bootstrap_command_centres": canonicalize(boot_cc)}
        json.dump({"bodies": bodies}, open(out_path, "w"), default=str)
    print("[scenario C] gzip transparency verified: compressed body decompresses to the same payload")


# --------------------------------------------------------------------------- #
# Orchestration.
# --------------------------------------------------------------------------- #
def run_scenarios() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    work = tempfile.mkdtemp(prefix="scip-w2-")
    outs = {s: os.path.join(work, f"scenario_{s}.json") for s in "abc"}

    common = {
        **os.environ,
        "SCIP_AUTH_MODE": "local_dev",
        "SCIP_LOCAL_DEV_BYPASS": "true",
        "SCIP_ENV": "local",
        "SCIP_SOURCE_ROOT": os.environ.get("SCIP_SOURCE_ROOT", "/tmp/scip/r-series"),
    }
    scenarios = {
        "a": {"SCIP_ENABLE_BOOTSTRAP_ROUTE": "false", "SCIP_ENABLE_GZIP": "false"},
        "b": {"SCIP_ENABLE_BOOTSTRAP_ROUTE": "true", "SCIP_ENABLE_GZIP": "false"},
        "c": {"SCIP_ENABLE_BOOTSTRAP_ROUTE": "true", "SCIP_ENABLE_GZIP": "true"},
    }
    for name, env in scenarios.items():
        print(f"--- scenario {name.upper()} ---")
        proc = subprocess.run(
            [sys.executable, os.path.abspath(__file__)],
            env={**common, **env, "SCIP_W2_SCENARIO": name, "SCIP_W2_OUT": outs[name]},
            cwd=here,
            capture_output=True,
            text=True,
            timeout=600,
        )
        sys.stdout.write("\n".join(line for line in proc.stdout.splitlines() if line.startswith("[scenario")) + "\n")
        if proc.returncode != 0:
            print(f"scenario {name.upper()} FAILED:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
            return 1

    a = json.load(open(outs["a"]))["bodies"]
    b = json.load(open(outs["b"]))["bodies"]
    c = json.load(open(outs["c"]))["bodies"]

    failures = []
    for name, _ in SUBS:
        if a[name] == b[name]:
            print(f"[PASS] {name}: flags-on standalone payload deep-equals flags-off payload")
        else:
            print(f"[FAIL] {name}: flags-on standalone payload differs from flags-off")
            failures.append(name)

    if a["command_centres"] == c["command_centres"] == c["bootstrap_command_centres"]:
        print("[PASS] command_centres: gzip-decompressed payload deep-equals uncompressed baseline")
    else:
        print("[FAIL] command_centres: gzip-decompressed payload differs from baseline")
        failures.append("gzip-transparency")

    print()
    if failures:
        print(f"W2 SMOKE FAILED: {failures}")
        return 1
    print("W2 SMOKE PASSED")
    return 0


if __name__ == "__main__":
    scenario = os.environ.get("SCIP_W2_SCENARIO")
    if scenario == "a":
        scenario_a(os.environ["SCIP_W2_OUT"])
    elif scenario == "b":
        scenario_b(os.environ["SCIP_W2_OUT"])
    elif scenario == "c":
        scenario_c(os.environ["SCIP_W2_OUT"])
    else:
        sys.exit(run_scenarios())
