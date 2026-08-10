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

    def process_trip(
        self,
        trip,
    ):

        # Generate CSV 
        csv_path = self.exporter.export(
            trip,
            self.output_dir,
        )
        
        print(f"TollMatch CSV path: {csv_path}")
        print("TollMatch CSV preview:")
        with csv_path.open("r", encoding="utf-8") as file:
            for index, line in enumerate(file):
                if index >= 5:
                    break
                print(line.rstrip())

        # Call TollMatch
        raw_response = self.client.calculate_toll(
            csv_path,
            vehicle_type=self.vehicle_type,
        )

        # Parse response
        result = self.parser.parse(
            trip_id=trip.trip_id,
            unit=trip.unit,
            requested_vehicle_type=self.vehicle_type,
            response=raw_response,
        )

        self.repository.save(result)

        return result