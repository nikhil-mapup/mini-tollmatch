from config.config import DEFAULT_VEHICLE_TYPE


class TollService:
    def __init__(
        self,
        exporter,
        client,
        parser,
        repository,
        output_dir,
        vehicle_type: str = DEFAULT_VEHICLE_TYPE,
    ):
        self.exporter = exporter
        self.client = client
        self.parser = parser
        self.repository = repository
        self.output_dir = output_dir
        self.vehicle_type = vehicle_type

    def process_trip(self, trip, vehicle_type: str | None = None):
        vehicle_type = vehicle_type or self.vehicle_type

        csv_path = self.exporter.export(
            trip,
            self.output_dir,
            vehicle_type=vehicle_type,
        )

        raw_response = self.client.calculate_toll(
            csv_path,
            vehicle_type=vehicle_type,
        )

        result = self.parser.parse(
            trip_id=trip.trip_id,
            unit=trip.unit,
            requested_vehicle_type=vehicle_type,
            response=raw_response,
        )

        self.repository.save(result)
        return result
