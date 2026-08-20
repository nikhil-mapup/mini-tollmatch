# Mini TollMatch Data Pipeline Logic

## 1. Purpose

This document describes the current data pipeline, how data moves through the
system, what each stage produces, and the assumptions behind the reconciliation
logic.

The goal is to reconstruct vehicle journeys, calculate expected toll events for
those journeys, and reconcile those expected toll events against actual invoice
transactions.

## 2. High-Level Flow

```text
GPS parquet
  |
  v
Unit/date filtering
  |
  v
GPS validation
  |
  v
Group GPS by unit
  |
  v
Route segmentation
  |    |
  |    `--> GPS gap events
  v
Route stitching
  |
  v
Physical trips
  |
  v
One CSV per physical trip
  |
  v
TollMatch/TollGuru API
  |
  v
SDK toll results
  |
  v
Toll location index
  |
  +-------------------+
  |                   |
  v                   v
GPS gap/toll       Invoice CSV
correlation          |
                     v
                  Unit/date filtering
                     |
                     v
                  MongoDB invoice_raw
                     |
  +------------------+
  v
Reconciliation
  |
  v
Mismatch records
  |
  +--> MongoDB mismatches
  |
  `--> output/reconciliation.csv
```

## 3. Execution Order

The pipeline starts in `pipeline/main.py`.

1. Create a run ID.
2. Connect to MongoDB.
3. Read GPS records from `data/Fleet_A_gps.parquet`.
4. Filter GPS records by selected units and date range.
5. Validate GPS records.
6. Save a GPS validation quality report.
7. Group valid GPS records by unit.
8. Split each unit's GPS records into route segments.
9. Save route segments and GPS gap events.
10. Stitch compatible route segments into physical trips.
11. Save physical trips.
12. Export each physical trip to a CSV under `output/tollguru/`.
13. Send each CSV to the TollMatch/TollGuru API.
14. Parse and save SDK results.
15. Build an in-memory toll-location index.
16. Correlate GPS gaps against known toll locations.
17. Read invoice records from `data/FleetA_invoices.csv`.
18. Filter invoices by selected units and date range.
19. Save invoice rows to MongoDB with duplicate rejection.
20. Reconcile invoices against detected toll points and GPS traces.
21. Save mismatch records.
22. Export `output/reconciliation.csv`.

## 4. Configuration

Runtime secrets and service URLs belong in `.env` or exported shell variables.
The pipeline reads `.env` from the project root through `python-dotenv`.

Backend and frontend env values are documented in `readme.md`.

Current pipeline thresholds live in `pipeline/config/config.py`:

```text
GPS_GAP_THRESHOLD_MINUTES = 30
ROUTE_STITCH_MAX_GAP_MINUTES = 60
ROUTE_STITCH_MAX_DISTANCE_KM = 5
DWELL_RADIUS_KM = 0.3
DWELL_THRESHOLD_MINUTES = 15
TOLL_MATCH_TIME_TOLERANCE_MINUTES = 25
TOLL_MATCH_DISTANCE_KM = 20
AMOUNT_TOLERANCE_USD = 1.00
DUPLICATE_TIME_WINDOW_MINUTES = 2
```

These values are prototype defaults and should be validated against real fleet
movement, invoice, and toll data before production use.

## 5. GPS Ingestion

`GPSReader` reads the parquet file and converts each row into:

```python
GPSRecord(
    latitude,
    longitude,
    gps_timestamp,
    unit,
)
```

The rest of the pipeline works with typed domain models instead of raw Pandas
rows.

## 6. Invoice Ingestion

`InvoiceReader` reads the invoice CSV and converts each row into:

```python
InvoiceRecord(
    post_date,
    transaction_id,
    tag_no,
    unit,
    cost_center,
    entry_time,
    exit_time,
    toll_loc_name_start,
    entry_plaza,
    toll_loc_name_end,
    exit_plaza,
    toll_class,
    agency,
    amount,
    transactiondesc,
)
```

Invoice `unit` values are normalized so empty strings and text placeholders such
as `nan`, `none`, and `null` become `None`.

## 7. Filtering

`GPSFilter` filters GPS records by `SELECTED_UNITS` when configured.

`DateRangeFilter` applies `WINDOW_START` and `WINDOW_END` to both GPS records
and invoice records. Setting either window value to `None` disables that side of
the date boundary.

## 8. GPS Validation

`GPSValidator` validates every in-scope GPS point.

Current validation rules:

- Latitude must satisfy `-90 <= latitude <= 90`.
- Longitude must satisfy `-180 <= longitude <= 180`.
- `(0, 0)` null-island coordinates are rejected.
- Missing units are rejected.
- Future timestamps are rejected.
- Exact duplicates are rejected by `(unit, timestamp, latitude, longitude)`.

