from pathlib import Path

import json
import requests


class TollMatchClient:
    def __init__(self, api_url: str, api_key: str, timeout: int = 120):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def calculate_toll(self, csv_path: Path, vehicle_type: str) -> dict:
        url = f"{self.api_url}/gps-tracks-csv-upload-intermediate"
        headers = {"x-api-key": self.api_key, "Content-Type": "text/csv"}
        params = {
            "mapProvider": "osrm",
            "vehicle": json.dumps({"type": vehicle_type}),
        }

        print(
            f"Sending TollGuru request: vehicle={vehicle_type}, "
            f"csv={csv_path.name}"
        )

        with csv_path.open("rb") as file:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                data=file,
                timeout=self.timeout,
            )

        print(f"TollGuru API status: {response.status_code}")

        if not response.ok:
            raise RuntimeError(
                f"TollGuru API failed: {response.status_code} {response.text}"
            )

        result = response.json()
        returned_vehicle_type = result.get("summary", {}).get("vehicleType")
        if returned_vehicle_type and returned_vehicle_type != vehicle_type:
            print(
                f"WARNING: requested={vehicle_type}, "
                f"response={returned_vehicle_type}"
            )
        return result
