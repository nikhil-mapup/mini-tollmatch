# Mini TollMatch
Mini TollMatch is a toll reconciliation prototype. It reads fleet GPS and toll
invoice files, reconstructs physical trips, sends trip GPS traces to the
TollMatch/TollGuru API, compares expected tolls with invoice rows, stores the
results in MongoDB, and exposes a small dashboard for review.

For the detailed pipeline logic, see
[DATA_PIPELINE_LOGIC.md](DATA_PIPELINE_LOGIC.md).

## What is Currently Implemented

### Data Pipeline

- Reads GPS data from `data/Fleet_A_gps.parquet`
- Reads invoice data from `data/FleetA_invoices.csv`
- Parses GPS timestamps like `2025-10-12T17:53:37.000000Z` as UTC datetimes
- Filters GPS and invoices by selected units and date range
- Validates GPS records and saves a quality report
- Splits GPS tracks into route segments using GPS gaps
- Records GPS gap events
- Stitches route segments into physical trips
- Exports each physical trip as a CSV for the API
- Sends the CSV as raw `text/csv` request body to the TollMatch/TollGuru API
- Prints the CSV path, CSV preview, API status, and API response body
- Parses API toll points into `SDKResult`
- Saves SDK results in MongoDB
- Correlates GPS gaps against known toll locations
- Saves invoice rows with duplicate handling
- Reconciles invoice rows against detected toll points
- Saves mismatch records in MongoDB
- Writes final reconciliation output to `output/reconciliation.csv`

### Backend API

- Go API built with Gin
- MongoDB-backed repositories and service layer
- Health check at `GET /healthz`
- Dashboard endpoints under `/api`
- CORS configured through `ALLOWED_ORIGIN`

Key endpoints:

- `GET /api/summary`
- `GET /api/mismatches`
- `GET /api/units`
- `GET /api/mismatch-types`
- `GET /api/trips`
- `GET /api/overview`
- `GET /api/cost-overview`
- `GET /api/cost-overview/by-cost-center`
- `GET /api/invoice-overview`
- `GET /api/mismatch-breakdown`
- `GET /api/top-units`
- `GET /api/invoices`

### Frontend Dashboard

- Next.js dashboard for reviewing reconciliation results
- Overview metrics, cost overview, invoice overview, mismatch breakdown, top
  mismatch units, and invoice table views
- Filter support for unit, mismatch type, date range, sorting, pagination, and
  invoice search
- API URL configured server-side through `API_URL`

## Outputs

MongoDB collections currently used:

- `route_segments`
- `gps_gap_events`
- `physical_trips`
- `trip_points`
- `quality_reports`
- `sdk_results`
- `invoice_raw`
- `mismatches`

Local files currently produced:

- `output/tollguru/<trip_id>.csv`
- `output/reconciliation.csv`

## Code Navigation

```text
.
├── architecture/
│   └── HLD.png                         # High-level design diagram
├── data/
│   ├── Fleet_A_gps.parquet             # Source GPS data
│   └── FleetA_invoices.csv             # Source toll invoice data
├── backend/
│   ├── cmd/api/main.go                 # Go API entrypoint
│   └── internal/
│       ├── config/                     # Env-driven API configuration
│       ├── db/                         # MongoDB connection and collection names
│       ├── handler/                    # Gin HTTP handlers
│       ├── middleware/                 # Logging and CORS middleware
│       ├── models/                     # API response models
│       ├── repository/                 # MongoDB query layer
│       ├── router/                     # API route definitions
│       └── service/                    # API business logic
├── frontend/
│   ├── app/                            # Next.js app routes
│   ├── components/                     # Dashboard UI components
│   ├── lib/api.ts                      # Server-side API client
│   └── types.ts                        # Shared frontend types
├── pipeline/
│   ├── main.py                         # Pipeline entrypoint
│   ├── config/
│   │   ├── config.py                   # Paths, env vars, filters, thresholds
│   │   └── constants.py                # MongoDB collection constants
│   ├── readers/
│   │   ├── gps_reader.py               # Reads GPS parquet
│   │   └── invoice_reader.py           # Reads invoice CSV
│   ├── models/
│   │   ├── gps.py                      # GPS schema
│   │   ├── invoice.py                  # Invoice schema
│   │   ├── route_segment.py            # Route segment schema
│   │   ├── gps_gap.py                  # GPS gap schema
│   │   ├── trip.py                     # Physical trip schema
│   │   ├── sdk_result.py               # Parsed API result schema
│   │   ├── mismatch.py                 # Reconciliation row schema
│   │   └── quality_report.py           # Validation report schema
│   ├── validators/
│   │   └── gps_validator.py            # GPS validation rules
│   ├── processors/
│   │   ├── gps_filter.py               # Unit filtering
│   │   ├── date_range_filter.py        # Shared GPS/invoice date filtering
│   │   ├── group_by_unit.py            # Groups GPS by vehicle
│   │   ├── route_segmenter.py          # Creates route segments
│   │   └── route_stitcher.py           # Builds physical trips
│   ├── services/
│   │   ├── route_trip_service.py       # Route/trip processing
│   │   ├── toll_service.py             # CSV export + API call + SDK save
│   │   ├── toll_location_index.py      # Indexes detected toll points
│   │   ├── gap_toll_correlator.py      # Flags gaps near tolls
│   │   └── reconciliation_service.py   # Invoice comparison
│   ├── tollmatch/
│   │   ├── csv_exporter.py             # Writes trip GPS CSV files
│   │   ├── client.py                   # Calls the TollMatch/TollGuru API
│   │   ├── parser.py                   # Parses raw API response
│   │   └── reconciliation_csv_exporter.py
│   ├── database/
│   │   ├── mongo.py
│   │   ├── route_repository.py
│   │   ├── gps_gap_repository.py
│   │   ├── trip_repository.py
│   │   ├── trip_point_repository.py
│   │   ├── sdk_result_repository.py
│   │   ├── invoice_repository.py
│   │   ├── mismatch_repository.py
│   │   └── quality_report_repository.py
│   └── utils/
│       ├── geo.py
│       └── text.py
├── DATA_PIPELINE_LOGIC.md
├── requirements.txt
├── readme.md
└── .env                                # Local secrets/config, not committed
```

