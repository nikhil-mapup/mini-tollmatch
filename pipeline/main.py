from config.config import (GPS_FILE,SELECTED_UNITS,WINDOW_START,WINDOW_END)
from readers.gps_reader import GPSReader
from validators.gps_validator import GPSValidator
from processors.gps_filter import GPSFilter
from database.mongo import MongoDB
from database.route_repository import RouteRepository
from database.gps_gap_repository import GPSGapRepository
from database.trip_repository import TripRepository
from database.trip_point_repository import (TripPointRepository)
from services.route_trip_service import (RouteTripService)

def main():
    gps_records = GPSReader(GPS_FILE).read()
    print(f"Total GPS records: {len(gps_records)}")

    filtered_gps = GPSFilter(units=SELECTED_UNITS, start_time=WINDOW_START, end_time=WINDOW_END).process(gps_records)
    print(f"Filtered GPS records: {len(filtered_gps)}")

    validation_result = (GPSValidator().validate(filtered_gps))

    valid_gps = (validation_result.valid_records)

    print(f"Valid GPS records: {len(valid_gps)}")

    mongo = MongoDB()

    route_repository = RouteRepository(mongo.get_collection("route_segments"))
    gap_repository = GPSGapRepository(mongo.get_collection("gps_gap_events"))
    trip_repository = TripRepository(mongo.get_collection("physical_trips"))
    trip_point_repository = (TripPointRepository(mongo.get_collection("trip_points")))

    service = RouteTripService(route_repository=route_repository, gap_repository=gap_repository, trip_repository=trip_repository, trip_point_repository=(trip_point_repository))

    trips = service.process(valid_gps)

    print(f"Physical trips created: {len(trips)}")

if __name__ == "__main__":
    main()