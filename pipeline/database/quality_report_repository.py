from collections import Counter

from models.quality_report import QualityReport
from models.validation import ValidationResult


class QualityReportRepository:

    def __init__(self, collection):
        self.collection = collection
        self.collection.create_index([("run_id", 1), ("stage", 1)])

    def save(self, report: QualityReport):
        self.collection.insert_one(report.model_dump(mode="json"))

    @staticmethod
    def build_from_validation(run_id: str, stage: str, result: ValidationResult) -> QualityReport:
        """
        Every invalid record can have multiple error codes (e.g. a point can be
        both NULL_ISLAND and FUTURE_TIMESTAMP at once) — count each occurrence,
        not just each record, so the summary reflects the real exclusion reasons.
        """
        counts = Counter()
        for invalid in result.invalid_records:
            for error in invalid.errors:
                counts[error] += 1

        return QualityReport(
            run_id=run_id,
            stage=stage,
            total_input=len(result.valid_records) + len(result.invalid_records),
            total_valid=len(result.valid_records),
            total_invalid=len(result.invalid_records),
            exclusion_counts=dict(counts),
        )
