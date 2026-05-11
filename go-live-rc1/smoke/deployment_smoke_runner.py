#!/usr/bin/env python3
"""SCIP Batch 14 deployment smoke runner.
Run after each deployment stage:
  SCIP_BASE_URL=https://your-scip-url SCIP_JWT=<token> python smoke/deployment_smoke_runner.py
"""
from __future__ import annotations
import json, os, sys, time, urllib.request, urllib.error

BASE_URL = os.environ.get("SCIP_BASE_URL", "").rstrip("/")
TOKEN = os.environ.get("SCIP_JWT", "")

def call(path: str, token: str | None = None):
    req = urllib.request.Request(BASE_URL + path)
    req.add_header("x-scip-correlation-id", f"smoke-{int(time.time())}")
    if token:
        req.add_header("authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            data = json.loads(body)
        except Exception:
            data = {"raw": body}
        return e.code, data, dict(e.headers)

if not BASE_URL:
    print(json.dumps({"passed": False, "reason": "SCIP_BASE_URL is required"}, indent=2))
    sys.exit(2)

checks = []

def add(name, passed, detail=None):
    checks.append({"name": name, "passed": bool(passed), "detail": detail or {}})

status, data, headers = call("/")
add("root available", status == 200, {"status": status})

status, data, headers = call("/identity/me")
add("missing token rejected", status in (401, 403), {"status": status})

if TOKEN:
    for path in ["/identity/me", "/security/policy-matrix", "/deployment/health", "/observability/summary", "/rollout/final-smoke-manifest"]:
        status, data, headers = call(path, TOKEN)
        add(f"authenticated {path}", status == 200, {"status": status})

status, data, headers = call("/rollout/final-smoke-manifest", TOKEN if TOKEN else None)
if status == 200:
    required = {"liquid_glass_two_door_navigation", "no_silent_fallback", "identity_enforcement", "row_level_visibility", "audit_export", "workflow_closure", "notification_dedupe", "observability_correlation"}
    found = set(data.get("checks", []))
    add("final smoke manifest contains required checks", required.issubset(found), {"missing": sorted(required - found)})
else:
    add("final smoke manifest reachable", False, {"status": status})

result = {"passed": all(c["passed"] for c in checks), "checks": checks}
print(json.dumps(result, indent=2))
sys.exit(0 if result["passed"] else 1)
