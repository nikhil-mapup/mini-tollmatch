import pandas as pd

from models.invoice import InvoiceRecord


class InvoiceReader:

    def __init__(self, file_path):
        self.file_path = file_path

    def read(self) -> list[InvoiceRecord]:

        df = pd.read_csv(
            self.file_path,
            dtype={
                "transaction_id": str,
                "tag_no": str,
                "unit": str,
            },
        )

        # Convert pandas NaN → None
        df = df.astype(object).where(
            pd.notna(df),
            None,
        )

        records = []

        for row in df.to_dict(orient="records"):

            # Normalize unit
            unit = row.get("unit")

            if unit is not None:
                unit = str(unit).strip()

                if not unit or unit.lower() in {
                    "nan",
                    "none",
                    "null",
                }:
                    unit = None

            row["unit"] = unit

            records.append(
                InvoiceRecord(**row)
            )

        return records