from datetime import datetime

from models.sdk_result import ExpectedTollPoint, SDKResult


class TollGuruParser:
    def parse(
        self,
        trip_id: str,
        unit: str,
        requested_vehicle_type: str,
        response: dict,
    ) -> SDKResult:
        summary = response.get("summary", {})
        route = response.get("route", {})

        response_vehicle_type = summary.get("vehicleType")
        vehicle_type_mismatch = bool(
            response_vehicle_type
            and response_vehicle_type != requested_vehicle_type
        )

        toll_points = [
            self._parse_toll_point(
                toll=toll,
                trip_id=trip_id,
                requested_vehicle_type=requested_vehicle_type,
                response_vehicle_type=response_vehicle_type,
                vehicle_type_mismatch=vehicle_type_mismatch,
            )
            for toll in route.get("tolls", [])
        ]

        distance = route.get("distance", {})
        distance_km = None
        if isinstance(distance, dict):
            raw_metric = distance.get("metric")
            if raw_metric is not None:
                try:
                    distance_km = float(str(raw_metric).replace(" km", "").strip())
                except ValueError:
                    pass

        warnings = response.get("warnings", []) or []
        warning_names = [
            w.get("type", "unknown") if isinstance(w, dict) else str(w)
            for w in warnings
        ]

        return SDKResult(
            trip_id=trip_id,
            unit=unit,
            requested_vehicle_type=requested_vehicle_type,
            response_vehicle_type=response_vehicle_type,
            vehicle_type_mismatch=vehicle_type_mismatch,
            has_tolls=bool(route.get("hasTolls", False)),
            distance_km=distance_km,
            warnings=warning_names,
            toll_points=toll_points,
        )

    @staticmethod
    def _parse_time(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def _parse_toll_point(
        self,
        toll: dict,
        trip_id: str,
        requested_vehicle_type: str,
        response_vehicle_type: str | None,
        vehicle_type_mismatch: bool,
    ) -> ExpectedTollPoint:
        # Current SDK response places arrival/name/lat/lng directly on toll.
        # Keep support for a nested `start` object too.
        start = toll.get("start") or toll
        arrival = start.get("arrival") or toll.get("arrival") or {}

        agency_names = toll.get("tollAgencyNames") or []

        tag_cost = toll.get("tagCost")
        tag_max_candidates = [
            toll.get("maxTollTagStart"),
            toll.get("maxTollTagEnd"),
            toll.get("maxTollTagSecStart"),
            toll.get("maxTollTagSecEnd"),
        ]
        tag_max_candidates = [
            float(v) for v in tag_max_candidates if v is not None
        ]

        return ExpectedTollPoint(
            toll_id=str(toll.get("id")) if toll.get("id") is not None else None,
            sdk_trip_id=trip_id,
            name=start.get("name") or toll.get("name"),
            road=start.get("road") or toll.get("road"),
            agency=agency_names[0] if agency_names else None,
            state=start.get("state") or toll.get("state"),
            start_lat=start.get("lat"),
            start_lng=start.get("lng"),
            arrival_time=self._parse_time(arrival.get("time")),
            tag_cost=tag_cost,
            tag_cost_min=tag_cost,
            tag_cost_max=max(tag_max_candidates) if tag_max_candidates else None,
            license_plate_cost=toll.get("licensePlateCost"),
            cash_cost=toll.get("cashCost"),
            requested_vehicle_type=requested_vehicle_type,
            response_vehicle_type=response_vehicle_type,
            vehicle_type_valid=not vehicle_type_mismatch,
        )
