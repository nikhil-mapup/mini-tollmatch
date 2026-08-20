from dataclasses import dataclass

from config.config import AMOUNT_TOLERANCE_PERCENT, AMOUNT_TOLERANCE_USD


@dataclass
class VehicleTypeCandidate:
    vehicle_type: str
    expected_amount: float | None
    difference: float | None
    relative_difference: float | None
    matches: bool
    is_max_toll: bool
    toll_point: object


class VehicleTypeMatcher:
    """Compare the invoice against SDK results for 2/3/4/5 axle hypotheses."""

    def __init__(
        self,
        absolute_tolerance: float = AMOUNT_TOLERANCE_USD,
        relative_tolerance: float = AMOUNT_TOLERANCE_PERCENT,
    ):
        self.absolute_tolerance = absolute_tolerance
        self.relative_tolerance = relative_tolerance

    def select_amount(self, invoice, toll_point) -> tuple[str | None, float | None]:
        has_tag = bool(invoice.tag_no and str(invoice.tag_no).strip())

        if has_tag and toll_point.tag_cost is not None:
            return "tag", float(toll_point.tag_cost)

        if not has_tag and toll_point.license_plate_cost is not None:
            return "plate", float(toll_point.license_plate_cost)

        if toll_point.cash_cost is not None:
            return "cash_fallback", float(toll_point.cash_cost)

        return None, None

    def _within_tolerance(self, billed: float, expected: float) -> bool:
        difference = abs(billed - expected)
        return (
            difference <= self.absolute_tolerance
            or difference <= self.relative_tolerance * max(abs(expected), 1.0)
        )

    def _is_max_toll(self, billed: float, point, billing_method: str | None) -> bool:
        if billing_method != "tag":
            return False

        minimum = point.tag_cost_min
        maximum = point.tag_cost_max

        if minimum is None or maximum is None:
            return False

        # If min == max, there is no evidence that a maximum-route charge
        # was applied.
        if maximum <= minimum:
            return False

        return self._within_tolerance(billed, maximum)

    def compare(self, invoice, candidates: list[object]) -> tuple[VehicleTypeCandidate | None, list[VehicleTypeCandidate]]:
        evaluated: list[VehicleTypeCandidate] = []

        for point in candidates:
            if not point.vehicle_type_valid:
                continue

            vehicle_type = (
                point.response_vehicle_type
                or point.requested_vehicle_type
            )
            if not vehicle_type:
                continue

            billing_method, expected = self.select_amount(invoice, point)
            if expected is None:
                continue

            difference = abs(float(invoice.amount) - expected)
            relative_difference = difference / max(abs(expected), 1.0)
            matches = self._within_tolerance(float(invoice.amount), expected)
            is_max = self._is_max_toll(float(invoice.amount), point, billing_method)

            evaluated.append(
                VehicleTypeCandidate(
                    vehicle_type=vehicle_type,
                    expected_amount=expected,
                    difference=difference,
                    relative_difference=relative_difference,
                    matches=matches,
                    is_max_toll=is_max,
                    toll_point=point,
                )
            )

        if not evaluated:
            return None, []

        evaluated.sort(key=lambda c: c.difference if c.difference is not None else float("inf"))
        return evaluated[0], evaluated
