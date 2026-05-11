#!/usr/bin/env python3
from __future__ import annotations
import json, re, py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []

def add(name, passed, detail=None):
    checks.append({"name": name, "passed": bool(passed), "detail": detail or {}})

required_files = [
    "SCIP_Batch14_Implementation_Report.md",
    "rollout/SCIP_Batch14_Staged_Rollout_Plan.md",
    "uat/SCIP_Batch14_UAT_Scripts_By_Role.md",
    "checklists/SCIP_Batch14_Production_Readiness_Checklist.md",
    "checklists/SCIP_Batch14_Data_Cutover_Checklist.md",
    "checklists/SCIP_Batch14_Source_Refresh_Checklist.md",
    "checklists/SCIP_Batch14_Identity_Provisioning_Checklist.md",
    "checklists/SCIP_Batch14_RBAC_Verification_Checklist.md",
    "checklists/SCIP_Batch14_Dashboard_Alert_Signoff.md",
    "signoff/SCIP_Batch14_Executive_Acceptance_Criteria.md",
    "signoff/SCIP_Batch14_Signoff_Matrix.json",
    "smoke/final_deployment_smoke_manifest_batch14.json",
    "rollout_uat.py",
    "main.py",
]
for rel in required_files:
    add(f"required file exists: {rel}", (ROOT / rel).exists())

app = (ROOT / "App.jsx").read_text(encoding="utf-8")
add("Liquid Glass two-door labels present", "Live Pulse" in app and "Narratives" in app)
add("no entity_head technical role in frontend", "entity_head" not in app.lower())
add("no silent fallback warning present", "No fallback" in app or "no fallback" in app.lower())
add("frontend uses bearer Authorization", "Authorization" in app and "Bearer" in app)

main = (ROOT / "main.py").read_text(encoding="utf-8")
add("main includes rollout router", "rollout_uat" in main and "rollout_router" in main)
add("main version bumped to batch14", "Batch 14" in main or "batch14" in main)

manifest = json.loads((ROOT / "smoke/final_deployment_smoke_manifest_batch14.json").read_text(encoding="utf-8"))
required_checks = {"LG-001","NSF-001","ID-001","RBAC-001","RBAC-002","AUD-001","WF-001","NOTIF-001","OBS-001","DATA-001","ROLE-001"}
found = {c["id"] for c in manifest["checks"]}
add("final smoke manifest covers mandatory gates", required_checks.issubset(found), {"missing": sorted(required_checks - found)})

matrix = json.loads((ROOT / "signoff/SCIP_Batch14_Signoff_Matrix.json").read_text(encoding="utf-8"))
roles = set(matrix["roles"])
required_roles = {"Board/CXO", "CCO/GM/AGM", "Finance", "MIS/QCG/Admin", "Collector/RM"}
add("signoff matrix has approved roles only", roles == required_roles, {"roles": sorted(roles)})
add("signoff matrix excludes Entity Head", "Entity Head" not in roles)

for py in ["rollout_uat.py", "main.py"]:
    try:
        py_compile.compile(str(ROOT / py), doraise=True)
        add(f"python compile: {py}", True)
    except Exception as e:
        add(f"python compile: {py}", False, {"error": str(e)})

result = {
    "contract": "rollout_uat_signoff.v1.batch14",
    "status": "passed" if all(c["passed"] for c in checks) else "failed",
    "passed": all(c["passed"] for c in checks),
    "checks_passed": sum(1 for c in checks if c["passed"]),
    "checks_total": len(checks),
    "checks": checks,
}
(ROOT / "smoke_batch14_rollout_uat_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["passed"] else 1)
