from pathlib import Path
from datetime import datetime

from pydantic import json
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
            'mapProvider': 'osrm',
            'vehicle': '{"type":"5AxlesTruck"}'
            # "vehicle": json.dumps({"type": "5AxlesTruck"})
        }
        print(f"Sending request to TollGuru API at {url} with params: {params} and CSV file: {csv_path}")

        with csv_path.open("rb") as file:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                data=file.read(),
                # timeout=self.timeout,
            )
        print(f"TollGuru API status: {response.status_code}")
        print(f"TollGuru API response body: {response.text}")


        if not response.ok:
            raise RuntimeError(
                "TollGuru API failed: "
                f"{response.status_code} "
                f"{response.text}"
            )

        result = response.json()

        warnings = result.get("warnings", [])
        if warnings:
            print(f"TollGuru returned warnings for {csv_path.name}: {warnings}")

        returned_vehicle_type = result.get("summary", {}).get("vehicleType")
        if returned_vehicle_type and returned_vehicle_type != vehicle_type:
            print(
                f"WARNING: requested vehicleType='{vehicle_type}' but response "
                f"summary reports vehicleType='{returned_vehicle_type}' — "
                "the request may not have been honored. Do not trust this "
                "result's costs as vehicle-class-accurate."
            )

        return result