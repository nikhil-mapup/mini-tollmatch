import statistics
import uuid
from datetime import datetime, timezone

from config.config import (
    GPS_FILE,
    INVOICE_FILE,
    SELECTED_UNITS,
    WINDOW_START,
    WINDOW_END,
    TOLLMATCH_API_URL,
    TOLLMATCH_API_KEY,
    OUTPUT_DIR,
    SDK_VEHICLE_TYPES,
)
from config import constants
from readers.gps_reader import GPSReader
from readers.invoice_reader import InvoiceReader
from validators.gps_validator import GPSValidator
from processors.gps_filter import GPSFilter
from processors.date_range_filter import DateRangeFilter
from processors.route_trip_stats import TripBuildStats
from database.mongo import MongoDB
from database.route_repository import RouteRepository
from database.gps_gap_repository import GPSGapRepository
from database.trip_repository import TripRepository
from database.trip_point_repository import TripPointRepository
from database.quality_report_repository import QualityReportRepository
from database.sdk_result_repository import SDKResultRepository
from database.invoice_repository import InvoiceRepository
from database.mismatch_repository import MismatchRepository
from services.route_trip_service import RouteTripService
from services.toll_service import TollService
from services.toll_location_index import TollLocationIndex
from services.gap_toll_correlator import GapTollCorrelator
from services.reconciliation_service import ReconciliationService
from tollmatch.client import TollMatchClient
from tollmatch.csv_exporter import TripCSVExporter
from tollmatch.parser import TollGuruParser
from tollmatch.reconciliation_csv_exporter import ReconciliationCSVExporter


