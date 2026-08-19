from models.sdk_result import ExpectedTollPoint, SDKResult
from utils.text import normalize_plaza_name


class TollLocationIndex:

    def __init__(self):
        self._by_unit: dict[str, dict[str, list[ExpectedTollPoint]]] = {}

    def add_result(self, result: SDKResult):
        bucket = self._by_unit.setdefault(result.unit, {})
        for point in result.toll_points:
            key = normalize_plaza_name(point.name)
            if not key:
                continue
            bucket.setdefault(key, []).append(point)

    def lookup(self, unit: str, plaza_name: str | None) -> list[ExpectedTollPoint] | None:
        key = normalize_plaza_name(plaza_name)
        if key is None:
            return None
        return self._by_unit.get(unit, {}).get(key, [])

    def all_points_for_unit(self, unit: str) -> list[ExpectedTollPoint]:
        points = []
        for plaza_points in self._by_unit.get(unit, {}).values():
            points.extend(plaza_points)
        return points