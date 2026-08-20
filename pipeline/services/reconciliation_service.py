from datetime import timedelta

from config.config import (
    TOLL_MATCH_TIME_TOLERANCE_MINUTES,
    TOLL_MATCH_DISTANCE_KM,
    AMOUNT_TOLERANCE_USD,
    AMOUNT_TOLERANCE_PERCENT,
    DUPLICATE_TIME_WINDOW_MINUTES,
)
from models.mismatch import Mismatch
from services.toll_location_index import TollLocationIndex
from services.vehicle_type_matcher import VehicleTypeMatcher
from utils.geo import haversine_distance_km
from utils.text import normalize_plaza_name


class ReconciliationService:
    """Applies the business reconciliation decision tree.

    1. No unit -> unassigned.
    2. Duplicate detection is applied after the base classification.
    3. Find the physical trip/GPS evidence around the invoice event.
    4. If GPS strongly says the unit was elsewhere -> misread (real
       absence evidence only).
    5. If GPS evidence is unavailable entirely -> unmatched (folded in
       from insufficient_gps — no reference data could be checked here,
       same shape as unmatched's other paths, not an absence finding).
    6. If GPS supports the toll, compare 2/3/4/5 axle SDK candidates.
    7. Invoice matches maximum reference -> max_toll.
    8. Invoice matches a vehicle hypothesis -> matched.
    9. Otherwise -> unmatched.
    """

    def __init__(
        self,
        toll_index: TollLocationIndex,
        time_tolerance_minutes: float = TOLL_MATCH_TIME_TOLERANCE_MINUTES,
        distance_km: float = TOLL_MATCH_DISTANCE_KM,
        amount_tolerance: float = AMOUNT_TOLERANCE_USD,
        duplicate_window_minutes: float = DUPLICATE_TIME_WINDOW_MINUTES,
    ):
        self.toll_index = toll_index
        self.time_tolerance = timedelta(minutes=time_tolerance_minutes)
        self.distance_km = distance_km
        self.strong_gps_window = timedelta(minutes=max(time_tolerance_minutes * 2, 60))
        self.duplicate_window = timedelta(minutes=duplicate_window_minutes)
        self.vehicle_matcher = VehicleTypeMatcher(
            absolute_tolerance=amount_tolerance,
            relative_tolerance=AMOUNT_TOLERANCE_PERCENT,
        )

    def reconcile(self, trips: list, invoices: list) -> list[Mismatch]:
        trips_by_unit: dict[str, list] = {}
        for trip in trips:
            trips_by_unit.setdefault(trip.unit, []).append(trip)

        for unit_trips in trips_by_unit.values():
            unit_trips.sort(key=lambda t: t.start_time)

        results = []
        for invoice in invoices:
            results.append(
                self._reconcile_one(
                    invoice,
                    trips_by_unit.get(invoice.unit, []) if invoice.unit else [],
                )
            )

        self._flag_duplicates(results)
        return results

    def _base(
        self,
        invoice,
        verdict: str,
        mismatch_type: str | None = None,
        **kwargs,
    ) -> Mismatch:
        return Mismatch(
            transaction_id=invoice.transaction_id,
            entry_time=invoice.entry_time,
            unit=invoice.unit,
            verdict=verdict,
            mismatch_type=mismatch_type,
            billed_amount=float(invoice.amount),
            **kwargs,
        )

    def _candidate_trips(self, invoice, unit_trips: list) -> list:
        """A trip is a candidate if it contains the invoice time or overlaps it."""
        before = invoice.entry_time - self.time_tolerance
        after = invoice.entry_time + self.time_tolerance
        return [
            trip
            for trip in unit_trips
            if trip.start_time <= after and trip.end_time >= before
        ]

    def _reconcile_one(self, invoice, unit_trips: list) -> Mismatch:
        
        if not invoice.unit:
            return self._base(
                invoice,
                verdict="unassigned",
                reason_code="NO_UNIT_ON_INVOICE",
            )

        
        toll_candidates = self.toll_index.lookup(
            invoice.unit,
            invoice.toll_loc_name_start,
        )

        if not toll_candidates:
            return self._base(
                invoice,
                verdict="mismatch",
                mismatch_type="unmatched",
                reason_code="REFERENCE_TOLL_NOT_FOUND",
            )

       
        candidate_trips = self._candidate_trips(
            invoice,
            unit_trips,
        )

        
        best = None
        evaluated = []

        # If we have candidate trips, prefer SDK toll points
        # belonging to those trips.
        if candidate_trips:

            candidate_trip_ids = {
                trip.trip_id
                for trip in candidate_trips
            }

            matching_points = [
                point
                for point in toll_candidates
                if point.sdk_trip_id in candidate_trip_ids
            ]

            if not matching_points:
                matching_points = toll_candidates

            best, evaluated = self.vehicle_matcher.compare(
                invoice,
                matching_points,
            )

        else:
            # No physical trip around invoice time.
            #
            # We can still use the SDK reference points that
            # belong to this unit.
            best, evaluated = self.vehicle_matcher.compare(
                invoice,
                toll_candidates,
            )

        

        expected_amount = (
            best.expected_amount
            if best is not None
            else None
        )

        inferred_vehicle_type = (
            best.vehicle_type
            if best is not None
            else None
        )

        billing_method = None

        if best is not None:
            billing_method, _ = (
                self.vehicle_matcher.select_amount(
                    invoice,
                    best.toll_point,
                )
            )

       

        gps_match = None

        if candidate_trips:
            gps_match = self._confirm_gps_presence(
                invoice,
                candidate_trips,
                toll_candidates,
            )

        

        if candidate_trips and gps_match is None:

            if self._has_gps_coverage_near_time(
                invoice,
                candidate_trips,
            ):

                delta = (
                    float(invoice.amount)
                    - float(expected_amount)
                    if expected_amount is not None
                    else None
                )

                return self._base(
                    invoice,
                    verdict="mismatch",
                    mismatch_type="misread",
                    reason_code="GPS_NOT_AT_INVOICED_TOLL",
                    expected_amount=expected_amount,
                    delta_amount=delta,
                    inferred_vehicle_type=inferred_vehicle_type,
                    matched_toll_point_name=(
                        best.toll_point.name
                        if best is not None
                        else toll_candidates[0].name
                    ),
                    billing_method=billing_method,
                )

            # GPS coverage is insufficient.
            return self._base(
                invoice,
                verdict="mismatch",
                mismatch_type="unmatched",
                reason_code="GPS_COVERAGE_INSUFFICIENT",
                expected_amount=expected_amount,
                delta_amount=(
                    float(invoice.amount)
                    - float(expected_amount)
                    if expected_amount is not None
                    else None
                ),
                inferred_vehicle_type=inferred_vehicle_type,
                matched_toll_point_name=(
                    best.toll_point.name
                    if best is not None
                    else toll_candidates[0].name
                ),
                billing_method=billing_method,
            )

        if not candidate_trips:

            return self._base(
                invoice,
                verdict="mismatch",
                mismatch_type="unmatched",
                reason_code="NO_GPS_TRIP_AROUND_INVOICE_TIME",
                expected_amount=expected_amount,
                delta_amount=(
                    float(invoice.amount)
                    - float(expected_amount)
                    if expected_amount is not None
                    else None
                ),
                inferred_vehicle_type=inferred_vehicle_type,
                matched_toll_point_name=(
                    best.toll_point.name
                    if best is not None
                    else toll_candidates[0].name
                ),
                billing_method=billing_method,
            )


        if best is None:

            return self._base(
                invoice,
                verdict="mismatch",
                mismatch_type="unmatched",
                reason_code="NO_REFERENCE_AMOUNT",
                trip_id=gps_match["trip_id"],
                matched_toll_point_name=(
                    gps_match["toll_point"].name
                ),
                time_delta_seconds=(
                    gps_match["gps_time_delta"]
                    .total_seconds()
                ),
                gps_distance_km=(
                    gps_match["gps_distance_km"]
                ),
            )



        delta = (
            float(invoice.amount)
            - float(best.expected_amount)
        )

        if best.is_max_toll:

            verdict = "mismatch"
            mismatch_type = "max_toll"
            reason_code = "INVOICE_MATCHES_MAX_REFERENCE"

        elif best.matches:

            verdict = "matched"
            mismatch_type = None
            reason_code = "VEHICLE_TYPE_PRICE_MATCH"

        else:

            verdict = "mismatch"
            mismatch_type = "unmatched"
            reason_code = "NO_VEHICLE_TYPE_PRICE_MATCH"

        matching_types = [
            c.vehicle_type
            for c in evaluated
            if c.matches
        ]

        confidence = (
            "high"
            if len(matching_types) == 1
            else (
                "ambiguous"
                if matching_types
                else "none"
            )
        )

        return self._base(
            invoice,
            verdict=verdict,
            mismatch_type=mismatch_type,
            reason_code=reason_code,
            trip_id=gps_match["trip_id"],
            billing_method=billing_method,
            expected_amount=best.expected_amount,
            delta_amount=delta,
            matched_toll_point_name=best.toll_point.name,
            time_delta_seconds=(
                gps_match["gps_time_delta"]
                .total_seconds()
            ),
            gps_distance_km=(
                gps_match["gps_distance_km"]
            ),
            inferred_vehicle_type=best.vehicle_type,
            vehicle_type_confidence=confidence,
        )

    def _confirm_gps_presence(self, invoice, candidate_trips, toll_candidates):
        best = None

        for trip in candidate_trips:
            trip_tolls = [
                t for t in toll_candidates
                if t.sdk_trip_id == trip.trip_id
            ] or toll_candidates

            for point in trip.gps_points:
                gps_dt = abs(point.gps_timestamp - invoice.entry_time)
                if gps_dt > self.time_tolerance:
                    continue

                for toll in trip_tolls:
                    if toll.start_lat is None or toll.start_lng is None:
                        continue

                    gps_distance = haversine_distance_km(
                        point.latitude,
                        point.longitude,
                        toll.start_lat,
                        toll.start_lng,
                    )
                    if gps_distance > self.distance_km:
                        continue

                    sdk_dt = None
                    if toll.arrival_time is not None:
                        sdk_dt = abs(toll.arrival_time - invoice.entry_time)

                    score = (
                        gps_distance,
                        sdk_dt.total_seconds() if sdk_dt else float("inf"),
                        gps_dt.total_seconds(),
                    )
                    candidate = {
                        "trip_id": trip.trip_id,
                        "gps_point": point,
                        "toll_point": toll,
                        "gps_time_delta": gps_dt,
                        "sdk_time_delta": sdk_dt,
                        "gps_distance_km": gps_distance,
                        "score": score,
                    }
                    if best is None or score < best["score"]:
                        best = candidate

        return best

    def _has_gps_coverage_near_time(self, invoice, unit_trips: list) -> bool:
        window_start = invoice.entry_time - self.strong_gps_window
        window_end = invoice.entry_time + self.strong_gps_window
        for trip in unit_trips:
            for point in trip.gps_points:
                if window_start <= point.gps_timestamp <= window_end:
                    return True
        return False

    def _flag_duplicates(self, results: list[Mismatch]):
        groups = {}
        for result in results:
            if not result.unit or not result.matched_toll_point_name:
                continue
            key = (
                result.unit,
                normalize_plaza_name(result.matched_toll_point_name),
            )
            groups.setdefault(key, []).append(result)

        for records in groups.values():
            records.sort(key=lambda x: x.entry_time)
            for i in range(1, len(records)):
                prev = records[i - 1]
                curr = records[i]
                dt = curr.entry_time - prev.entry_time
                if dt > self.duplicate_window:
                    continue

                same_amount = abs(curr.billed_amount - prev.billed_amount) <= self.vehicle_matcher.absolute_tolerance
                same_trip = (
                    prev.trip_id is not None
                    and curr.trip_id is not None
                    and prev.trip_id == curr.trip_id
                )

                if same_amount or same_trip:
                    curr.is_duplicate = True
                    curr.verdict = "duplicate"
                    curr.reason_code = "DUPLICATE_CLOSE_EVENT"