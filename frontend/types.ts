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

// The filter shape shared by every fetch call and by FilterBar — one
// definition, so a new filter field only needs to be added once.
export interface Filters {
  unit?: string;
  type?: string;
  start?: string;
  end?: string;
  sort?: string;
  order?: string;
  page?: string;
}
