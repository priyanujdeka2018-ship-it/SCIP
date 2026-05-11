"""
SCIP Batch 18 Analytics Transformation Engine - shared runtime models.

Additive overlay. Does not replace Batch 13 runtime files.
Runtime dependencies: Python stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ReportProfile:
    report_code: str
    source_file: str
    profiled_at: str
    sheets: List[Dict[str, Any]]
    snapshot_date: Optional[str] = None
    detected_grains: List[str] = field(default_factory=list)
    header_strategy: str = "unknown"
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FactRecord:
    fact_id: str
    fact_type: str
    source_code: str
    source_file: str
    sheet: str
    grain: str
    measure_name: str
    value: Any
    unit: str
    reporting_basis: str
    validation_status: str
    confidence_state: str
    lineage_hash: str
    loaded_at: str
    cell_or_range: Optional[str] = None
    extraction_rule: Optional[str] = None
    snapshot_date: Optional[str] = None
    entity_key: Optional[str] = None
    project_key: Optional[str] = None
    customer_key: Optional[str] = None
    unit_key: Optional[str] = None
    collector_key: Optional[str] = None
    role_visibility: List[str] = field(default_factory=list)
    lineage_refs: List[str] = field(default_factory=list)
    dimensions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetricValue:
    metric_id: str
    label: str
    value: Any
    unit: str
    formula: str
    source_basis: str
    validation_status: str
    confidence_state: str
    lineage_refs: List[str]
    role_visibility: List[str]
    grain: Optional[str] = None
    source_reports: List[str] = field(default_factory=list)
    display_surfaces: List[str] = field(default_factory=list)
    components: Dict[str, Any] = field(default_factory=dict)
    caveats: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetricLink:
    source_metric_id: str
    target_metric_id: str
    classification: str
    confidence: float
    caveat: Optional[str]
    evidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetricCandidate:
    candidate_id: str
    suggested_name: str
    formula: str
    source_reports: List[str]
    business_question: str
    role_value: Dict[str, str]
    lineage_completeness: float
    actionability: str = "medium"
    duplicate_risk: str = "unknown"
    recommended_surface: Optional[str] = None
    priority_score: float = 0.0
    approval_status: str = "proposed"
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChartSpec:
    chart_id: str
    title: str
    surface: str
    chart_type: str
    metric_ids: List[str]
    series: List[Dict[str, Any]]
    source_basis: str
    confidence_state: str
    validation_status: str
    lineage_refs: List[str]
    role_visibility: List[str]
    evidence_available: bool = True
    quickball_prompts: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    validation_id: str
    passed: bool
    severity: str
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EngineRunResult:
    profiles: List[ReportProfile] = field(default_factory=list)
    facts: List[FactRecord] = field(default_factory=list)
    metrics: List[MetricValue] = field(default_factory=list)
    links: List[MetricLink] = field(default_factory=list)
    candidates: List[MetricCandidate] = field(default_factory=list)
    charts: List[ChartSpec] = field(default_factory=list)
    validations: List[ValidationResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profiles": [x.to_dict() for x in self.profiles],
            "facts": [x.to_dict() for x in self.facts],
            "metrics": [x.to_dict() for x in self.metrics],
            "links": [x.to_dict() for x in self.links],
            "candidates": [x.to_dict() for x in self.candidates],
            "charts": [x.to_dict() for x in self.charts],
            "validations": [x.to_dict() for x in self.validations],
            "warnings": self.warnings,
            "errors": self.errors,
        }
