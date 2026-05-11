"""
SCIP Batch 18 Analytics Transformation Engine - runtime orchestrator.

Additive overlay for Batch 13. It can run standalone and can later be mounted behind
an authenticated API route. It never computes frontend business logic; it returns
server-side facts, metrics, links, candidate metrics, chart specs, and validations.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from analytics_models import EngineRunResult
from analytics_utils import utc_now
from analytics_validation import AnalyticsValidationEngine
from chart_spec_factory import ChartSpecFactory
from metric_compiler import MetricCompiler
from metric_linker import MetricLinker
from metric_registry import MetricRegistry
from metric_suggestion_engine import MetricSuggestionEngine
from report_profiler import ReportProfiler
from semantic_fact_builder import SemanticFactBuilder


class AnalyticsTransformationEngine:
    def __init__(self, registry_path: str | Path | None = None):
        registry = MetricRegistry(registry_path)
        self.profiler = ReportProfiler()
        self.fact_builder = SemanticFactBuilder()
        self.compiler = MetricCompiler(registry)
        self.linker = MetricLinker()
        self.suggester = MetricSuggestionEngine()
        self.chart_factory = ChartSpecFactory()
        self.validator = AnalyticsValidationEngine()

    def run(self, report_files: Dict[str, str | Path], role: str = "Board/CXO", surface: Optional[str] = None) -> EngineRunResult:
        result = EngineRunResult()
        for code, path in sorted(report_files.items()):
            source_path = Path(path)
            if not source_path.exists():
                result.errors.append(f"{code}: file not found: {source_path}")
                continue
            try:
                result.profiles.append(self.profiler.profile_report(code, source_path))
            except Exception as exc:
                result.warnings.append(f"{code}: profile failed: {exc}")
            try:
                result.facts.extend(self.fact_builder.build_facts(code, source_path))
            except Exception as exc:
                result.errors.append(f"{code}: fact build failed: {exc}")

        try:
            result.metrics = self.compiler.compile_metrics(result.facts)
        except Exception as exc:
            result.errors.append(f"metric compilation failed: {exc}")
        try:
            result.links = self.linker.link_metrics(result.metrics)
        except Exception as exc:
            result.warnings.append(f"metric linking failed: {exc}")
        try:
            result.candidates = self.suggester.suggest_metrics(result.facts)
        except Exception as exc:
            result.warnings.append(f"metric suggestion failed: {exc}")
        try:
            result.charts = self.chart_factory.create_chart_specs(result.metrics, role=role, surface=surface)
        except Exception as exc:
            result.warnings.append(f"chart spec creation failed: {exc}")
        try:
            result.validations = self.validator.validate(result.facts, result.metrics)
        except Exception as exc:
            result.warnings.append(f"analytics validation failed: {exc}")
        return result

    def quick_summary(self, report_files: Dict[str, str | Path], role: str = "Board/CXO") -> Dict:
        run = self.run(report_files, role=role)
        return {
            "generated_at": utc_now(),
            "profile_count": len(run.profiles),
            "fact_count": len(run.facts),
            "metric_count": len(run.metrics),
            "linked_metric_count": len(run.links),
            "candidate_count": len(run.candidates),
            "chart_count": len(run.charts),
            "blocked_metric_count": sum(1 for m in run.metrics if str(m.confidence_state).startswith("blocked")),
            "errors": run.errors,
            "warnings": run.warnings,
        }


def build_default_report_file_map(data_dir: str | Path) -> Dict[str, Path]:
    """Resolve uploaded/staging R-series files using filename prefixes."""
    base = Path(data_dir)
    patterns = {
        "R01": "R01*.xlsx", "R02": "R02*.xlsx", "R04": "R04*.xlsx", "R08": "R08*.xlsx",
        "R09": "R09*.xlsx", "R10": "R10*.xlsx", "R16": "R16*.xlsx", "R17": "R17*.xlsx",
        "R18": "R18*.xlsx", "R20": "R20*.xlsx", "R30": "R30*.xlsx", "R31": "R31*.xlsx",
        "R32": "R32*.xlsx", "R34": "R34*.xlsx", "R36": "R36*.xlsx", "R38": "R38*.xlsx",
    }
    out: Dict[str, Path] = {}
    for code, pattern in patterns.items():
        matches = sorted(base.glob(pattern))
        if matches:
            out[code] = matches[-1]
    return out