Invalid records are excluded from trip reconstruction.

## 9. Quality Reporting

Every validation run creates a `QualityReport` with:

```text
run_id
stage
total_input
total_valid
total_invalid
exclusion_counts
```

Reports are saved to the `quality_reports` collection so validation loss is
auditable by reason code.

## 10. Grouping by Vehicle

`GroupByUnitProcessor` groups GPS points by `unit`.

GPS points from different vehicles are never sorted and processed together. A
route can only be reconstructed within one physical vehicle.

## 11. Route Segmentation

`RouteSegmenter` sorts each unit's GPS points by timestamp and splits them into
route segments using two independent boundary signals.

### 11.1 Telemetry Gap Boundary

For consecutive GPS points, the segmenter calculates:

```text
gap = next_timestamp - previous_timestamp
```

If the gap is greater than `GPS_GAP_THRESHOLD_MINUTES`, a new route segment is
created and a `GPSGap` is saved.

Current threshold:

```text
30 minutes
```

### 11.2 Stationary Dwell Boundary

The segmenter also detects when the device keeps reporting but the vehicle has
stopped moving. Starting from an anchor point, it scans forward while later
points remain within `DWELL_RADIUS_KM` of the anchor. If the stationary period
lasts at least `DWELL_THRESHOLD_MINUTES`, the dwell period is treated as a trip
boundary.

Current dwell settings:

```text
DWELL_RADIUS_KM = 0.3
DWELL_THRESHOLD_MINUTES = 15
```

Points inside a qualifying dwell period are excluded from both adjacent
segments because they represent the vehicle at rest, not travel.

This exists because telematics devices can continue pinging while parked. A pure
time-gap rule can accidentally turn several days of parked and moving data into
one giant trip when the device never goes silent.

## 12. Route IDs

The GPS dataset does not provide route IDs, so the pipeline generates them:

```text
ROUTE-{unit}-{sequence}
```

Example:

```text
ROUTE-1951-0001
ROUTE-1951-0002
ROUTE-1951-0003
```

Each route ID represents a continuous GPS segment. It is not necessarily a
complete physical trip.

## 13. GPS Gap Events

When a telemetry gap exceeds the configured threshold, the pipeline creates a
`GPSGap` with:

```text
unit
previous_timestamp
next_timestamp
previous_latitude
previous_longitude
next_latitude
next_longitude
gap_seconds
threshold_seconds
route_split
possible_missed_toll
matched_toll_point_name
```

After TollMatch/TollGuru results exist, the gap can be checked against known
toll coordinates. This allows the pipeline to flag:

```text
GPS telemetry gap + near known toll = possible missed toll
```

## 14. Route Stitching

`RouteStitcher` attempts to merge consecutive route segments into a
`PhysicalTrip`.

Two segments can be stitched when:

```text
time_gap <= ROUTE_STITCH_MAX_GAP_MINUTES
and
distance_between_previous_end_and_next_start <= ROUTE_STITCH_MAX_DISTANCE_KM
```

Current configuration:

```text
maximum stitch gap = 60 minutes
maximum stitch distance = 5 km
```

Distance is calculated with the Haversine formula.

Segmentation and stitching are separate decisions:

- Segmentation asks whether a telemetry or dwell signal indicates a boundary.
- Stitching asks whether adjacent segments still plausibly belong to the same
  physical journey.

The pipeline must not stitch merely because two dates are consecutive.

## 15. Physical Trips

A `PhysicalTrip` contains:

```text
trip_id
unit
start_time
end_time
route_ids
gps_point_count
gps_points
```

Trips are saved in the `physical_trips` collection.

## 16. Toll Detection and Calculation

For every physical trip:

```text
PhysicalTrip
  |
  v
TripCSVExporter
  |
  v
TollMatch/TollGuru API
  |
  v
TollGuruParser
  |
  v
SDKResult
```

`TripCSVExporter` writes one CSV with these headers:

```csv
latitude,longitude,timestamp,units
```

The API call sends the CSV file content directly as the request body with:

```text
Content-Type: text/csv
```

The request is not multipart form data.

## 17. Vehicle Type Handling

Vehicle-class handling is currently a known prototype gap.

`DEFAULT_VEHICLE_TYPE` is configured as:

```text
5AxlesTruck
```

The current HTTP client sends `5AxlesTruck` in the `vehicle` query parameter.
There is not yet a confirmed mapping from invoice `toll_class` values to
TollGuru vehicle type enums, and there is no vehicle master-data lookup by
unit.

