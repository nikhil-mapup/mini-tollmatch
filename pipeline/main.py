import uuid
from datetime import datetime, timezone

from config.config import (
    GPS_FILE, INVOICE_FILE, SELECTED_UNITS, WINDOW_START, WINDOW_END,
    TOLLMATCH_API_URL, TOLLMATCH_API_KEY, OUTPUT_DIR,
)
from config import constants

from readers.gps_reader import GPSReader
from readers.invoice_reader import InvoiceReader
from validators.gps_validator import GPSValidator
from processors.gps_filter import GPSFilter
from processors.date_range_filter import DateRangeFilter

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
    # run_id = f"{datetime.now(timezone.utc).isoformat()}_{uuid.uuid4().hex[:8]}"
    # print(f"Run ID: {run_id}")

    mongo = MongoDB()
    quality_repository = QualityReportRepository(mongo.get_collection(constants.QUALITY_REPORTS))
    date_filter = DateRangeFilter(WINDOW_START, WINDOW_END)

    print("\n=== Step 1: GPS track reconstruction ===")
    gps_records = GPSReader(GPS_FILE).read()
    print(f"Total GPS records: {len(gps_records)}")

    filtered_gps = GPSFilter(units=SELECTED_UNITS).process(gps_records)
    filtered_gps = date_filter.filter_gps(filtered_gps)
    print(f"Filtered GPS records (unit + date range): {len(filtered_gps)}")

    validation_result = GPSValidator().validate(filtered_gps)
    valid_gps = validation_result.valid_records
    print(f"Valid GPS records: {len(valid_gps)}, invalid: {len(validation_result.invalid_records)}")

    gps_quality_report = QualityReportRepository.build_from_validation(
        run_id=run_id, stage="gps_validation", result=validation_result
    )
    quality_repository.save(gps_quality_report)
    print(f"GPS quality report saved: {gps_quality_report.exclusion_counts}")

    route_repository = RouteRepository(mongo.get_collection(constants.ROUTE_SEGMENTS))
    gap_repository = GPSGapRepository(mongo.get_collection(constants.GPS_GAP_EVENTS))
    trip_repository = TripRepository(mongo.get_collection(constants.PHYSICAL_TRIPS))
    trip_point_repository = TripPointRepository(mongo.get_collection(constants.TRIP_POINTS))

    route_trip_service = RouteTripService(
        route_repository=route_repository, gap_repository=gap_repository,
        trip_repository=trip_repository, trip_point_repository=trip_point_repository,
    )

    trips, gaps = route_trip_service.process(valid_gps)
    print(f"Physical trips created: {len(trips)}, GPS gaps detected: {len(gaps)}")

    print("\n=== Step 2: toll detection + calculation (TollGuru) ===")
    sdk_result_repository = SDKResultRepository(mongo.get_collection(constants.SDK_RESULTS))

    toll_service = TollService(
        exporter=TripCSVExporter(),
        client=TollMatchClient(api_url=TOLLMATCH_API_URL, api_key=TOLLMATCH_API_KEY),
        parser=TollGuruParser(),
        repository=sdk_result_repository,
        output_dir=OUTPUT_DIR / "tollguru",
    )

    toll_index = TollLocationIndex()
    sdk_failures = 0
    for trip in trips:
        print(f"Calculating toll for {trip.trip_id}")
        try:
            result = toll_service.process_trip(trip)
            toll_index.add_result(result)
            if result.warnings:
                print(f"  warnings: {result.warnings}")
            if result.vehicle_type_mismatch:
                print(f"  WARNING: requested={result.requested_vehicle_type} got={result.response_vehicle_type}")
        except Exception as e:
            sdk_failures += 1
            print(f"  SDK call failed for {trip.trip_id}: {e}")

    print(f"SDK calls succeeded: {len(trips) - sdk_failures}, failed: {sdk_failures}")

    print("\n=== Correlating GPS gaps against known toll locations ===")
    correlator = GapTollCorrelator(toll_index)
    correlated_gaps = correlator.correlate(gaps)
    flagged_count = 0
    for gap in correlated_gaps:
        if gap.possible_missed_toll:
            gap_repository.update_missed_toll_flag(gap)
            flagged_count += 1
    print(f"Gaps flagged as possible missed toll: {flagged_count} / {len(gaps)}")

    print("\n=== Step 4: invoice comparison ===")
    invoice_records = InvoiceReader(INVOICE_FILE).read()
    print(f"Total invoice records: {len(invoice_records)}")

    if SELECTED_UNITS:
        selected = set(SELECTED_UNITS)
        invoice_records = [inv for inv in invoice_records if inv.unit in selected]
    invoice_records = date_filter.filter_invoices(invoice_records)
    print(f"Filtered invoice records (unit + date range): {len(invoice_records)}")

    invoice_repository = InvoiceRepository(mongo.get_collection(constants.INVOICE_RAW))
    invoice_ingest_result = invoice_repository.save_many(invoice_records)
    print(f"Invoices inserted: {invoice_ingest_result['inserted']}, "
          f"duplicates rejected: {invoice_ingest_result['duplicates_rejected']}")

    reconciliation_service = ReconciliationService(toll_index=toll_index)
    mismatches = reconciliation_service.reconcile(trips=trips, invoices=invoice_records)

    mismatch_repository = MismatchRepository(mongo.get_collection(constants.MISMATCHES))
    mismatch_repository.save_many(mismatches)

    type_counts = {}
    for m in mismatches:
        type_counts[m.mismatch_type] = type_counts.get(m.mismatch_type, 0) + 1
    print(f"Mismatch breakdown: {type_counts}")

    output_path = OUTPUT_DIR / "reconciliation.csv"
    ReconciliationCSVExporter().export(mismatches, output_path)
    print(f"\nReconciliation CSV written to: {output_path}")


if __name__ == "__main__":
    main()