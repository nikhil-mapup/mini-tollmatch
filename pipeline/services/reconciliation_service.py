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
                mismatch_type="unassigned",
                billed_amount=invoice.amount,
            )
        toll_point = self.toll_index.lookup(invoice.unit, invoice.toll_loc_name_start)

        if toll_point is None or toll_point.start_lat is None or toll_point.start_lng is None:

            return Mismatch(
                transaction_id=invoice.transaction_id,
                entry_time=invoice.entry_time,
                unit=invoice.unit,
                mismatch_type="unassigned",
                billed_amount=invoice.amount,
            )

        confirmed_point, time_delta = self._confirm_match(invoice, unit_gps_points, toll_point)

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
        mismatch_type = self._classify_delta(delta, invoice.amount, toll_point, billing_method)
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

    def _confirm_match(self, invoice, gps_points: list, toll_point):
        best_point = None
        best_delta = None
        for point in gps_points:
            time_delta = abs(point.gps_timestamp - invoice.entry_time)
            if time_delta > self.time_tolerance:
                continue
            distance = haversine_distance_km(
                point.latitude, point.longitude, toll_point.start_lat, toll_point.start_lng
            )
            if distance > self.distance_km:
                continue
            if best_delta is None or time_delta < best_delta:
                best_point = point
                best_delta = time_delta
        return best_point, best_delta

    def _select_expected_amount(self, invoice, toll_point):
        has_tag = bool(invoice.tag_no and str(invoice.tag_no).strip())
        if has_tag:
            if toll_point.tag_cost is not None:
                return "tag", toll_point.tag_cost
        else:
            if toll_point.license_plate_cost is not None:
                return "plate", toll_point.license_plate_cost

        if toll_point.cash_cost is not None:
            return "cash_fallback", toll_point.cash_cost

        return (None, None)

    def _classify_delta(self, delta: float, billed_amount: float, toll_point, billing_method: str) -> str:
        if abs(delta) <= self.amount_tolerance:
            return "matched"

        max_reference = toll_point.tag_cost_max if billing_method == "tag" else None
        if max_reference is not None and abs(billed_amount - max_reference) <= self.amount_tolerance:
            return "max_toll"

        # Confirmed GPS+location match, but amount is wrong for a reason
        # other than the max-toll fallback pattern — "Misread".
        return "misread"

    def _find_containing_trip_id(self, point, unit_trips: list) -> str | None:
        for trip in unit_trips:
            if trip.start_time <= point.gps_timestamp <= trip.end_time:
                return trip.trip_id
        return None

    def _flag_duplicates(self, mismatches: list[Mismatch]):
        seen: dict[tuple, list[Mismatch]] = {}
        for m in mismatches:
            if not m.matched_toll_point_name or m.mismatch_type in ("unassigned", "unmatched"):
                continue
            key = (m.unit, m.matched_toll_point_name)
            seen.setdefault(key, []).append(m)

        for group in seen.values():
            if len(group) < 2:
                continue
            for m in group[1:]:
                m.mismatch_type = "duplicate"