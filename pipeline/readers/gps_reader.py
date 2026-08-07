import pandas as pd
from models.gps import GPSRecord
class GPSReader:
    def __init__(self, file_path):
        self.file_path = file_path

    def read(self) -> list[GPSRecord]:
        df = pd.read_parquet(self.file_path)
        return [GPSRecord(**row) for row in df.to_dict(orient="records")]
        