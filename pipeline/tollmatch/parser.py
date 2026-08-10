from datetime import datetime

from models.sdk_result import ExpectedTollPoint, SDKResult


class TollGuruParser:

    def parse(self, trip_id: str, unit: str, requested_vehicle_type: str, response: dict) -> SDKResult:
        summary = response.get("summary", {})
        route = response.get("route", {})

        response_vehicle_type = summary.get("vehicle")
        vehicle_type_mismatch = bool(
            response_vehicle_type and response_vehicle_type != requested_vehicle_type
        )

        toll_points = [
            self._parse_toll_point(toll) for toll in route.get("tolls", [])
        ]

        distance = route.get("distance", {})
        distance_km = None
        if isinstance(distance, dict) and "metric" in distance:
            try:
                distance_km = float(str(distance["metric"]).replace(" km", "").strip())
            except ValueError:
                distance_km = None

        return SDKResult(
            trip_id=trip_id,
            unit=unit,
            requested_vehicle_type=requested_vehicle_type,
            response_vehicle_type=response_vehicle_type,
            vehicle_type_mismatch=vehicle_type_mismatch,
            has_tolls=bool(route.get("hasTolls", False)),
            distance_km=distance_km,
            warnings=[w.get("type", "unknown") for w in response.get("warnings", [])],
            toll_points=toll_points,
        )

    def _parse_toll_point(self, toll: dict) -> ExpectedTollPoint:
        start = toll.get("start", toll)
        arrival = start.get("arrival", {})
        arrival_time = None
        if arrival.get("time"):
            try:
                arrival_time = datetime.fromisoformat(arrival["time"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                arrival_time = None

        agency_names = toll.get("tollAgencyNames") or []

        return ExpectedTollPoint(
            name=start.get("name") or toll.get("name"),
            road=start.get("road") or toll.get("road"),
            agency=agency_names[0] if agency_names else None,
            state=start.get("state") or toll.get("state"),
            start_lat=start.get("lat"),
            start_lng=start.get("lng"),
            arrival_time=arrival_time,
            tag_cost=toll.get("tagCost"),
            tag_cost_min=toll.get("tagCostMin"),
            tag_cost_max=toll.get("tagCostMax"),
            license_plate_cost=toll.get("licensePlateCost") or toll.get("licensePlateCostMax"),
            cash_cost=toll.get("cashCost"),
        )
