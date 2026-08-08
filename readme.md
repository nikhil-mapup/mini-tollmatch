# Mini TollMatch

The current implementation reads local GPS and
invoice files, filters GPS records for a selected time window and selected
vehicles, validates GPS records, builds route segments, stitches those segments
into physical trips, and stores the output in MongoDB.

For the higher-level pipeline plan, see
[DATA_PIPELINE_LOGIC.md](DATA_PIPELINE_LOGIC.md).

## What is Currently Implemented

- Reads GPS data from `data/Fleet_A_gps.parquet`
- Reads invoice data from `data/FleetA_invoices.csv`
- Converts rows into typed Pydantic models
- Parses GPS timestamps like `2025-10-12T17:53:37.000000Z` as UTC datetimes
- Filters GPS records by selected units and a configured UTC time window
- Validates GPS records for coordinate, unit, timestamp, and duplicate issues
- Splits GPS pings into route segments using a `30` minute gap threshold
- Records GPS gap events when a route split happens
- Stitches nearby route segments into physical trips
- Stores route segments, GPS gaps, physical trips, and trip points in MongoDB

The current run writes output to these MongoDB collections:

- `route_segments`
- `gps_gap_events`
- `physical_trips`
- `trip_points`

## Code Navigation

```text
.
├── architecture/
│   └── HLD.png                         # High-level design diagram
├── data/
│   ├── Fleet_A_gps.parquet             # Source GPS data
│   └── FleetA_invoices.csv             # Source toll invoice data
├── pipeline/
│   ├── main.py                         # Pipeline entrypoint
│   ├── config/
│   │   ├── config.py                   # File paths, env vars, filters, thresholds
│   │   └── constants.py                # MongoDB collection name constants
│   ├── readers/
│   │   ├── gps_reader.py               # Reads GPS parquet into GPSRecord models
│   │   └── invoice_reader.py           # Reads invoice CSV into InvoiceRecord models
│   ├── models/
│   │   ├── gps.py                      # GPS Pydantic schema
│   │   ├── invoice.py                  # Invoice Pydantic schema
│   │   ├── route_segment.py            # Route segment schema
│   │   ├── gps_gap.py                  # GPS gap event schema
│   │   ├── trip.py                     # Physical trip schema
│   │   └── validation.py               # Validation result models
│   ├── validators/
│   │   └── gps_validator.py            # GPS validation rules
│   ├── processors/
│   │   ├── gps_filter.py               # Filters GPS by unit and time window
│   │   ├── group_by_unit.py            # Groups GPS records by vehicle/unit
│   │   ├── route_segmenter.py          # Splits GPS into route segments
│   │   └── route_stitcher.py           # Stitches route segments into trips
│   ├── services/
│   │   └── route_trip_service.py       # Coordinates route and trip processing
│   ├── utils/
│   │   └── geo.py                      # Geospatial helper functions
│   └── database/
│       ├── mongo.py                    # MongoDB client wrapper
│       ├── route_repository.py         # Saves route segment documents
│       ├── gps_gap_repository.py       # Saves GPS gap events
│       ├── trip_repository.py          # Saves physical trip documents
│       └── trip_point_repository.py    # Saves trip GPS point documents
├── DATA_PIPELINE_LOGIC.md              # Detailed pipeline logic and future stages
├── requirements.txt                    # Python dependencies
├── readme.md                           # Project setup and navigation
└── .env                                # Local environment config, not committed
```

## Current Pipeline Flow

The pipeline starts in `pipeline/main.py`.

Current flow:

1. Read all GPS records from `Fleet_A_gps.parquet`.
2. Filter GPS records by `SELECTED_UNITS`, `WINDOW_START`, and `WINDOW_END`.
3. Validate the filtered GPS records using `GPSValidator`.
4. Read invoice records from `FleetA_invoices.csv`.
5. Connect to MongoDB.
6. Group valid GPS records by `unit`.
7. Split each unit's GPS records into route segments.
8. Save route split gaps into `gps_gap_events`.
9. Save route segment summaries into `route_segments`.
10. Stitch route segments into physical trips.
11. Save physical trip summaries into `physical_trips`.
12. Save trip GPS points into `trip_points`.

## HLD

![Mini TollMatch High Level Design](architecture/HLD.png)

## Run Locally

### 1. Install Dependencies

You can install dependencies directly:

```bash
pip3 install -r requirements.txt
```

### 2. Configure MongoDB

Create a `.env` file in the project root:

```env
MONGO_URI=your_mongodb_connection_string
DATABASE_NAME=tollmatch
```

`DATABASE_NAME` is optional. If it is not set, the code defaults to
`tollmatch`.

### 3. Run the Pipeline

From the project root:

```bash
python3 pipeline/main.py
```

## Notes

The GPS file is large, so reading, filtering, and route processing can take
time.