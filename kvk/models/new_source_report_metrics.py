"""Immutable derived reader facts, separate from original publication/audit facts."""

from dataclasses import dataclass

from kvk.models.new_source_observation import MetricValue
from kvk.models.new_source_reporting import CalculatedMetric

REPORT_METRIC_VERSION = "snapshot_report_combat_metrics_v1"


@dataclass(frozen=True, slots=True)
class DerivedReportMetric:
    result: CalculatedMetric
    definition: str
    unit: str
    input_keys: tuple[str, ...]
    precision: str


@dataclass(frozen=True, slots=True)
class SourceReportMetrics:
    publication_id: str
    calculation_version: str
    entity_kind: str
    entity_id: int
    aggregate_revision_id: str | None
    inputs: tuple[tuple[str, MetricValue], ...]
    metrics: tuple[tuple[str, DerivedReportMetric], ...]
    version: str = REPORT_METRIC_VERSION

    def metric(self, key: str) -> CalculatedMetric:
        return dict(self.metrics)[key].result

    def to_dict(self) -> dict:
        """Lossless decimal strings; percentage values remain fractions, not *100."""
        return {
            "version": self.version,
            "publication_id": self.publication_id,
            "calculation_version": self.calculation_version,
            "entity_kind": self.entity_kind,
            "entity_id": str(self.entity_id),
            "aggregate_revision_id": self.aggregate_revision_id,
            "inputs": {
                key: {
                    "value": format(item.value, "f") if item.value is not None else None,
                    "state": item.state.value,
                    "raw": item.raw_token,
                    "unit": (
                        format(item.displayed_unit, "f")
                        if item.displayed_unit is not None
                        else None
                    ),
                    "precision": item.precision_kind,
                }
                for key, item in self.inputs
            },
            "metrics": {
                key: {
                    "value": (
                        format(item.result.value, "f") if item.result.value is not None else None
                    ),
                    "state": item.result.state.value,
                    "reason": item.result.reason,
                    "definition": item.definition,
                    "unit": item.unit,
                    "inputs": list(item.input_keys),
                    "precision": item.precision,
                }
                for key, item in self.metrics
            },
        }
