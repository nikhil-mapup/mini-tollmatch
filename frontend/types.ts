// Mirrors the JSON tags in tollmatch-backend/internal/models/mismatch.go
// exactly. If a field is added or renamed on the Go side, this is the one
// file to update on the frontend — nowhere else should redefine this shape.

export interface Mismatch {
  transactionId: string;
  unit: string;
  tripId?: string;
  mismatchType: string;
  billingMethod?: string;
  expectedAmount?: number;
  billedAmount: number;
  deltaAmount?: number;
  matchedTollPointName?: string;
  entryTime: string;
  status: string;
  detectedAt: string;
}

export interface SummaryResponse {
  totalTollSpend: number;
  mismatchCount: number;
  mismatchAmount: number;
  topType: string;
}

export interface MismatchListResponse {
  items: Mismatch[];
  total: number;
  page: number;
  limit: number;
}

export interface TypeCount {
  type: string;
  count: number;
}

export interface Trip {
  tripId: string;
  unit: string;
  fleetId: string;
  startTime: string;
  endTime: string;
  routeIds: string[];
  gpsPointCount: number;
  mismatchCount: number;
  mismatchTypes: string[];
}

// Screenshot 1
export interface OverviewResponse {
  vehicles: number;
  tollsPaid: number;
  tollsExpected: number;
  tollsOverpaid: number;
  overpaidPct: number;
  tollsRefunded: number; // always 0 — no refund/dispute data exists in this pipeline
}

// Screenshot 2
export interface CostOverviewResponse {
  matchAmount: number;
  matchPct: number;
  mismatchAmount: number;
  mismatchPct: number;
  totalUnits: number;
  paidTolls: number;
}

// Screenshot 3
export interface CostCenterRow {
  costCenter: string;
  totalTxns: number;
  units: number;
  totalTollsPaid: number;
  tollsOverpaid: number;
}

export interface CostOverviewByCostCenterResponse {
  matchAmount: number;
  matchPct: number;
  mismatchAmount: number;
  mismatchPct: number;
  rows: CostCenterRow[];
  totalUnits: number;
  paidTolls: number;
}

// Screenshot 4
export interface InvoiceOverviewResponse {
  matchCount: number;
  matchPct: number;
  mismatchCount: number;
  mismatchPct: number;
  totalInvoices: number;
}

// Screenshot 5 — relabeled "by Mismatch Type" on the frontend too, since
// there's no invoice-status lifecycle in this data.
export interface MismatchBreakdownItem {
  type: string;
  count: number;
}

// Screenshot 6
export interface TopUnitRow {
  unit: string;
  tollsPaid: number;
  tollsMismatch: number;
}

// Screenshot 7
export interface InvoiceRow {
  transactionId: string;
  unit: string;
  tollsPaid: number;
  expected?: number;
  overpaid?: number;
  matchType: string;
  status: string;
  tripId?: string;
  tagNo?: string;
  tollClass?: string;
  entryPlaza?: string;
  entryTime: string;
}

export interface InvoiceListResponse {
  items: InvoiceRow[];
  total: number;
  page: number;
  limit: number;
}

// The filter shape shared by every fetch call and by FilterBar — one
// definition, so a new filter field only needs to be added once. tab/search
// are optional and only meaningful on the invoices page, but including them
// here means withFilters() preserves them automatically on any navigation
// (e.g. changing the date range) instead of silently dropping them.
export interface Filters {
  unit?: string;
  type?: string;
  start?: string;
  end?: string;
  sort?: string;
  order?: string;
  page?: string;
  tab?: string;
  search?: string;
}
