"""
Collection name constants. These MUST be used everywhere a collection is
opened — no hardcoded collection-name strings in main.py or elsewhere.
Previously these existed but went unused (main.py had hardcoded strings
that didn't even match these names) — that's fixed now.
"""

GPS_RAW = "gps_raw"
INVOICE_RAW = "invoice_raw"

ROUTE_SEGMENTS = "route_segments"
GPS_GAP_EVENTS = "gps_gap_events"
PHYSICAL_TRIPS = "physical_trips"
TRIP_POINTS = "trip_points"

QUALITY_REPORTS = "quality_reports"

SDK_RESULTS = "sdk_results"
MISMATCHES = "mismatches"

# Not wired in yet.
RECONCILIATION = "reconciliation"