from pydantic import BaseModel

class QualityReport(BaseModel):
    total_gps_records: int = 0
    valid_gps_records: int = 0
    invalid_gps_records: int = 0
    duplicate_gps_records: int = 0
    future_timestamps: int = 0
    invalid_coordinates: int = 0
    total_invoice_records: int = 0
    invalid_invoice_records: int = 0