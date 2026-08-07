import pandas as pd

from models.invoice import InvoiceRecord

class InvoiceReader:
    def __init__(self, file_path):
        self.file_path = file_path
    def read(self) -> list[InvoiceRecord]:
        df = pd.read_csv(
            self.file_path,
            dtype={"transaction_id": str, "tag_no": str, "unit": str},
        )
        df = df.astype(object).where(pd.notna(df), None)
        return [InvoiceRecord(**row) for row in df.to_dict(orient="records")]
