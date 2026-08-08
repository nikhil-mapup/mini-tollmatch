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


# Development / assignment window
SELECTED_UNITS = ["1951", "1027"]

WINDOW_START = datetime(
    2025,
    10,
    8,
    tzinfo=timezone.utc,
)

WINDOW_END = datetime(
    2025,
    10,
    11,
    tzinfo=timezone.utc,
)