"""SCIP Batch 18 metric linker."""
from __future__ import annotations

from typing import List, Optional

from analytics_models import MetricLink, MetricValue
from analytics_utils import to_float


class MetricLinker:
    def link_metrics(self, metrics: List[MetricValue]) -> List[MetricLink]:
        by_id = {m.metric_id: m for m in metrics}
        links: List[MetricLink] = []
        self._add_if_present(links, by_id, "M_COLLECTION_MTD_FINANCE", "M_R31_DAILY_COLLECTION_DEPOSIT", "same_family", "R04 finance actual and R31 receipt/deposit bridge should reconcile by snapshot caveat")
        self._add_if_present(links, by_id, "M_HIGH_VALUE_NO_TOUCH_POOL", "M_R10_PTP_COUNT", "related_metric", "No-touch pool and PTP count are action funnel companions")
        self._add_if_present(links, by_id, "M_R30_TOTAL_PAYMENT", "M_TRACKER_TO_RECEIPT_CONVERSION", "related_metric", "Collector payment links to tracker-to-receipt conversion")
        self._add_if_present(links, by_id, "M_R34_ELIGIBLE_TERMINATION_EXPOSURE", "M_R17_LEGAL_BLOCKED_OD", "related_risk", "Termination exposure should be interpreted with SPA/pre-registration blockage")
        self._add_if_present(links, by_id, "M_FORWARD_CALENDAR_TOTAL", "M_R09_PROJECT_FUTURE_COLLECTIBLES", "diagnostic_reconciliation", "R36 forward calendar and R09 project future collectibles are related but may differ by basis")
        return links

    def _add_if_present(self, links: List[MetricLink], by_id: dict, left: str, right: str, classification: str, caveat: str) -> None:
        if left not in by_id or right not in by_id:
            return
        l = by_id[left]; r = by_id[right]
        lv = to_float(l.value); rv = to_float(r.value)
        confidence = 0.65
        evidence = {"left_value": l.value, "right_value": r.value, "left_basis": l.source_basis, "right_basis": r.source_basis}
        if lv is not None and rv is not None and max(abs(lv), abs(rv)) > 0:
            diff_pct = abs(lv - rv) / max(abs(lv), abs(rv))
            evidence["diff_pct"] = diff_pct
            if diff_pct <= 0.005:
                confidence = 0.95
            elif diff_pct <= 0.05:
                confidence = 0.8
        links.append(MetricLink(source_metric_id=left, target_metric_id=right, classification=classification, confidence=confidence, caveat=caveat, evidence=evidence))
