"""SCIP Batch 18 candidate metric suggestion engine."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List, Set

from analytics_models import FactRecord, MetricCandidate


class MetricSuggestionEngine:
    def suggest_metrics(self, facts: Iterable[FactRecord]) -> List[MetricCandidate]:
        fact_list = list(facts)
        sources: Set[str] = {f.source_code for f in fact_list}
        candidates: List[MetricCandidate] = []
        def add(cid, name, formula, reports, question, roles, score, surface, action="high", dup="low"):
            if all(r in sources for r in reports):
                lineage = self._lineage_score(fact_list, reports)
                candidates.append(MetricCandidate(candidate_id=cid, suggested_name=name, formula=formula, source_reports=reports,
                    business_question=question, role_value=roles, lineage_completeness=lineage, actionability=action,
                    duplicate_risk=dup, recommended_surface=surface, priority_score=round(score * lineage, 3),
                    evidence={"fact_count": sum(1 for f in fact_list if f.source_code in reports)}))
        add("C_OD_180PLUS_PRESSURE", "180+ OD concentration", "R18 ageing_180plus / R18 OD_TODAY", ["R18"], "How much OD is structurally aged?", {"Board/CXO":"high","CCO/GM/AGM":"high"}, 0.95, "Live Pulse / Risk & Action")
        add("C_FUTURE_COLLECTIBLE_PRESSURE", "Future collectible pressure", "R36 forward calendar / R18 OD today", ["R36","R18"], "Is future collectible load building while current OD remains high?", {"Board/CXO":"high","CCO/GM/AGM":"high"}, 0.9, "Narratives / Portfolio")
        add("C_HIGH_VALUE_NO_TOUCH_POOL", "High-value no-touch pool", "R10 overdue EOM >= threshold and communication_count = 0", ["R10"], "Which high-value accounts are not being worked?", {"CCO/GM/AGM":"high","Collector/RM":"high"}, 0.95, "Live Pulse / Risk & Action")
        add("C_COLLECTOR_COACHING_PRIORITY", "Collector coaching priority score", "low contact intensity + high allocated OD + low payment per contact", ["R30"], "Which collectors need intervention?", {"CCO/GM/AGM":"high"}, 0.85, "Live Pulse / Risk & Action")
        add("C_PR_RECEIPT_CONFIDENCE_BRIDGE", "PR to receipt confidence bridge", "R31 approved PR amount vs cleared receipt amount vs R04 finance collection", ["R31"], "How much reported collection is cleanly converted to receipt?", {"Finance":"high","MIS/QCG/Admin":"high"}, 0.85, "Narratives / Story")
        add("C_LEGAL_BLOCKED_OD", "Legal-process blocked OD", "SPA not sent + SPA sent not signed + SPA executed not pre-registered", ["R17"], "How much OD is blocked by legal/documentation process?", {"CCO/GM/AGM":"high","Finance":"medium"}, 0.9, "Narratives / Dues")
        add("C_TERMINATION_NOT_IN_SYSTEM", "Eligible but not-in-system termination exposure", "R34 eligible exposure filtered by system status", ["R34"], "How much termination exposure is not yet operationally in system?", {"CCO/GM/AGM":"high","MIS/QCG/Admin":"high"}, 0.9, "Live Pulse / Risk & Action")
        add("C_CUSTOMER_CONCENTRATION_RISK", "Customer concentration risk", "top customer/nationality/CIV exposure from R16", ["R16"], "Where is portfolio exposure concentrated?", {"CCO/GM/AGM":"medium","Finance":"medium"}, 0.75, "Narratives / Portfolio")
        return candidates

    @staticmethod
    def _lineage_score(facts: List[FactRecord], reports: List[str]) -> float:
        relevant = [f for f in facts if f.source_code in reports]
        if not relevant:
            return 0.0
        with_hash = [f for f in relevant if f.lineage_hash and f.confidence_state != "blocked"]
        return round(len(with_hash) / len(relevant), 4)
