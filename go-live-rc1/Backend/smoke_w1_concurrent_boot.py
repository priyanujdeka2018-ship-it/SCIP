"""
SCIP W1 smoke — concurrent boot + warming state (SCIP_CONCURRENT_BOOT).

Three isolated scenarios, each in its own subprocess so flag/env/module state
never leaks between them:

  A. flag OFF (default): /health reports warmup state "disabled"; core
     endpoints serve full payloads exactly as before this wave.
  B. flag ON, simulated cold boot: the source dir is EMPTY at process start;
     the Drive download step is simulated by copying real workbooks from
     SCIP_W1_REAL_SOURCES after the smoke has asserted the warming envelopes
     (deterministic via a release event — no sleeps in the warming window).
     After the background load completes, the five core endpoints must
     deep-equal scenario A (volatile timestamp keys normalized).
  C. flag ON, negative: real bootstrap failure (bad Drive folder id) must
     surface warmup_failed on /health and the endpoints, with no values.

Run from Backend/ with real sources staged:
    SCIP_W1_REAL_SOURCES=/tmp/scip/r-series python smoke_w1_concurrent_boot.py

Uses the staging local-dev bypass (header identity) — UAT posture only.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

REAL_SOURCES = os.environ.get("SCIP_W1_REAL_SOURCES", "/tmp/scip/r-series")
SMOKE_HEADERS = {
    "x-scip-role": "mis_qcg_admin",
    "x-scip-actor-id": "smoke_w1",
    "x-scip-actor-name": "Smoke W1",
}
CORE_GETS = [
    ("command_centres", "/command-centres"),
    ("forecast", "/forecast/month-end"),
    ("action_queues", "/action-queues"),
    ("workflows", "/workflows"),
    ("quickball_explain", "/quickball/explain?metric=OD_TODAY&role=board_cxo"),
]
ENVELOPE_KEYS_WARMING = {"scip_state", "stage", "started_at", "confidence_state", "detail", "retry_after_seconds"}
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


def _client():
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)


def _get(client, path):
    response = client.get(path, headers=SMOKE_HEADERS)
    assert response.status_code == 200, f"{path}: HTTP {response.status_code}: {response.text[:200]}"
    return response.json()


def scenario_a(out_path: str) -> None:
    """Flag OFF — current behavior, warmup disabled on /health."""
    with _client() as client:
        health = _get(client, "/health")
        assert health.get("warmup", {}).get("state") == "disabled", f"warmup block: {health.get('warmup')}"
        bodies = {}
        for name, path in CORE_GETS:
            body = _get(client, path)
            assert "scip_state" not in body, f"{name}: unexpected warming envelope with flag off"
            bodies[name] = body
        json.dump({"health": health, "bodies": canonicalize(bodies)}, open(out_path, "w"), default=str)
    print("[scenario A] flag-off OK: warmup disabled, full payloads served")


def scenario_b(out_path: str) -> None:
    """Flag ON — cold boot with empty source dir, then simulated download of real sources."""
    import main
    import bootstrap_rseries_google_drive_folder as bootstrap_mod

    source_root = os.environ["SCIP_SOURCE_ROOT"]
    release = threading.Event()

    def simulated_download() -> None:
        release.wait(timeout=120)
        for fname in os.listdir(REAL_SOURCES):
            shutil.copy2(os.path.join(REAL_SOURCES, fname), os.path.join(source_root, fname))

    bootstrap_mod.run_bootstrap = simulated_download

    from fastapi.testclient import TestClient
    with TestClient(main.app) as client:
        envelopes = {}
        for name, path in CORE_GETS:
            body = _get(client, path)
            assert body.get("scip_state") == "warming", f"{name}: expected warming envelope, got {str(body)[:200]}"
            assert body.get("confidence_state") == "unavailable", f"{name}: confidence_state missing"
            assert body.get("stage") in ("downloading_sources", "parsing_sources"), f"{name}: stage={body.get('stage')}"
            assert body.get("retry_after_seconds") == 4
            assert set(body.keys()) == ENVELOPE_KEYS_WARMING, f"{name}: envelope keys {sorted(body.keys())}"
            envelopes[name] = body
        health = _get(client, "/health")
        assert health["warmup"]["state"] in ("cold", "downloading_sources"), health["warmup"]
        print(f"[scenario B] warming envelopes verified on {len(envelopes)} core endpoints while cold")

        release.set()
        deadline = time.time() + 180
        while time.time() < deadline:
            state = _get(client, "/health")["warmup"]["state"]
            if state == "warm":
                break
            assert state != "warmup_failed", f"unexpected warmup_failed: {_get(client, '/health')['warmup']}"
            time.sleep(0.5)
        else:
            raise AssertionError("background load did not reach warm in time")
        print("[scenario B] warm reached after simulated download")

        bodies = {}
        for name, path in CORE_GETS:
            body = _get(client, path)
            assert "scip_state" not in body, f"{name}: still warming after warm state"
            bodies[name] = body
        json.dump({"bodies": canonicalize(bodies)}, open(out_path, "w"), default=str)
    print("[scenario B] post-warm payloads captured")


def scenario_c(out_path: str) -> None:
    """Flag ON — real bootstrap failure must surface warmup_failed, no values."""
    with _client() as client:
        deadline = time.time() + 120
        while time.time() < deadline:
            warmup = _get(client, "/health")["warmup"]
            if warmup["state"] == "warmup_failed":
                break
            assert warmup["state"] != "warm", "bad folder id must not reach warm"
            time.sleep(0.5)
        else:
            raise AssertionError("warmup_failed not reached in time")
        assert warmup.get("reason"), f"warmup_failed must carry the failure reason: {warmup}"
        for name, path in CORE_GETS:
            body = _get(client, path)
            assert body.get("scip_state") == "warmup_failed", f"{name}: expected warmup_failed envelope"
            assert body.get("confidence_state") == "unavailable"
            assert body.get("reason"), f"{name}: failed envelope must carry reason"
        json.dump({"warmup": warmup}, open(out_path, "w"), default=str)
    print(f"[scenario C] warmup_failed surfaced with reason on /health and {len(CORE_GETS)} endpoints; no values served")


def run_scenarios() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    work = tempfile.mkdtemp(prefix="scip-w1-")
    outs = {s: os.path.join(work, f"scenario_{s}.json") for s in "abc"}

    common = {
        **os.environ,
        "SCIP_AUTH_MODE": "local_dev",
        "SCIP_LOCAL_DEV_BYPASS": "true",
        "SCIP_ENV": "local",
    }
    scenarios = {
        "a": {
            "SCIP_SOURCE_ROOT": REAL_SOURCES,
            "SCIP_CONCURRENT_BOOT": "false",
        },
        "b": {
            "SCIP_SOURCE_ROOT": os.path.join(work, "cold", "r-series"),
            "SCIP_CONCURRENT_BOOT": "true",
            "SCIP_RSERIES_BOOTSTRAP": "false",
        },
        "c": {
            "SCIP_SOURCE_ROOT": os.path.join(work, "negative", "r-series"),
            "SCIP_CONCURRENT_BOOT": "true",
            "SCIP_RSERIES_BOOTSTRAP": "true",
            "SCIP_GOOGLE_DRIVE_FOLDER_ID": "this-folder-does-not-exist-w1-negative",
        },
    }
    for name, env in scenarios.items():
        os.makedirs(env["SCIP_SOURCE_ROOT"], exist_ok=True)
        print(f"--- scenario {name.upper()} ---")
        proc = subprocess.run(
            [sys.executable, os.path.abspath(__file__)],
            env={**common, **env, "SCIP_W1_SCENARIO": name, "SCIP_W1_OUT": outs[name]},
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
    failures = []
    for name, _ in CORE_GETS:
        if a[name] == b[name]:
            print(f"[PASS] {name}: flag-on post-warm payload deep-equals flag-off payload")
        else:
            print(f"[FAIL] {name}: flag-on post-warm payload differs from flag-off")
            failures.append(name)

    print()
    if failures:
        print(f"W1 SMOKE FAILED: {failures}")
        return 1
    print("W1 SMOKE PASSED")
    return 0


if __name__ == "__main__":
    scenario = os.environ.get("SCIP_W1_SCENARIO")
    if scenario == "a":
        scenario_a(os.environ["SCIP_W1_OUT"])
    elif scenario == "b":
        scenario_b(os.environ["SCIP_W1_OUT"])
    elif scenario == "c":
        scenario_c(os.environ["SCIP_W1_OUT"])
    else:
        sys.exit(run_scenarios())