## Current Pipeline Flow

The pipeline starts in `pipeline/main.py`.

1. Create a run ID.
2. Connect to MongoDB.
3. Read GPS records.
4. Filter GPS records by unit and date range.
5. Validate GPS records.
6. Save GPS validation quality report.
7. Build route segments, GPS gap events, physical trips, and trip points.
8. Export each trip to a CSV under `output/tollguru/`.
9. Send each CSV to the TollMatch/TollGuru API.
10. Print the CSV preview and raw API response.
11. Parse and save SDK results.
12. Correlate GPS gaps with detected toll locations.
13. Read, filter, and save invoice rows.
14. Reconcile invoice rows against detected toll points.
15. Save mismatches and write `output/reconciliation.csv`.

## API CSV Upload Note

The API expects the CSV itself as the raw request body with:

```text
Content-Type: text/csv
```

The request should not be sent as `multipart/form-data`. When the CSV was sent
as multipart, the API returned:

```text
Invalid CSV file: Headers 'latitude', 'longitude', 'timestamp' must be present
```

The CSV generated for a trip starts like this:

```csv
latitude,longitude,timestamp,units
27.6327209,-99.5327911,2025-10-08T00:12:21Z,1027
```

The client now sends this file content directly and prints the API status and
response body.

## HLD

![Mini TollMatch High Level Design](architecture/HLD.png)

## Run Locally

### 1. Install Pipeline Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Configure Pipeline Environment

Create a `.env` file in the project root:

```env
MONGO_URI=your_mongodb_connection_string
DATABASE_NAME=tollmatch
TOLLMATCH_API_URL=your_api_base_url
TOLLMATCH_API_KEY=your_api_key
```

### 3. Run the Pipeline

From the project root:

```bash
python3 pipeline/main.py
```

### 4. Run the Backend API

From the backend directory:

```bash
cd backend
go run ./cmd/api
```

Backend environment variables:

```env
MONGO_URI=your_mongodb_connection_string
MONGO_DB=tollmatch
PORT=8080
ALLOWED_ORIGIN=http://localhost:3000
```

### 5. Run the Frontend

From the frontend directory:

```bash
cd frontend
npm install
npm run dev
```

Frontend environment variable:

```env
API_URL=http://localhost:8080
```

The dashboard runs at `http://localhost:3000` by default.

## Production Gap

This project is currently a working prototype, not a production-ready toll
reconciliation system. The most important production gap is vehicle-class
accuracy: the pipeline currently uses a placeholder TollGuru vehicle type for
SDK calls because there is no confirmed mapping from invoice `toll_class`
values to TollGuru vehicle type enums, and there is no vehicle master-data
lookup by unit. Any expected toll amount that depends on vehicle class should
therefore be treated as provisional.

Other known production gaps:

- GPS gap and route-stitching thresholds are configured as placeholders and
  still need percentile-backed validation on real fleet movement data.
- The pipeline is batch-oriented and local-file driven; production would need
  scheduled or event-driven ingestion, idempotent reruns, and operational
  observability.
- Error handling, retry policy, API rate-limit handling, and partial-run
  recovery are minimal.
- The dashboard has no authentication, authorization, audit logging, or
  deployment hardening.
