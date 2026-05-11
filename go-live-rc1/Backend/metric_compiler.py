"""SCIP Batch 18 metric compiler.

Compiles governed metric values from lineaged facts. Missing inputs yield blocked
metric states, never silent fallback values.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional

from analytics_models import FactRecord, MetricValue
from analytics_utils import safe_div, to_float
from metric_registry import MetricRegistry


class MetricCompiler:
    def __init__(self, registry: MetricRegistry | None = None):
        self.registry = registry or MetricRegistry()

    def compile_metrics(self, facts: Iterable[FactRecord]) -> List[MetricValue]:
        facts_list = list(facts)
        metrics: List[MetricValue] = []
        # First compile registry-defined metrics where supported.
        for spec in self.registry.all():
            compiled = self._compile_registry_metric(spec, facts_list)
            if compiled:
                metrics.append(compiled)
        # Then compile operational metrics discovered from uploaded report set.
        metrics.extend(self._compile_runtime_operational_metrics(facts_list))
        return self._dedupe(metrics)

    def _compile_registry_metric(self, spec: Dict[str, Any], facts: List[FactRecord]) -> Optional[MetricValue]:
        mid = spec.get("metric_id")
        if not mid:
            return None
        selector = {
            "M_OD_TODAY_GROUP": lambda: self._latest_value(facts, "R18", "fact_overdue_snapshot", "OD_TODAY"),
            "M_AGEING_180PLUS_EXPOSURE": lambda: self._ratio_metric(facts, "R18", "ageing_180plus", "OD_TODAY", percent=True),
            "M_COLLECTION_MTD_FINANCE": lambda: self._first_value_by_names(facts, "R04", ["mtd_total_collections", "mtd_total_collections_aed", "MTD_TOTAL_COLLECTIONS"]),
            "M_MONTH_TARGET_MDO": lambda: self._first_value_by_names(facts, "R02", ["month_target_total", "may_total_collection_target", "MAY_TOTAL_COLLECTION_TARGET"]),
            "M_FORWARD_CALENDAR_TOTAL": lambda: self._first_value_by_names(facts, "R36", ["PIPELINE_GROSS", "pipeline_gross", "PIPELINE_TOTAL_FORWARD_CALENDAR"]),
            "M_ADVANCE_CY_FY_MIX": lambda: self._ratio_metric(facts, "R08", "CY_ADVANCE", "TOTAL_ADVANCE", percent=True),
            "M_HIGH_VALUE_NO_TOUCH_POOL": lambda: self._first_value_by_names(facts, "R10", ["high_value_no_touch_amount_aed"]),
            "M_TRACKER_TO_RECEIPT_CONVERSION": lambda: self._ratio_values(self._first_value_by_names(facts, "R10", ["receipt_generated_aed"]), self._first_value_by_names(facts, "R10", ["amount_in_tracker_aed"]), percent=True),
        }.get(mid)
        value = selector() if selector else None
        return self._metric_from_spec(spec, value, facts)

    def _compile_runtime_operational_metrics(self, facts: List[FactRecord]) -> List[MetricValue]:
        out: List[MetricValue] = []
        runtime_specs = [
            ("M_R10_PTP_COUNT", "PTP Count", self._first_value_by_names(facts, "R10", ["ptp_count"]), "count", "R10 PTP Data", ["CCO/GM/AGM", "Collector/RM"]),
            ("M_R10_PTP_AMOUNT_EST", "PTP Amount - Estimated", self._first_value_by_names(facts, "R10", ["ptp_amount_estimated_aed"]), "AED", "R10 PTP Data", ["CCO/GM/AGM"]),
            ("M_R30_TOTAL_PAYMENT", "Collector Total Payment", self._first_value_by_names(facts, "R30", ["total_payment_aed"]), "AED", "R30 Monthly Feedback", ["CCO/GM/AGM", "Collector/RM"]),
            ("M_R30_PAYMENT_PER_CONTACT", "Payment per Contact", self._ratio_values(self._first_value_by_names(facts, "R30", ["total_payment_aed"]), self._first_value_by_names(facts, "R30", ["contacts"]), percent=False), "AED/contact", "R30 Monthly Feedback", ["CCO/GM/AGM"]),
            ("M_R31_PR_TOTAL_AMOUNT", "PR Total Amount", self._first_value_by_names(facts, "R31", ["pr_total_amount_aed"]), "AED", "R31 PR Unit Update", ["Finance", "MIS/QCG/Admin"]),
            ("M_R31_DAILY_COLLECTION_DEPOSIT", "R31 Daily Collection Deposit", self._first_value_by_names(facts, "R31", ["daily_collection_deposit_aed"]), "AED", "R31 Daily Collection", ["Finance", "MIS/QCG/Admin"]),
            ("M_R34_ELIGIBLE_TERMINATION_EXPOSURE", "Eligible Termination Exposure", self._dimension_sum(facts, "R34", "fact_termination_eligibility", "eligible", "Eligible"), "AED", "R34 Termination Status", ["CCO/GM/AGM"]),
            ("M_R34_NOT_IN_SYSTEM_EXPOSURE", "Termination Not-in-System Exposure", self._dimension_sum(facts, "R34", "fact_termination_system_status", "system_status", "Not in System"), "AED", "R34 Termination Status", ["CCO/GM/AGM", "MIS/QCG/Admin"]),
            ("M_R17_LEGAL_BLOCKED_OD", "Legal / PR Blocked OD", self._sum_names(facts, "R17", ["spa_not_sent_aed", "spa_sent_not_signed_aed", "spa_signed_not_executed_aed", "spa_executed_not_preregistered_aed"]), "AED", "R17 SPA / preregistration", ["CCO/GM/AGM", "Finance"]),
            ("M_R09_PROJECT_FUTURE_COLLECTIBLES", "Project Future Collectibles", self._first_value_by_names(facts, "R09", ["future_collectibles_aed"]), "AED", "R09 Collections", ["Board/CXO", "CCO/GM/AGM"]),
            ("M_R16_CUSTOMER_FUTURE_COLLECTIBLES", "Customer Future Collectibles", self._first_value_by_names(facts, "R16", ["future_collectibles_aed"]), "AED", "R16 Customer Portfolio", ["CCO/GM/AGM"]),
        ]
        for mid, label, value, unit, basis, roles in runtime_specs:
            out.append(self._metric(mid, label, value, unit, basis, roles, facts))
        return out

    def _metric_from_spec(self, spec: Dict[str, Any], value: Any, facts: List[FactRecord]) -> MetricValue:
        return MetricValue(
            metric_id=spec.get("metric_id"),
            label=spec.get("label") or spec.get("metric_id"),
            value=value,
            unit=spec.get("unit", "AED"),
            formula=spec.get("formula", ""),
            source_basis=spec.get("reporting_basis", ""),
            validation_status="passed" if value is not None else "blocked",
            confidence_state="live_validated" if value is not None else "blocked_missing_fact",
            lineage_refs=self._lineage_for_sources(facts, spec.get("source_reports", [])),
            role_visibility=spec.get("role_visibility", []),
            grain=spec.get("grain"),
            source_reports=spec.get("source_reports", []),
            display_surfaces=spec.get("display_surfaces", []),
            caveats=[] if value is not None else ["Required lineaged facts not available; no fallback value published."],
        )

    def _metric(self, metric_id: str, label: str, value: Any, unit: str, basis: str, roles: List[str], facts: List[FactRecord]) -> MetricValue:
        source = basis.split()[0] if basis else ""
        return MetricValue(
            metric_id=metric_id, label=label, value=value, unit=unit, formula="compiled from Batch 18 facts",
            source_basis=basis, validation_status="passed" if value is not None else "blocked",
            confidence_state="live_validated" if value is not None else "blocked_missing_fact",
            lineage_refs=self._lineage_for_sources(facts, [source]), role_visibility=roles, source_reports=[source] if source else [],
            caveats=[] if value is not None else ["Input facts missing; no silent fallback."],
        )

    def _lineage_for_sources(self, facts: List[FactRecord], sources: List[str]) -> List[str]:
        src = {s.upper() for s in sources if s}
        refs = [f.lineage_hash for f in facts if f.source_code.upper() in src and f.lineage_hash]
        return refs[:50]

    @staticmethod
    def _latest_value(facts: List[FactRecord], source: str, fact_type: str, measure: str) -> Any:
        matches = [f for f in facts if f.source_code == source and f.fact_type == fact_type and f.measure_name == measure]
        return matches[-1].value if matches else None

    def _first_value_by_names(self, facts: List[FactRecord], source: str, names: List[str]) -> Any:
        wanted = {n.lower() for n in names}
        for f in facts:
            if f.source_code == source and f.measure_name.lower() in wanted:
                return f.value
        # relaxed normalized containment
        for f in facts:
            if f.source_code == source and any(n.lower() in f.measure_name.lower() for n in names):
                return f.value
        return None

    def _sum_names(self, facts: List[FactRecord], source: str, names: List[str]) -> Optional[float]:
        total = 0.0; found = False
        wanted = {n.lower() for n in names}
        for f in facts:
            if f.source_code == source and f.measure_name.lower() in wanted:
                val = to_float(f.value)
                if val is not None:
                    total += val; found = True
        return total if found else None

    def _ratio_metric(self, facts: List[FactRecord], source: str, numerator_name: str, denominator_name: str, percent: bool) -> Optional[float]:
        return self._ratio_values(self._first_value_by_names(facts, source, [numerator_name]), self._first_value_by_names(facts, source, [denominator_name]), percent=percent)

    @staticmethod
    def _ratio_values(numerator: Any, denominator: Any, percent: bool) -> Optional[float]:
        value = safe_div(numerator, denominator)
        if value is None:
            return None
        return value * 100 if percent else value

    def _dimension_sum(self, facts: List[FactRecord], source: str, fact_type: str, dim_key: str, dim_value: str) -> Optional[float]:
        total = 0.0; found = False
        for f in facts:
            if f.source_code == source and f.fact_type == fact_type and str(f.dimensions.get(dim_key, "")).lower() == dim_value.lower():
                val = to_float(f.value)
                if val is not None:
                    total += val; found = True
        return total if found else None

    @staticmethod
    def _dedupe(metrics: List[MetricValue]) -> List[MetricValue]:
        seen = set(); out = []
        for metric in metrics:
            if metric.metric_id in seen:
                continue
            seen.add(metric.metric_id)
            out.append(metric)
        return out
