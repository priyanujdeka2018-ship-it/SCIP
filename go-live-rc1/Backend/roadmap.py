"""
SCIP Batch 17 - Long-term roadmap and executive operating rhythm routes.
This module serves governance artifacts only. It does not compute financial metrics
and does not create a new Liquid Glass arrival surface.
"""
from __future__ import annotations
import json
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter(prefix="/roadmap", tags=["roadmap"])
_HERE = Path(__file__).resolve().parent

def _load_json(rel: str):
    with open(_HERE / rel, "r", encoding="utf-8") as f:
        return json.load(f)

def _read_text(rel: str) -> str:
    return (_HERE / rel).read_text(encoding="utf-8")

@router.get("/summary")
async def roadmap_summary():
    data = _load_json("roadmap/roadmap_12_month_batch17.json")
    return JSONResponse({
        "contract": "roadmap.v1.batch17",
        "status": "ready_executive_operating_rhythm_governed",
        "liquid_glass_surface": "l5_governance_output_not_arrival",
        "quarters": data["quarters"],
        "item_count": len(data["items"]),
        "locked_principles": data["locked_principles"],
    })

@router.get("/12-month")
async def roadmap_12_month():
    return JSONResponse(_load_json("roadmap/roadmap_12_month_batch17.json"))

@router.get("/okr-tree")
async def okr_tree():
    return JSONResponse(_load_json("okr/kpi_okr_tree_batch17.json"))

@router.get("/ownership-map")
async def ownership_map():
    return JSONResponse(_load_json("ownership/ownership_map_batch17.json"))

@router.get("/release-train")
async def release_train():
    return JSONResponse(_load_json("release_train/release_train_model_batch17.json"))

@router.get("/benefits")
async def benefits():
    return JSONResponse(_load_json("benefits/benefits_realization_tracking_batch17.json"))

@router.get("/steering-pack")
async def steering_pack():
    return JSONResponse(_load_json("steering/executive_steering_committee_pack_batch17.json"))

@router.get("/monthly-calendar")
async def monthly_calendar():
    return JSONResponse(_load_json("cadence/monthly_review_calendar_batch17.json"))

@router.get("/templates")
async def templates():
    return JSONResponse({
        "weekly_management_review": _read_text("executive/SCIP_Batch17_Executive_Operating_Rhythm_Templates.md"),
        "quarterly_operating_rhythm": _read_text("cadence/SCIP_Batch17_Quarterly_Executive_Operating_Rhythm.md"),
        "steering_committee_pack": _read_text("steering/SCIP_Batch17_Executive_Steering_Committee_Pack.md"),
    })

@router.get("/validation")
async def validation():
    return JSONResponse(_load_json("smoke_batch17_roadmap_exec_rhythm_results.json"))
