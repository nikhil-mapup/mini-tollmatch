package models

import "time"

// Mismatch mirrors models/mismatch.py exactly — same field names, same
// collection. This is what guarantees API numbers match the reconciliation
// CSV: both read the same documents, shaped the same way.
type Mismatch struct {
	TransactionID        string    `bson:"transaction_id" json:"transactionId"`
	Unit                 string    `bson:"unit" json:"unit"`
	TripID               *string   `bson:"trip_id,omitempty" json:"tripId,omitempty"`
	MismatchType         string    `bson:"mismatch_type" json:"mismatchType"`
	BillingMethod        *string   `bson:"billing_method,omitempty" json:"billingMethod,omitempty"`
	ExpectedAmount       *float64  `bson:"expected_amount,omitempty" json:"expectedAmount,omitempty"`
	BilledAmount         float64   `bson:"billed_amount" json:"billedAmount"`
	DeltaAmount          *float64  `bson:"delta_amount,omitempty" json:"deltaAmount,omitempty"`
	MatchedTollPointName *string   `bson:"matched_toll_point_name,omitempty" json:"matchedTollPointName,omitempty"`
	EntryTime            time.Time `bson:"entry_time" json:"entryTime"`
	Status               string    `bson:"status" json:"status"`
	DetectedAt           time.Time `bson:"detected_at" json:"detectedAt"`
}

// Filters is built once per request from query params and passed down
// through service -> repository unchanged. Every handler that accepts
// unit/date filtering uses this same struct — one shape, not four
// slightly-different ones per endpoint.
//
// TransactionID and Type (mismatch type) live directly on `mismatches`,
// so they're safe to apply generically (see buildFilter in
// mismatch_repository.go) — Type already existed and already does exact
// match-type filtering; it just was never exposed on the invoices page UI.
// TagNo only exists on invoice_raw and requires the $lookup that only
// InvoiceViewRepository performs — it's deliberately NOT applied in the
// shared buildFilter(), only inside that repository, after the join.
//
// Start/End are deliberately reinterpreted per endpoint rather than always
// meaning "entry_time": the dashboard's cards filter by entry_time (via
// buildFilter, unchanged), but InvoiceViewRepository strips that and
// re-applies Start/End against invoice.post_date instead, post-lookup —
// post date is what actually matters for reviewing invoices, not the GPS
// entry timestamp. A single-day PostDate field was removed entirely once
// this range covers the same need without a second, redundant control.
type Filters struct {
	Unit          string
	Type          string
	Start         *time.Time
	End           *time.Time
	TransactionID string
	TagNo         string
}

type SummaryResponse struct {
	TotalTollSpend float64 `json:"totalTollSpend"`
	MismatchCount  int64   `json:"mismatchCount"`
	MismatchAmount float64 `json:"mismatchAmount"`
	TopType        string  `json:"topType"`
}

type MismatchListResponse struct {
	Items []Mismatch `json:"items"`
	Total int64      `json:"total"`
	Page  int64      `json:"page"`
	Limit int64      `json:"limit"`
}

type TypeCount struct {
	Type  string `bson:"_id" json:"type"`
	Count int64  `bson:"count" json:"count"`
}