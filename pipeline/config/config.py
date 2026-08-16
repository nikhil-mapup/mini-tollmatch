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

# TODO: these three are still placeholders, not yet derived from real data.
# Before trusting them, run the percentile analysis (sorted GPS timestamp
# deltas per unit) and replace each with a value backed by that evidence,
# with a comment citing the percentile that justified it. Do not present
# these numbers to a reviewer as final until that analysis has been run.
GPS_GAP_THRESHOLD_MINUTES = 30
ROUTE_STITCH_MAX_GAP_MINUTES = 60
ROUTE_STITCH_MAX_DISTANCE_KM = 5

# Dwell-based trip boundary detection — added because the pure time-gap
# check above only catches trip boundaries where the GPS device actually
# stops transmitting. Real telematics hardware often pings continuously
# even while parked (this is exactly what produced the week-long
# single-trip bug: 10,713 points, Oct 8-15, zero gaps ever exceeding 30
# minutes because the device never went silent overnight). A dwell check
# catches "the vehicle stopped MOVING" independently of "the device
# stopped REPORTING" — the two are different signals and a real trip
# boundary can be caused by either one.
#
# TODO: like GPS_GAP_THRESHOLD_MINUTES, these are placeholders — validate
# against real GPS traces of known parking/depot dwell times before
# treating them as final. 300m allows for GPS drift and movement around a
# depot lot without falsely extending the dwell; 15 minutes is meant to be
# long enough to not fire on ordinary traffic stops/red lights.
DWELL_RADIUS_KM = 0.3
DWELL_THRESHOLD_MINUTES = 15

# A GPS reading sitting exactly on (0, 0) is not a real location — it's the
# classic "null island" sentinel value for missing/default coordinates.
# It passes a normal lat/lon range check silently (0 is a valid number),
# so it needs its own explicit rule rather than relying on the range check.
NULL_ISLAND_LAT = 0.0
NULL_ISLAND_LON = 0.0

# --- Vehicle type for the toll SDK ---
# TODO: this is the single biggest open gap in the pipeline right now.
# We do not yet have a confirmed mapping from our invoice `toll_class`
# values to TollGuru's real vehicleType enum, and we do not yet have a
# vehicles/master-data collection to look up a trip's real class by unit.
# Until both of those are confirmed, DEFAULT_VEHICLE_TYPE below is used for
# every SDK call, unconditionally. This means: do not trust any expected
# toll amount produced right now if it depends on vehicle-class-specific
# pricing (e.g. express lane truck rates vs. car rates) until this is
# replaced with a real per-trip lookup.
TOLL_CLASS_TO_VEHICLE_TYPE = {
    # "5": "5AxlesTruck",   # <- placeholder, unconfirmed against real API enum
}
DEFAULT_VEHICLE_TYPE = "5AxlesTruck"  # explicit placeholder, NOT a silent default


# Development / assignment window
# SELECTED_UNITS = None means "run every unit found in the file" — this is
# the full-dataset mode. Keep a non-empty list here only when deliberately
# testing against a small, known subset; leave as None for a real run.
SELECTED_UNITS = None

# Set either to None to disable date-range scoping entirely (run every
# record in the file regardless of date). Now actually applied in main.py
# via processors/date_range_filter.py — previously these two constants
# were defined but never used anywhere.

WINDOW_START = None

WINDOW_END = None

TOLLMATCH_API_URL = os.getenv(
    "TOLLMATCH_API_URL"
)

TOLLMATCH_API_KEY = os.getenv(
    "TOLLMATCH_API_KEY"
)

# --- Step 4: invoice comparison ---
# Confirmed by reviewer clarification — a toll is only considered matched
# when BOTH conditions pass. Time alone is not sufficient (a close
# timestamp at the wrong location is not a match) and distance alone is
# not sufficient either (the right location at the wrong time is not a
# match). See services/reconciliation_service.py.
TOLL_MATCH_TIME_TOLERANCE_MINUTES = 25
TOLL_MATCH_DISTANCE_KM = 20

AMOUNT_TOLERANCE_USD = 1.00
DUPLICATE_TIME_WINDOW_MINUTES = 2