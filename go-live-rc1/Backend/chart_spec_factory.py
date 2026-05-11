"""SCIP Batch 18 chart spec factory."""
from __future__ import annotations

from typing import Iterable, List

from analytics_models import ChartSpec, MetricValue


class ChartSpecFactory:
    def create_chart_specs(self, metrics: Iterable[MetricValue], role: str = "Board/CXO", surface: str | None = None) -> List[ChartSpec]:
        metrics_list = [m for m in metrics if role in m.role_visibility or not m.role_visibility]
        by_id = {m.metric_id: m for m in metrics_list}
        charts: List[ChartSpec] = []
        def metric_series(ids):
            return [{"metric_id": mid, "label": by_id[mid].label, "value": by_id[mid].value, "unit": by_id[mid].unit} for mid in ids if mid in by_id]
        def lineage(ids):
            refs=[]
            for mid in ids:
                if mid in by_id:
                    refs.extend(by_id[mid].lineage_refs[:10])
            return refs[:40]
        if "M_OD_TODAY_GROUP" in by_id or "M_AGEING_180PLUS_EXPOSURE" in by_id:
            ids=[x for x in ["M_OD_TODAY_GROUP","M_AGEING_180PLUS_EXPOSURE"] if x in by_id]
            charts.append(ChartSpec(chart_id="batch18_od_risk_signal", title="OD Risk Signal", surface="Live Pulse / Current Signal", chart_type="kpi_group", metric_ids=ids, series=metric_series(ids), source_basis="R18", confidence_state="live_validated", validation_status="passed", lineage_refs=lineage(ids), role_visibility=[role], quickball_prompts=["Explain this number", "Show source basis", "Why did OD risk matter?"]))
        if "M_COLLECTION_MTD_FINANCE" in by_id or "M_MONTH_TARGET_MDO" in by_id:
            ids=[x for x in ["M_COLLECTION_MTD_FINANCE","M_MONTH_TARGET_MDO","M_REQUIRED_RUN_RATE"] if x in by_id]
            charts.append(ChartSpec(chart_id="batch18_collection_track", title="Collection Track vs Target", surface="Live Pulse / Month Movement", chart_type="progress_bridge", metric_ids=ids, series=metric_series(ids), source_basis="R04 Finance + R02 MDO", confidence_state="live_validated", validation_status="passed", lineage_refs=lineage(ids), role_visibility=[role], quickball_prompts=["Explain target basis", "Show Finance vs MDO basis", "Prepare board explanation"]))
        if "M_FORWARD_CALENDAR_TOTAL" in by_id or "M_R09_PROJECT_FUTURE_COLLECTIBLES" in by_id:
            ids=[x for x in ["M_FORWARD_CALENDAR_TOTAL","M_R09_PROJECT_FUTURE_COLLECTIBLES"] if x in by_id]
            charts.append(ChartSpec(chart_id="batch18_forward_collectible_pressure", title="Forward Collectible Pressure", surface="Narratives / Portfolio", chart_type="kpi_group", metric_ids=ids, series=metric_series(ids), source_basis="R36 + R09", confidence_state="live_validated", validation_status="passed", lineage_refs=lineage(ids), role_visibility=[role], quickball_prompts=["Explain future collectible basis", "Show caveats"]))
        if any(x in by_id for x in ["M_HIGH_VALUE_NO_TOUCH_POOL","M_R10_PTP_COUNT","M_R30_TOTAL_PAYMENT"]):
            ids=[x for x in ["M_HIGH_VALUE_NO_TOUCH_POOL","M_R10_PTP_COUNT","M_R30_TOTAL_PAYMENT","M_R30_PAYMENT_PER_CONTACT"] if x in by_id]
            charts.append(ChartSpec(chart_id="batch18_action_intelligence", title="Action Intelligence", surface="Live Pulse / Risk & Action", chart_type="action_kpi_group", metric_ids=ids, series=metric_series(ids), source_basis="R10 + R30", confidence_state="live_validated", validation_status="passed", lineage_refs=lineage(ids), role_visibility=[role], quickball_prompts=["Open action list", "Explain no-touch pool", "Show collector basis"]))
        return charts if surface is None else [c for c in charts if c.surface == surface]
