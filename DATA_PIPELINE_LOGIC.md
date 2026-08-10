# Mini TollMatch --- Data Pipeline Logic

## 1. Purpose

This document describes the **current data pipeline, how data moves through the system, what each stage produces, why the stages are separated, and the current assumptions/open
gaps.

The overall goal is to reconstruct vehicle journeys, calculate the tolls
expected on those journeys, and reconcile those expected toll events
against actual invoice transactions.

------------------------------------------------------------------------

# 2. High-Level Architecture

``` text
                    ┌──────────────────┐
                    │   GPS Parquet    │
                    └────────┬─────────┘
                             │
                             ▼
                  Unit + Date Filtering
                             │
                             ▼
                       GPS Validation
                             │
                             ▼
                    Group GPS by Unit
                             │
                             ▼
                    Sort by Timestamp
                             │
                             ▼
                    Route Segmentation
                             │
                             ├──────────────► GPS Gap Events
                             │
                             ▼
                     Route Stitching
                             │
                             ▼
                      Physical Trips
                             │
                             ▼
                 One CSV per Physical Trip
                             │
                             ▼
                       TollMatch API
                             │
                             ▼
                     SDK Toll Results
                             │
                             ├──────────────► Toll Location Index
                             │
                             ▼
                    Expected Toll Points
                             │
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
              GPS Gap/Toll       Invoice CSV
               Correlation            │
                    │                  ▼
                    │           Unit + Date Filter
                    │                  │
                    │                  ▼
                    │           MongoDB Invoice Raw
                    │                  │
                    └──────────┬───────┘
                               ▼
                       Reconciliation
                               │
                               ▼
                         Mismatch Records
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
                 MongoDB          reconciliation.csv
```

------------------------------------------------------------------------

# 3. Main Pipeline Execution

The current execution order is:

``` text
1. Read GPS
2. Filter GPS by unit
3. Filter GPS by date
4. Validate GPS
5. Build route segments
6. Detect GPS gaps
7. Stitch route segments into physical trips
8. Call TollMatch for each physical trip
9. Build toll-location index
10. Correlate GPS gaps with known toll locations
11. Read invoices
12. Filter invoices by unit/date
13. Store invoices in MongoDB
14. Reconcile invoice lines against toll locations + GPS
15. Store mismatch/reconciliation results
16. Export reconciliation.csv
```

------------------------------------------------------------------------

# 4. Stage 1 --- GPS Ingestion and Trip Reconstruction

## 4.1 Read GPS Parquet

The internal model is:

``` python
GPSRecord(
    latitude,
    longitude,
    gps_timestamp,
    unit
)
```
The rest of the pipeline should work with a validated domain object
rather than raw Pandas rows.

------------------------------------------------------------------------

# 5. GPS Validation

`validators/gps_validator.py` validates every in-scope GPS point.

Current validation rules:

## 5.1 Latitude

Must satisfy:

``` text
-90 <= latitude <= 90
```

## 5.2 Longitude

Must satisfy:

``` text
-180 <= longitude <= 180
```

## 5.3 Null Island

The coordinate:

``` text
(0, 0)
```

is explicitly rejected.

Why?

`0,0` passes ordinary latitude/longitude range validation but is
commonly used as a missing/default GPS value.

## 5.4 Missing unit

A GPS record without a vehicle/unit cannot participate in vehicle-level
reconstruction.

## 5.5 Future timestamp

GPS timestamps later than the current UTC time are rejected.

## 5.6 Exact duplicate

The following tuple is used to identify an exact duplicate:

``` text
(unit, timestamp, latitude, longitude)
```

Duplicates are excluded.

------------------------------------------------------------------------

# 6. Data Quality Reporting

Invalid records are not simply discarded.

For every validation run, the pipeline creates a `QualityReport`
containing:

``` text
run_id
stage
total_input
total_valid
total_invalid
exclusion_counts
```

The report is persisted in:

``` text
quality_reports
```

This gives us an audit trail.

Instead of saying:

> "We had 10 invalid GPS points."

we can answer:

``` text
10 invalid records

INVALID_LATITUDE:       2
NULL_ISLAND_COORDINATES: 4
FUTURE_TIMESTAMP:       3
DUPLICATE_GPS:           1
```

------------------------------------------------------------------------

# 7. Group GPS by Vehicle

`GroupByUnitProcessor` groups GPS points by `unit`.

Conceptually:

``` text
GPS
 │
 ├── unit 1027
 │     ├── point
 │     ├── point
 │     └── ...
 │
 ├── unit 1951
 │     ├── point
 │     ├── point
 │     └── ...
 │
 └── unit S17033
       ├── point
       └── ...
```

A route can only be reconstructed within the same physical vehicle.

GPS points from two vehicles must never be sorted and processed
together.

------------------------------------------------------------------------

# 8. Route Segmentation

`RouteSegmenter` sorts each vehicle's GPS points by timestamp.

For consecutive points:

``` text
previous GPS timestamp
        ↓
next GPS timestamp
```

it calculates:

