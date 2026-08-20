from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

GPS_FILE = DATA_DIR / "Fleet_A_gps.parquet"
INVOICE_FILE = DATA_DIR / "FleetA_invoices.csv"

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "tollmatch")

GPS_GAP_THRESHOLD_MINUTES = 30
ROUTE_STITCH_MAX_GAP_MINUTES = 60
ROUTE_STITCH_MAX_DISTANCE_KM = 5
TRIP_BREAK_DWELL_MINUTES = 240

DWELL_RADIUS_KM = 0.3
DWELL_THRESHOLD_MINUTES = 15

NULL_ISLAND_LAT = 0.0
NULL_ISLAND_LON = 0.0
DEFAULT_VEHICLE_TYPE = "2AxlesTruck"
SDK_VEHICLE_TYPES = [
    # "2AxlesTruck",
    "3AxlesTruck",
    "4AxlesTruck",
    "5AxlesTruck",
]

SELECTED_UNITS = None


WINDOW_START = None

WINDOW_END = None

TOLLMATCH_API_URL = os.getenv(
    "TOLLMATCH_API_URL"
)

TOLLMATCH_API_KEY = os.getenv(
    "TOLLMATCH_API_KEY"
)

TOLL_MATCH_TIME_TOLERANCE_MINUTES = 25
TOLL_MATCH_DISTANCE_KM = 20

AMOUNT_TOLERANCE_USD = 1.00
AMOUNT_TOLERANCE_PERCENT = 0.05
DUPLICATE_TIME_WINDOW_MINUTES = 2