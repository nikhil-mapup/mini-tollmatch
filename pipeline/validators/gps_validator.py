from datetime import datetime, timezone
from config.config import NULL_ISLAND_LAT, NULL_ISLAND_LON
from models.gps import GPSRecord
from models.validation import ValidationResult, InvalidRecord

class GPSValidator:
    def validate(self, records: list[GPSRecord]) -> ValidationResult[GPSRecord]:

        valid = []
        invalid = []
        seen = set()

        now = datetime.now(timezone.utc)

        for record in records:
            errors = []

            if not (-90 <= record.latitude <= 90):
                errors.append("INVALID_LATITUDE")

            if not (-180 <= record.longitude <= 180):
                errors.append("INVALID_LONGITUDE")

            if record.latitude == NULL_ISLAND_LAT and record.longitude == NULL_ISLAND_LON:
                errors.append("NULL_ISLAND_COORDINATES")

            if record.unit is None:
                errors.append("MISSING_UNIT")

            if record.gps_timestamp > now:
                errors.append("FUTURE_TIMESTAMP")

            key = (
                record.unit,
                record.gps_timestamp,
                record.latitude,
                record.longitude,
            )

            if key in seen:
                errors.append("DUPLICATE_GPS")
            else:
                seen.add(key)

            if errors:
                invalid.append(InvalidRecord(record=record, errors=errors))
            else:
                valid.append(record)

        return ValidationResult(valid_records=valid, invalid_records=invalid)