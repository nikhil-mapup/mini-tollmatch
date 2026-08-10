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
type Filters struct {
	Unit  string
	Type  string
	Start *time.Time
	End   *time.Time
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