``` text
gap = next_timestamp - previous_timestamp
```

If:

``` text
gap > GPS_GAP_THRESHOLD_MINUTES
```

a new route segment is created.

Current configured threshold:

``` text
30 minutes
```

------------------------------------------------------------------------

# 9. Route IDs

Route IDs are generated because the GPS dataset does not provide a Route
ID.

The current format is:

``` text
ROUTE-{unit}-{sequence}
```

Example:

``` text
ROUTE-1951-0001
ROUTE-1951-0002
ROUTE-1951-0003
```

Each Route ID represents a **continuous GPS segment**, not necessarily a
complete physical trip.

This distinction is important.

``` text
Route Segment
    ↓
may later be stitched
    ↓
Physical Trip
```

------------------------------------------------------------------------

# 10. GPS Gap Events

When a gap exceeds the configured threshold, a `GPSGap` is created.

It contains:

``` text
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

Later, after TollMatch has identified toll locations, the two sides of
the GPS gap can be checked against known toll coordinates.

This allows us to detect:

``` text
GPS telemetry gap
+
near a known toll
=
possible missed toll
```

The gap is therefore not silently thrown away.

------------------------------------------------------------------------

# 11. Route Stitching

After segmentation, `RouteStitcher` attempts to merge consecutive Route
Segments into a `PhysicalTrip`.

Two segments can be stitched when:

``` text
time_gap <= ROUTE_STITCH_MAX_GAP_MINUTES
AND
distance_between_previous_end_and_next_start
    <= ROUTE_STITCH_MAX_DISTANCE_KM
```

Current configuration:

``` text
maximum stitch gap     = 60 minutes
maximum stitch distance = 5 km
```

Distance is calculated using the Haversine formula.

------------------------------------------------------------------------

# 12

These are intentionally separate decisions.

### Segmentation asks:

> "Is there a sufficiently large telemetry gap that we should create a
> new route segment?"

### Stitching asks:

> "Even though the telemetry was interrupted, is the next segment
> plausibly the continuation of the same physical journey?"

Example:

``` text
Route A
ends 23:55
Houston

Route B
starts 00:10
nearby location
```

The date changed, but:

``` text
15 minute gap
+
small geographic distance
```

may indicate one physical journey.

Therefore:

``` text
Route A + Route B
        ↓
Physical Trip
```

We must **not** stitch merely because two dates are consecutive.

------------------------------------------------------------------------

# 13. Stage 2 --- Toll Detection and Calculation

For every `PhysicalTrip`:

``` text
PhysicalTrip
     ↓
CSV export
     ↓
TollMatch GPS Tracks API
     ↓
Raw JSON response
     ↓
TollMatchParser
     ↓
SDKResult
```

------------------------------------------------------------------------

# 14. TollMatch CSV Export

`TripCSVExporter` generates one CSV for each PhysicalTrip.

The intended payload fields are:

``` text
latitude
longitude
timestamp
units
```

The exporter currently writes exactly those header names.

------------------------------------------------------------------------

# 15. Why Toll Points Instead of One Trip Cost?

A physical trip may contain multiple toll events.

For example:

``` text
Physical Trip
    │
    ├── Toll A
    ├── Toll B
    └── Toll C
```

The invoice may contain:

``` text
Invoice A → Toll A
Invoice B → Toll B
Invoice C → Toll C
```

Therefore this would be insufficient:

``` text
Physical Trip
expected_total = $10
```

We need:

``` text
ExpectedTollPoint A
ExpectedTollPoint B
ExpectedTollPoint C
```

so each invoice transaction can be reconciled independently.

------------------------------------------------------------------------

# 16. Expected Toll Cost

The current reconciliation logic selects the expected billing method
based on the invoice:

``` text
invoice has tag_no
        ↓
tag billing
        ↓
use SDK tag_cost
```

If:

``` text
invoice.tag_no is empty
```

the pipeline attempts:

``` text
license plate cost
```

and then has a cash fallback if available.

This is important because the same toll location can have different
rates depending on payment/billing method.

------------------------------------------------------------------------

# 17. SDK Result Persistence

Each `SDKResult` is stored in:

``` text
sdk_results
```

with a unique `trip_id`.

This makes the SDK stage idempotent at the trip level:

``` text
same trip_id
    ↓
replace existing result
```

rather than creating an unlimited number of duplicate SDK result
documents.

------------------------------------------------------------------------

# 18. Toll Location Index

After every successful SDK call, `TollLocationIndex` indexes toll points
by:

``` text
unit
+
normalized toll name
```

Conceptually:

``` text
unit 1951
    │
    ├── normalized toll name A → coordinates + cost
    ├── normalized toll name B → coordinates + cost
    └── normalized toll name C → coordinates + cost