Any expected toll amount that depends on vehicle class should be treated as
provisional until this is replaced with a real per-trip vehicle type lookup.

## 18. SDK Result Persistence

`TollGuruParser` extracts:

- trip ID and unit;
- requested and returned vehicle type;
- vehicle type mismatch flag;
- toll presence;
- distance in kilometers when available;
- warning types;
- expected toll points.

Each `SDKResult` is saved to `sdk_results`. The repository saves by `trip_id`,
so rerunning the same trip replaces the prior SDK result instead of creating
unbounded duplicates.

## 19. Expected Toll Points

A physical trip can contain multiple toll events. The pipeline stores toll
points rather than only a trip total because invoice rows reconcile at the
transaction level.

Each expected toll point can include:

```text
name
road
agency
state
start_lat
start_lng
arrival_time
tag_cost
tag_cost_min
tag_cost_max
license_plate_cost
cash_cost
```

## 20. Toll Location Index

`TollLocationIndex` indexes toll points by:

```text
unit + normalized toll name
```

The current assumption is that invoice `toll_loc_name_start` can be normalized
and matched to an SDK toll point name. That assumption should be validated
against real invoice and SDK naming conventions.

## 21. GPS Gap to Possible Missed Toll

`GapTollCorrelator` examines GPS gaps after toll locations have been indexed.
If a gap is near a known toll point for the same unit, the gap is marked as a
possible missed toll and written back to MongoDB.

This does not create a billed mismatch by itself. It is an investigation signal
attached to the GPS gap event.

## 22. Invoice Persistence

Invoices are saved to `invoice_raw`.

The repository creates:

- a unique index on `transaction_id`;
- a lookup index on `(unit, entry_time)`.

Duplicate invoice batches are rejected at the MongoDB unique-index layer.

## 23. Reconciliation Logic

`ReconciliationService` reconciles each invoice row against expected toll
points and GPS traces for the same unit.

### 23.1 Unassigned

An invoice becomes `unassigned` when:

- the invoice has no unit; or
- the invoice unit/toll-name combination cannot be found in the toll-location
  index; or
- the indexed toll point does not have coordinates.

### 23.2 Match Confirmation

A toll event is only considered matched when both checks pass:

```text
abs(gps_timestamp - invoice.entry_time) <= TOLL_MATCH_TIME_TOLERANCE_MINUTES
and
distance(gps_point, toll_point) <= TOLL_MATCH_DISTANCE_KM
```

Current settings:

```text
time tolerance = 25 minutes
distance tolerance = 20 km
```

Time alone is not enough. Distance alone is not enough.

### 23.3 Unmatched

An invoice becomes `unmatched` when:

- a toll point was found by name, but no GPS point confirms it within both time
  and distance; or
- the GPS/location match exists but there is no usable expected amount.

### 23.4 Expected Amount Selection

Expected amount is selected from the invoice billing context:

```text
invoice has tag_no -> use tag_cost
invoice has no tag_no -> use license_plate_cost
fallback -> use cash_cost when available
```

The billing method is recorded as `tag`, `plate`, or `cash_fallback`.

### 23.5 Amount Classification

After a GPS/location match and expected amount are found:

```text
delta = billed_amount - expected_amount
```

The mismatch type is:

- `reconciled` when `abs(delta) <= AMOUNT_TOLERANCE_USD`;
- `max_toll` when tag billing is expected and billed amount is within tolerance
  of `tag_cost_max`;
- `misread` for any other confirmed location/time match with an amount delta.

### 23.6 Duplicate Flagging

After initial classification, `_flag_duplicates` groups reconciled candidates by:

```text
unit + matched_toll_point_name
```

For groups with more than one row, rows after the first are marked as
`duplicate`.

The configured `DUPLICATE_TIME_WINDOW_MINUTES` value exists in config, but the
current implementation does not yet apply it when flagging duplicates.

## 24. Mismatch Records

Mismatch records are saved to `mismatches` and include:

```text
transaction_id
unit
trip_id
mismatch_type
entry_time
billing_method
expected_amount
billed_amount
delta_amount
matched_toll_point_name
time_delta_seconds
status
detected_at
```

Current mismatch types:

```text
unassigned
unmatched
duplicate
max_toll
misread
reconciled
```

`entry_time` is stored on mismatch records so dashboard date filters can query
the `mismatches` collection directly.

## 25. Outputs

MongoDB collections:

```text
route_segments
gps_gap_events
physical_trips
trip_points
quality_reports
sdk_results
invoice_raw
mismatches
```

Local generated files:

```text
output/tollguru/<trip_id>.csv
output/reconciliation.csv
```
