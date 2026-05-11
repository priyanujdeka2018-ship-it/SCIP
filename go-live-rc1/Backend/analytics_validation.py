"""SCIP Batch 18 date-aware validation rules."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List

from analytics_models import FactRecord, MetricValue, ValidationResult
from analytics_utils import to_float


class AnalyticsValidationEngine:
    def validate(self, facts: Iterable[FactRecord], metrics: Iterable[MetricValue]) -> List[ValidationResult]:
        fact_list = list(facts); metric_list = list(metrics)
        out: List[ValidationResult] = []
        out.append(self._lineage_coverage(fact_list))
        out.extend(self._blocked_critical_metrics(metric_list))
        out.extend(self._date_alignment_checks(fact_list))
        return out

    def _lineage_coverage(self, facts: List[FactRecord]) -> ValidationResult:
        if not facts:
            return ValidationResult("B18_LINEAGE_COVERAGE", False, "critical", "No facts produced", {})
        covered = sum(1 for f in facts if f.lineage_hash)
        return ValidationResult("B18_LINEAGE_COVERAGE", covered == len(facts), "critical" if covered != len(facts) else "info", f"{covered}/{len(facts)} facts have lineage hashes", {"covered": covered, "total": len(facts)})

    def _blocked_critical_metrics(self, metrics: List[MetricValue]) -> List[ValidationResult]:
        out=[]
        for m in metrics:
            if m.confidence_state.startswith("blocked"):
                out.append(ValidationResult("B18_BLOCKED_METRIC_" + m.metric_id, False, "warning", f"Metric {m.metric_id} blocked because source facts are missing", {"metric_id": m.metric_id, "label": m.label}))
        return out

    def _date_alignment_checks(self, facts: List[FactRecord]) -> List[ValidationResult]:
        by_source = defaultdict(set)
        for f in facts:
            if f.snapshot_date:
                by_source[f.source_code].add(f.snapshot_date)
        out=[]
        # Do not fail cross-report validation if dates differ; emit caveat.
        important = [s for s in ["R18","R10","R30","R31","R04","R02"] if by_source.get(s)]
        dates = {s: sorted(by_source[s]) for s in important}
        if len({tuple(v) for v in dates.values()}) > 1:
            out.append(ValidationResult("B18_CROSS_REPORT_DATE_ALIGNMENT", False, "info", "Cross-report snapshot dates differ; reconciliation should be diagnostic, not hard tolerance", {"dates": dates}))
        elif dates:
            out.append(ValidationResult("B18_CROSS_REPORT_DATE_ALIGNMENT", True, "info", "Cross-report snapshot dates are aligned for available sources", {"dates": dates}))
        return out
