import csv
from pathlib import Path

from models.mismatch import Mismatch


class ReconciliationCSVExporter:
    HEADERS = [
        "transaction_id",
        "unit",
        "trip_id",
        "mismatch_type",
        "billing_method",
        "expected_amount",
        "billed_amount",
        "delta_amount",
        "matched_toll_point_name",
        "time_delta_seconds",
        "status",
    ]

    def export(self, mismatches: list[Mismatch], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.HEADERS)
            writer.writeheader()
            for m in mismatches:
                row = m.model_dump()
                writer.writerow({k: row.get(k) for k in self.HEADERS})
        return output_path
