# Mini TollMatch

Mini TollMatch is a toll reconciliation prototype. It reads fleet GPS and toll
invoice files, reconstructs vehicle trips, sends each trip trace to the
TollMatch/TollGuru GPS Tracks API, compares expected toll events with invoice
transactions, stores the results in MongoDB, and exposes a Next.js dashboard
through a Go API.

For the detailed pipeline rules, see
[DATA_PIPELINE_LOGIC.md](DATA_PIPELINE_LOGIC.md).

## What Is Implemented

### Data Pipeline

- Reads GPS data from `data/Fleet_A_gps.parquet`.
- Reads invoice data from `data/FleetA_invoices.csv`.
- Loads local pipeline settings from `.env` with `python-dotenv`.
- Filters GPS and invoice records by `SELECTED_UNITS`, `WINDOW_START`, and
  `WINDOW_END` from `pipeline/config/config.py`.
- Validates GPS latitude, longitude, null-island coordinates, unit, future
  timestamps, and exact duplicates.
- Saves GPS validation quality reports to MongoDB.
- Groups GPS records by unit.
- Splits routes using two boundary signals:
  - telemetry gaps longer than `GPS_GAP_THRESHOLD_MINUTES`;
  - stationary dwell periods within `DWELL_RADIUS_KM` for at least
    `DWELL_THRESHOLD_MINUTES`.
- Saves route segments and GPS gap events.
- Stitches nearby route segments into physical trips.
- Exports one CSV per physical trip under `output/tollguru/`.
- Sends each CSV as the raw `text/csv` request body to the TollMatch/TollGuru
  API.
- Parses API toll points into `SDKResult` records.
- Saves SDK results in MongoDB.
- Builds an in-memory toll-location index by unit and normalized toll name.
- Correlates GPS gaps against detected toll locations.
- Saves invoice rows with duplicate rejection on `transaction_id`.
- Reconciles invoices against expected toll points using both time and distance.
- Saves mismatch records in MongoDB.
- Writes final reconciliation output to `output/reconciliation.csv`.

### Backend API

- Go API built with Gin.
- MongoDB-backed repository and service layers.
- Health check at `GET /healthz`.
- Dashboard endpoints under `/api`.
- CORS configured through `ALLOWED_ORIGIN`.

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

- Next.js dashboard for reviewing reconciliation results.
- Overview metrics, cost overview, invoice overview, mismatch breakdown, top
  mismatch units, unit pages, and invoice table views.
- Filter support for unit, mismatch type, date range, sorting, pagination, tab
  selection, and invoice search.
- Server-side API URL configured through `API_URL`.

## Repository Layout

```text
.
|-- architecture/
|   `-- HLD.png
|-- data/
|   |-- Fleet_A_gps.parquet
|   `-- FleetA_invoices.csv
|-- backend/
|   |-- cmd/api/main.go
|   |-- internal/config/
|   |-- internal/db/
|   |-- internal/handler/
|   |-- internal/middleware/
|   |-- internal/models/
|   |-- internal/repository/
|   |-- internal/router/
|   `-- internal/service/
|-- frontend/
|   |-- app/
|   |-- components/
|   |-- lib/
|   `-- types.ts
|-- pipeline/
|   |-- main.py
|   |-- config/
|   |-- readers/
|   |-- validators/
|   |-- processors/
|   |-- services/
|   |-- tollmatch/
|   |-- database/
|   `-- models/
|-- DATA_PIPELINE_LOGIC.md
|-- requirements.txt
`-- readme.md
```

## MongoDB Collections

The pipeline and backend currently use these collections:

- `route_segments`
- `gps_gap_events`
- `physical_trips`
- `quality_reports`
- `sdk_results`
- `invoice_raw`
- `mismatches`

## Local Outputs

The pipeline writes generated files locally:

- `output/tollguru/<trip_id>.csv`
- `output/reconciliation.csv`

These are runtime artifacts and should not be committed.

## Environment Variables

Keep secrets and machine-specific settings in environment files or exported
shell variables, not in application code.

### Root `.env` for the Python Pipeline

Create `.env` in the project root:

```env
MONGO_URI=mongodb+srv://USER:PASSWORD@HOST/DATABASE?retryWrites=true&w=majority
DATABASE_NAME=tollmatch
TOLLMATCH_API_URL=https://example-toll-api-host
TOLLMATCH_API_KEY=replace_with_real_api_key
```

### Backend Environment

The Go backend reads OS environment variables directly. It does not load
`backend/.env` by itself, so export these values in your shell or source an env
file before starting the server:

```env
MONGO_URI=mongodb+srv://USER:PASSWORD@HOST/DATABASE?retryWrites=true&w=majority
MONGO_DB=tollmatch
PORT=8080
ALLOWED_ORIGIN=http://localhost:3000
```

### Frontend Environment

The Next.js app reads `API_URL` on the server side. Put this in
`frontend/.env.local` or export it before running `npm run dev`:

```env
API_URL=http://localhost:8080
```

`API_URL` intentionally does not use the `NEXT_PUBLIC_` prefix because it is
used only by server components and should not be exposed to browser code.

## Run Locally

### 1. Install Pipeline Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Run the Pipeline

From the project root:

```bash
python3 pipeline/main.py
```

### 3. Run the Backend API

From the backend directory, with backend environment variables already loaded:

```bash
cd backend
go run ./cmd/api
```

The backend listens on `http://localhost:8080` by default.

### 4. Run the Frontend

From the frontend directory:

```bash
cd frontend
npm install
npm run dev
```

The dashboard runs at `http://localhost:3000` by default.

## API CSV Upload Note

The TollMatch/TollGuru endpoint expects the CSV itself as the raw request body:

```text
Content-Type: text/csv
```

The request should not be sent as `multipart/form-data`. The generated CSV
starts like this:

```csv
latitude,longitude,timestamp,units
27.6327209,-99.5327911,2025-10-08T00:12:21Z,1027
```

## HLD

![Mini TollMatch High Level Design](architecture/HLD.png)