```

The purpose is to convert invoice location information into a known
geographic toll point.

The current assumption is that:

``` text
invoice.toll_loc_name_start
```

can be normalized and matched to:

``` text
SDK toll point name
```

This assumption should be validated against the real invoice/SDK data
because different agencies may use different naming conventions.

------------------------------------------------------------------------

# 19. GPS Gap → Possible Missed Toll

After TollMatch results exist, `GapTollCorrelator` examines previously
detected GPS gaps.

For each gap:

``` text
gap before coordinate
gap after coordinate
```

are compared to known toll coordinates using Haversine distance.

If either side is within:

``` text
20 km
```

of a known toll point, the gap is flagged:

``` text
possible_missed_toll = true
```

This is a warning signal, not proof of a missed toll.

Reason:

``` text
GPS gap near toll
```

could mean:

-   missing telemetry
-   tunnel/network outage
-   toll crossing during telemetry loss
-   unrelated nearby road/toll

Therefore the result is intentionally called a **possible missed toll**.

------------------------------------------------------------------------

# 20. Stage 4 --- Invoice Ingestion

The invoice CSV is read into:

``` text
InvoiceRecord
```

The pipeline then applies:

``` text
unit filter
+
date filter
```

and stores the invoice records in:

``` text
invoice_raw
```

------------------------------------------------------------------------

# 21. Core Reconciliation Rule

The core business rule currently implemented is:

> A toll is considered matched only when BOTH the time and distance
> conditions pass.

### Time

A GPS point for the invoice's vehicle must be within:

``` text
±25 minutes
```

of:

``` text
invoice.entry_time
```

### Distance

That same GPS point must be within:

``` text
20 km
```

Haversine distance of the resolved toll location.

Therefore:

``` text
TIME PASS
    AND
DISTANCE PASS
    =
MATCH
```

Neither condition alone is sufficient.

------------------------------------------------------------------------

# 22. Why the Same GPS Point Must Pass Both

We should not do:

``` text
GPS point A
passes time

GPS point B
passes distance

therefore match
```

That can create a false match.

The implementation searches for a **single GPS point** that satisfies
both:

``` text
abs(GPS timestamp - invoice.entry_time) <= 25 min
AND
Haversine(GPS point, toll coordinates) <= 20 km
```

This is a strong safeguard.

------------------------------------------------------------------------

# 23. Invoice-to-Toll Matching Flow

For each invoice:

``` text
Invoice
  │
  ▼
Find SDK toll point using normalized toll_loc_name_start
  │
  ├── no toll point
  │       ↓
  │    unassigned
  │
  ▼
Find GPS points for same unit
  │
  ▼
Check ±25 minute window
  │
  ▼
Check ≤20 km distance
  │
  ├── no confirming GPS
  │       ↓
  │    unmatched
  │
  ▼
Determine billing method
  │
  ▼
Select expected SDK amount
  │
  ▼
Compare invoice amount
  │
  ▼
Classify reconciliation result
```

------------------------------------------------------------------------

# 24. Amount Reconciliation

Once a toll event is matched:

``` text
expected_amount = SDK selected billing-method cost
actual_amount   = invoice.amount
```

Then:

``` text
delta = actual_amount - expected_amount
```

The current tolerance is:

``` text
AMOUNT_TOLERANCE_USD = $1.00
```

If:

``` text
abs(delta) <= $1
```

the result is:

``` text
reconciled
```

If it does not reconcile, the pipeline can classify patterns such as:

``` text
max_toll
misread
```

according to the current implementation.

------------------------------------------------------------------------

# 25. Important: Max Toll

TollMatch can provide:

``` text
tagCostMin
tagCost
tagCostMax
```

The current logic treats a billed amount close to the maximum reference
as:

``` text
max_toll
```

when the normal expected amount is meaningfully different.

This can help identify cases where the agency billed at a
maximum/fallback rate.

------------------------------------------------------------------------

# 26. Reconciliation Output

Each invoice produces a `Mismatch` record containing information such
as:

``` text
transaction_id
unit
trip_id
mismatch_type

billing_method

expected_amount
billed_amount
delta_amount

matched_toll_point_name
time_delta_seconds

status
detected_at
```

This makes the result explainable rather than simply returning:

``` text
MATCH / NO MATCH
```

------------------------------------------------------------------------

# 27. End-to-End Example

Suppose:

``` text
Vehicle:
1951
```

GPS data contains:

``` text
10:00
10:01
10:02
...
```

A large telemetry gap occurs:

``` text
10:10
      ↓
10:55
```

The pipeline creates:

``` text
ROUTE-1951-0001
ROUTE-1951-0002
```

If the second segment begins close enough in time and geography, they
may be stitched into:

``` text
TRIP-1951-ROUTE-1951-0001
```

That trip's GPS points are sent to TollMatch.

Suppose TollMatch detects:

``` text
Toll A = $8
Toll B = $2
```

The invoice contains:

``` text
Invoice A
unit = 1951
location = Toll A
entry_time = around Toll A crossing
amount = $8
```

The reconciliation engine checks:

``` text
same unit       → YES
time <= 25 min  → YES
distance <= 20 km → YES
```

Then:

``` text
expected = $8
billed   = $8
delta    = $0
```

Result:

``` text
reconciled
```

------------------------------------------------------------------------
