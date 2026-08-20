from models.sdk_result import ExpectedTollPoint, SDKResult
from utils.text import normalize_plaza_name


class TollLocationIndex:

    def __init__(self):
        self._by_unit: dict[
            str,
            dict[str, list[ExpectedTollPoint]]
        ] = {}

    def add_result(
        self,
        result: SDKResult,
    ):
        bucket = self._by_unit.setdefault(
            result.unit,
            {},
        )

        for point in result.toll_points:

            key = normalize_plaza_name(
                point.name
            )

            if not key:
                continue

            bucket.setdefault(
                key,
                [],
            ).append(point)

    def lookup(
        self,
        unit: str,
        plaza_name: str | None,
    ) -> list[ExpectedTollPoint]:

        unit_bucket = self._by_unit.get(
            unit,
            {},
        )

        if not plaza_name:
            return self.all_points_for_unit(unit)

        key = normalize_plaza_name(
            plaza_name
        )

        if not key:
            return self.all_points_for_unit(unit)

        # -----------------------------------------------------
        # 1. Exact normalized match
        # -----------------------------------------------------

        exact = unit_bucket.get(key)

        if exact:
            return list(exact)

        # -----------------------------------------------------
        # 2. Token/substring fallback
        #
        # Example:
        #
        # "sam houston south plaza"
        # "sam houston south"
        #
        # -----------------------------------------------------

        candidates = []

        query_tokens = set(
            key.split()
        )

        for indexed_name, points in (
            unit_bucket.items()
        ):

            indexed_tokens = set(
                indexed_name.split()
            )

            if not indexed_tokens:
                continue

            intersection = (
                query_tokens
                & indexed_tokens
            )

            if not intersection:
                continue

            # Require reasonable overlap.
            query_ratio = (
                len(intersection)
                / len(query_tokens)
            )

            indexed_ratio = (
                len(intersection)
                / len(indexed_tokens)
            )

            if (
                query_ratio >= 0.5
                or indexed_ratio >= 0.5
            ):
                candidates.extend(
                    points
                )

        return candidates

    def all_points_for_unit(
        self,
        unit: str,
    ) -> list[ExpectedTollPoint]:

        points = []

        for plaza_points in (
            self._by_unit
            .get(unit, {})
            .values()
        ):

            points.extend(
                plaza_points
            )

        return points