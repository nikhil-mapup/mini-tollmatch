# Data Pipeline Logic

This is my initial approach for now. I'll refine the logic as I get into the implementation if a better solution comes up.
I have kept the pipeline split into clear stages. Each stage does one job and
passes its output to the next stage. This makes the logic easier to debug,
change, and test later.

---

## Pipeline Overview

```text
GPS.parquet
│
▼
Reader
│
▼
Validation
│
▼
Group By Unit
│
▼
Trip Reconstruction
│
▼
Trip CSV
│
▼
TollMatch SDK
│
▼
SDK Toll Events
│
▼
Invoice Matching
│
▼
Reconciliation
│
▼
MongoDB
```

---

## Stage 1 - Data Ingestion

### Input

- `GPS.parquet`
- `Invoice.csv`

### Output

- Raw MongoDB collections

### Reason

Keeping the raw data available is important. If validation rules or matching logic change later, the pipeline can be rerun from the original imported data instead of asking for the files again.

---

## Stage 2 - Validation

### Purpose

Validation is used to catch bad or incomplete records before they enter the trip-building and matching stages.

### GPS validation rules

- Latitude should be between `-90` and `90`
- Longitude should be between `-180` and `180`
- Unit should be present
- Timestamp should be present
- Timestamp should not be in the future
- Duplicate GPS points should be detected

### Invoice validation rules

- Transaction ID should be present
- Amount should be greater than `0`
- Entry time should be present
- Unit should be present
- Duplicate transaction IDs should be detected

### Output

- Valid records
- Invalid records
- Quality report

---

## Stage 3 - Group By Vehicle

Fleet GPS data contains records for many vehicles.

Example vehicles:

- Truck `1951`
- Truck `8657`
- Truck `8425`

Each vehicle moves independently, so the GPS records are grouped by `Unit`
before trip reconstruction.

### Output

```text
{
  1951: [...],
  8657: [...],
  8425: [...]
}
```

After grouping, each vehicle can be processed separately.

---

## Stage 4 - Trip Reconstruction

### Purpose

This stage converts continuous GPS pings into separate trips.

### Input

- GPS records for one vehicle

### Algorithm

1. Sort the GPS records by timestamp.
2. Read the records in chronological order.
3. Compare the timestamp of each point with the previous point.
4. If the gap is more than the threshold, start a new trip.
5. If the gap is within the threshold, keep adding points to the current trip.

gap threshold = `30 minutes`.

### Output

Trip objects:

```text
Trip
  trip_id
  unit
  start_time
  end_time
  gps_points
```

---

## Stage 5 - Trip CSV Generation

The TollMatch SDK expects GPS tracks in CSV format.

Each reconstructed trip is exported as a separate CSV file, for example:

```text
trip_001.csv
```

---

## Stage 6 - TollMatch SDK

### Input

- Trip CSV

### Output

- Expected toll events

Each SDK toll event contains:

- Toll name
- Coordinates
- Timestamp
- Amount

---

## Stage 7 - Invoice Matching

This stage matches invoice rows against the toll events returned by the SDK.

### Matching rules

1. Same vehicle
2. Same toll name
3. Time difference is less than or equal to `25 minutes`
4. Haversine distance is less than or equal to `20 km`

Both the time rule and the distance rule must pass.

### Reason

Timestamp alone is not enough to confirm that the truck crossed the same toll.
Two toll events can happen close together in time.

Distance alone is also not enough. A vehicle can be near a toll location at a
different time.

Using both checks reduces false matches.

---

## Time Matching

```text
abs(invoice.entry_time - sdk.timestamp) <= 25 minutes
```

---

## Distance Matching

```text
Haversine(
  gps.latitude,
  gps.longitude,
  sdk.latitude,
  sdk.longitude
) <= 20 km
```

---

## Stage 8 - Reconciliation

For every matched pair, the pipeline compares the expected toll amount with the
invoice amount.

```text
Expected Amount
↓
Invoice Amount
↓
Difference
↓
Classification
```

### Possible statuses

- `MATCHED`
- `AMOUNT_MISMATCH`
- `MISSING_INVOICE`
- `UNMATCHED_SDK_EVENT`
- `DUPLICATE_INVOICE`

---

## Stage 9 - MongoDB

The pipeline stores intermediate and final results in MongoDB collections.

### Collections

- `gps_raw`
- `invoice_raw`
- `gps_validated`
- `invoice_validated`
- `trips`
- `sdk_events`
- `reconciliation`
- `quality_reports`

---

## Handling Messy Data

### Missing Unit

GPS records without a `Unit` cannot be linked to a vehicle, so they are
rejected.

---

### Duplicate GPS

Duplicate GPS points are detected using this combination:

```text
(Unit, Timestamp, Latitude, Longitude)
```

Duplicates are removed before trip reconstruction.

---

### Missing Invoice

If the SDK detects a toll event but no matching invoice is found, the record is
classified as:

```text
MISSING_INVOICE
```

---

### Invoice Without SDK Event

If an invoice exists but no SDK toll event satisfies the time and distance
rules, the record is classified as:

```text
UNMATCHED_INVOICE
```