def main():
    run_id = f"{datetime.now(timezone.utc).isoformat()}_{uuid.uuid4().hex[:8]}"
    print(f"Run ID: {run_id}")
    print(f"SDK vehicle candidates: {SDK_VEHICLE_TYPES}")

    mongo = MongoDB()
    quality_repository = QualityReportRepository(
        mongo.get_collection(constants.QUALITY_REPORTS)
    )
    date_filter = DateRangeFilter(WINDOW_START, WINDOW_END)

    # ------------------------------------------------------------
    # STEP 1: GPS reconstruction
    # ------------------------------------------------------------
    print("\n=== Step 1: GPS track reconstruction ===")
    gps_records = GPSReader(GPS_FILE).read()
    print(f"Total GPS records: {len(gps_records)}")

    filtered_gps = GPSFilter(units=SELECTED_UNITS).process(gps_records)
    filtered_gps = date_filter.filter_gps(filtered_gps)
    print(f"Filtered GPS records: {len(filtered_gps)}")

    validation_result = GPSValidator().validate(filtered_gps)
    valid_gps = validation_result.valid_records
    print(
        f"Valid GPS records: {len(valid_gps)}, "
        f"invalid: {len(validation_result.invalid_records)}"
    )

    quality_repository.save(
        QualityReportRepository.build_from_validation(
            run_id=run_id,
            stage="gps_validation",
            result=validation_result,
        )
    )

    route_repository = RouteRepository(
        mongo.get_collection(constants.ROUTE_SEGMENTS)
    )
    gap_repository = GPSGapRepository(
        mongo.get_collection(constants.GPS_GAP_EVENTS)
    )
    trip_repository = TripRepository(
        mongo.get_collection(constants.PHYSICAL_TRIPS)
    )
    trip_point_repository = TripPointRepository(
        mongo.get_collection(constants.TRIP_POINTS)
    )

    route_trip_service = RouteTripService(
        route_repository=route_repository,
        gap_repository=gap_repository,
        trip_repository=trip_repository,
        trip_point_repository=trip_point_repository,
    )

    trip_stats = TripBuildStats()
    trips, gaps = route_trip_service.process(valid_gps, stats=trip_stats)

    print("\n=== Trip Reconstruction Diagnostics ===")
    print(f"GPS points: {trip_stats.gps_points}")
    print(f"Units: {trip_stats.units}")
    print(f"Segments: {trip_stats.segments}")
    print(f"Physical trips: {trip_stats.trips}")
    print(f"Splits caused by GPS gaps: {trip_stats.time_gap_splits}")
    print(f"Splits caused by dwell: {trip_stats.dwell_splits}")
    print(f"Dwell boundaries stitched: {trip_stats.dwell_stitches}")
    print(f"Dwell boundaries creating trips: {trip_stats.dwell_trip_breaks}")
    print(f"Stitch rejected because of time: {trip_stats.stitch_rejections_time}")
    print(f"Stitch rejected because of distance: {trip_stats.stitch_rejections_distance}")
    print(f"Largest GPS gap: {trip_stats.largest_gap_minutes:.2f} minutes")
    print(f"Largest stitch distance: {trip_stats.largest_stitch_distance_km:.2f} km")

    durations = route_trip_service.segmenter.dwell_durations
    if durations:
        print("\n=== Dwell Duration Distribution ===")
        print(f"15-30 min:   {route_trip_service.segmenter.dwell_15_30}")
        print(f"30-60 min:   {route_trip_service.segmenter.dwell_30_60}")
        print(f"60-120 min:  {route_trip_service.segmenter.dwell_60_120}")
        print(f"120-240 min: {route_trip_service.segmenter.dwell_120_240}")
        print(f"240+ min:    {route_trip_service.segmenter.dwell_240_plus}")
        print(f"Count:       {len(durations)}")
        print(f"Average:     {statistics.mean(durations):.2f} min")
        print(f"Median:      {statistics.median(durations):.2f} min")

    # ------------------------------------------------------------
    # STEP 2: SDK
    # Existing SDK results are reused. Only missing vehicle types are called.
    # This is the important resume behavior: an existing 2AxlesTruck result
    # does NOT get called again.
    # ------------------------------------------------------------
    print("\n=== Step 2: toll detection + calculation (TollGuru) ===")

    sdk_repository = SDKResultRepository(
        mongo.get_collection(constants.SDK_RESULTS)
    )

    toll_service = TollService(
        exporter=TripCSVExporter(),
        client=TollMatchClient(
            api_url=TOLLMATCH_API_URL,
            api_key=TOLLMATCH_API_KEY,
        ),
        parser=TollGuruParser(),
        repository=sdk_repository,
        output_dir=OUTPUT_DIR / "tollguru",
    )

    toll_index = TollLocationIndex()
    sdk_calls = 0
    sdk_failures = 0

    # IMPORTANT: every run starts fresh from the current physical trips.
    # We intentionally do NOT reuse existing SDK results from Mongo.
    # Each physical trip is evaluated for every configured vehicle type.
    for trip in trips:
        print(f"\nTrip: {trip.trip_id}")

        for vehicle_type in SDK_VEHICLE_TYPES:
            print(f"  CALL  {vehicle_type}")
            try:
                result = toll_service.process_trip(
                    trip,
                    vehicle_type=vehicle_type,
                )
                toll_index.add_result(result)
                sdk_calls += 1

                if result.vehicle_type_mismatch:
                    print(
                        f"  WARNING: requested={result.requested_vehicle_type} "
                        f"response={result.response_vehicle_type}"
                    )
            except Exception as exc:
                sdk_failures += 1
                print(
                    f"  SDK failed: trip={trip.trip_id}, "
                    f"vehicle={vehicle_type}, error={exc}"
                )

    print("\n=== SDK Summary ===")
    print(f"SDK calls made: {sdk_calls}")
    print(f"SDK failures: {sdk_failures}")

    # ------------------------------------------------------------
    # STEP 3: GPS gap correlation
    # ------------------------------------------------------------
    print("\n=== Step 3: GPS gap / missed toll correlation ===")
    correlator = GapTollCorrelator(toll_index)
    correlated_gaps = correlator.correlate(gaps)

    flagged_count = 0
    for gap in correlated_gaps:
        if gap.possible_missed_toll:
            gap_repository.update_missed_toll_flag(gap)
            flagged_count += 1

    print(
        f"Gaps flagged as possible missed toll: "
        f"{flagged_count} / {len(gaps)}"
    )

    # ------------------------------------------------------------
    # STEP 4: Invoice reconciliation
    # ------------------------------------------------------------
    print("\n=== Step 4: invoice comparison ===")
    invoice_records = InvoiceReader(INVOICE_FILE).read()
    print(f"Total invoice records: {len(invoice_records)}")

    if SELECTED_UNITS:
        selected = set(SELECTED_UNITS)
        invoice_records = [
            inv for inv in invoice_records
            if inv.unit in selected
        ]

    invoice_records = date_filter.filter_invoices(invoice_records)
    print(f"Filtered invoice records: {len(invoice_records)}")

    invoice_repository = InvoiceRepository(
        mongo.get_collection(constants.INVOICE_RAW)
    )
    ingest = invoice_repository.save_many(invoice_records)
    print(
        f"Invoices inserted: {ingest['inserted']}, "
        f"duplicates rejected: {ingest['duplicates_rejected']}"
    )

    reconciliation_service = ReconciliationService(
        toll_index=toll_index,
    )
    results = reconciliation_service.reconcile(
        trips=trips,
        invoices=invoice_records,
    )

    mismatch_repository = MismatchRepository(
        mongo.get_collection(constants.MISMATCHES)
    )
    mismatch_repository.save_many(results)

    # Business-facing breakdown.
    breakdown = {}
    for result in results:
        key = (
            result.mismatch_type
            if result.verdict == "mismatch" and result.mismatch_type
            else result.verdict
        )
        breakdown[key] = breakdown.get(key, 0) + 1

    print("\n=== Reconciliation Breakdown ===")
    for key, count in sorted(breakdown.items()):
        print(f"{key}: {count}")

    output_path = OUTPUT_DIR / "reconciliation.csv"
    ReconciliationCSVExporter().export(results, output_path)
    print(f"\nReconciliation CSV written to: {output_path}")


if __name__ == "__main__":
    main()
