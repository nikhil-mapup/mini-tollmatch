from datetime import timedelta

from config.config import (
    TOLL_MATCH_TIME_TOLERANCE_MINUTES,
    TOLL_MATCH_DISTANCE_KM,
    AMOUNT_TOLERANCE_USD,
    DUPLICATE_TIME_WINDOW_MINUTES,
)
from models.mismatch import Mismatch
from services.toll_location_index import TollLocationIndex
from utils.geo import haversine_distance_km
from utils.text import normalize_plaza_name

class ReconciliationService:

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
        self.amount_tolerance = amount_tolerance
        self.duplicate_window = timedelta(minutes=duplicate_window_minutes)

    def reconcile(self, trips: list, invoices: list) -> list[Mismatch]:
        points_by_unit: dict[str, list] = {}
        trips_by_unit: dict[str, list] = {}
        for trip in trips:
            points_by_unit.setdefault(trip.unit, []).extend(trip.gps_points)
            trips_by_unit.setdefault(trip.unit, []).append(trip)

        mismatches = []
        for invoice in invoices:
            mismatch = self._reconcile_one(
                invoice,
                points_by_unit.get(invoice.unit, []),
                trips_by_unit.get(invoice.unit, []),
            )
            mismatches.append(mismatch)

        self._flag_duplicates(mismatches)
        return mismatches

    def _reconcile_one(self, invoice, unit_gps_points: list, unit_trips: list) -> Mismatch:
        if not invoice.unit:
            return Mismatch(
                transaction_id=invoice.transaction_id,
                entry_time=invoice.entry_time,
                unit="UNKNOWN",
                verdict="unassigned",
                billed_amount=invoice.amount,
            )
        toll_point = self.toll_index.lookup(invoice.unit, invoice.toll_loc_name_start)

        if toll_point is None or toll_point.start_lat is None or toll_point.start_lng is None:

            return Mismatch(
                transaction_id=invoice.transaction_id,
                entry_time=invoice.entry_time,
                unit=invoice.unit,
                verdict="unassigned",
                billed_amount=invoice.amount,
            )

        confirmed_point, time_delta = self._confirm_match(invoice, unit_gps_points, toll_point)
        if not toll_point.vehicle_type_valid:
            return Mismatch(
                transaction_id=invoice.transaction_id,
                entry_time=invoice.entry_time,
                unit=invoice.unit,
                verdict="unassigned",
                reason_code="VEHICLE_TYPE_MISMATCH",
                billed_amount=invoice.amount,
                matched_toll_point_name=toll_point.name,
                time_delta_seconds=(
                    time_delta.total_seconds()
                    if time_delta
                    else None
                ),
            )

        if confirmed_point is None:
            return Mismatch(
                transaction_id=invoice.transaction_id,
                entry_time=invoice.entry_time,
                unit=invoice.unit,
                mismatch_type="unmatched",
                billed_amount=invoice.amount,
                matched_toll_point_name=toll_point.name,
            )

        billing_method, expected_amount = self._select_expected_amount(invoice, toll_point)

        if expected_amount is None:
            return Mismatch(
                transaction_id=invoice.transaction_id,
                entry_time=invoice.entry_time,
                unit=invoice.unit,
                mismatch_type="unmatched",
                billed_amount=invoice.amount,
                matched_toll_point_name=toll_point.name,
                time_delta_seconds=time_delta.total_seconds() if time_delta else None,
            )

        delta = invoice.amount - expected_amount
        mismatch_type = self._classify_delta(
            billed_amount=invoice.amount,
            expected_amount=expected_amount,
            toll_point=toll_point,
            billing_method=billing_method,
        )
        trip_id = self._find_containing_trip_id(confirmed_point, unit_trips)

        return Mismatch(
            transaction_id=invoice.transaction_id,
            entry_time=invoice.entry_time,
            unit=invoice.unit,
            trip_id=trip_id,
            mismatch_type=mismatch_type,
            billing_method=billing_method,
            expected_amount=expected_amount,
            billed_amount=invoice.amount,
            delta_amount=delta,
            matched_toll_point_name=toll_point.name,
            time_delta_seconds=time_delta.total_seconds() if time_delta else None,
        )
        
    def _candidate_trips(self, invoice, unit_trips):
        candidates = []

        for trip in unit_trips:

            if (
                trip.start_time
                <= invoice.entry_time
                <= trip.end_time
            ):
                candidates.append(trip)
                continue

            # Optional tolerance around trip boundaries
            before = invoice.entry_time - self.time_tolerance
            after = invoice.entry_time + self.time_tolerance

            if trip.start_time <= after and trip.end_time >= before:
                candidates.append(trip)

        return candidates

    def _confirm_match(self, invoice, unit_trips, toll_point_candidates):
        candidate_trips = self._candidate_trips(invoice, unit_trips)
        best = None
        for trip in candidate_trips:
            for point in trip.gps_points:
                gps_dt = abs(point.gps_timestamp - invoice.entry_time)
                if gps_dt > self.time_tolerance:
                    continue
                for toll in toll_point_candidates:
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
                    if best is None or score < best["score"]:
                        best = {
                        "trip_id": trip.trip_id,
                        "gps_point": point,
                        "toll_point": toll,
                        "score": score,
                        "gps_time_delta": gps_dt,
                        "sdk_time_delta": sdk_dt,
                        "gps_distance_km": gps_distance,
                        }
        return best

    def _select_expected_amount(self, invoice, toll_point):

        if not toll_point.vehicle_type_valid:
            return None, None

        has_tag = bool(
            invoice.tag_no
            and str(invoice.tag_no).strip()
        )

        if has_tag:
            if toll_point.tag_cost is not None:
                return "tag", toll_point.tag_cost

        else:
            if toll_point.license_plate_cost is not None:
                return "plate", toll_point.license_plate_cost

        if toll_point.cash_cost is not None:
            return "cash_fallback", toll_point.cash_cost

        return None, None
    
    def _within_amount_tolerance(
        self,
        billed: float,
        expected: float,
    ) -> bool:

        absolute_tolerance = self.amount_tolerance
        relative_tolerance = 0.05  # 5%

        difference = abs(billed - expected)

        return (
            difference <= absolute_tolerance
            or
            difference <= (
                relative_tolerance
                * max(expected, 1.0)
            )
        )

    def _classify_delta(
        self,
        billed_amount: float,
        expected_amount: float,
        toll_point,
        billing_method: str,
    ) -> str:

        delta = billed_amount - expected_amount

        if self._within_amount_tolerance(
            billed=billed_amount,
            expected=expected_amount,
        ):
            return "matched"

        max_reference = (
            toll_point.tag_cost_max
            if billing_method == "tag"
            else None
        )

        if (
            max_reference is not None
            and self._within_amount_tolerance(
                billed=billed_amount,
                expected=max_reference,
            )
        ):
            return "max_toll"

        return "misread"

    def _find_containing_trip_id(self, point, unit_trips: list) -> str | None:
        for trip in unit_trips:
            if trip.start_time <= point.gps_timestamp <= trip.end_time:
                return trip.trip_id
        return None

    def _flag_duplicates(self, mismatches: list[Mismatch]):
        groups = {}
        for m in mismatches:
            if not m.matched_toll_point_name or m.verdict in ("unassigned", "unmatched"):
                continue
            key = (m.unit, normalize_plaza_name(m.matched_toll_point_name))
            groups.setdefault(key, []).append(m)

        for records in groups.values():
            records.sort(key=lambda x: x.entry_time)
            for i in range(1, len(records)):
                prev = records[i - 1]
                curr = records[i]
                dt = curr.entry_time - prev.entry_time
                if dt > self.duplicate_window:
                    continue
                same_amount = abs((curr.billed_amount or 0) - (prev.billed_amount or 0)) <= self.amount_tolerance
                same_trip = (prev.trip_id is not None and curr.trip_id is not None and prev.trip_id == curr.trip_id)
                
                if same_amount or same_trip:
                    curr.verdict = "duplicate"
                    curr.reason_code = "DUPLICATE_CLOSE_EVENT"