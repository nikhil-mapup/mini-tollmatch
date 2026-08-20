package models

import "time"

// Mismatch mirrors models/mismatch.py exactly — same field names, same
// collection. This is what guarantees API numbers match the reconciliation
// CSV: both read the same documents, shaped the same way.
//
// As of the pipeline's rewrite, the good outcome is signaled by
// Verdict == "matched", with MismatchType left nil — NOT by
// MismatchType == "matched". Verdict is the top-level outcome (matched |
// mismatch | unassigned | duplicate), and MismatchType only carries a
// value when Verdict == "mismatch" (misread | unmatched | max_toll).
//
// A fourth verdict, "insufficient_gps" (missing GPS coverage, not a
// proven absence signal), existed briefly and has since been folded back
// into mismatch_type "unmatched" by the pipeline — grouped with
// unmatched's other "couldn't verify against reference data" cases,
// not with misread's evidence-based ones. Removed here to match.
type Mismatch struct {
	TransactionID         string    `bson:"transaction_id" json:"transactionId"`
	Unit                  string    `bson:"unit" json:"unit"`
	TripID                *string   `bson:"trip_id,omitempty" json:"tripId,omitempty"`
	Verdict               string    `bson:"verdict" json:"verdict"`
	MismatchType          *string   `bson:"mismatch_type,omitempty" json:"mismatchType,omitempty"`
	ReasonCode            *string   `bson:"reason_code,omitempty" json:"reasonCode,omitempty"`
	BillingMethod         *string   `bson:"billing_method,omitempty" json:"billingMethod,omitempty"`
	ExpectedAmount        *float64  `bson:"expected_amount,omitempty" json:"expectedAmount,omitempty"`
	BilledAmount          float64   `bson:"billed_amount" json:"billedAmount"`
	DeltaAmount           *float64  `bson:"delta_amount,omitempty" json:"deltaAmount,omitempty"`
	MatchedTollPointName  *string   `bson:"matched_toll_point_name,omitempty" json:"matchedTollPointName,omitempty"`
	EntryTime             time.Time `bson:"entry_time" json:"entryTime"`
	TimeDeltaSeconds      *float64  `bson:"time_delta_seconds,omitempty" json:"timeDeltaSeconds,omitempty"`
	GPSDistanceKm         *float64  `bson:"gps_distance_km,omitempty" json:"gpsDistanceKm,omitempty"`
	InferredVehicleType   *string   `bson:"inferred_vehicle_type,omitempty" json:"inferredVehicleType,omitempty"`
	VehicleTypeConfidence *string   `bson:"vehicle_type_confidence,omitempty" json:"vehicleTypeConfidence,omitempty"`
	IsDuplicate           bool      `bson:"is_duplicate" json:"isDuplicate"`
	Status                string    `bson:"status" json:"status"`
	DetectedAt            time.Time `bson:"detected_at" json:"detectedAt"`
}

// isConfirmedProblem is the one place "counts as a real, evidence-backed
// mismatch" is defined — reused everywhere the binary match/mismatch split
// is computed, so it can't drift between endpoints.
//
// Deliberately NOT included: "unassigned". It's a "we don't have enough
// evidence either way" outcome, not a proven overcharge — folding it into
// "mismatch" would inflate the mismatch rate with an unconfirmed case,
// which is exactly the thing this whole project has tried never to do.
// It's tracked separately (see UnconfirmedCount/UnconfirmedAmount on the
// response types below) instead of being silently absorbed into either
// bucket.
//
// "insufficient_gps" was a second such verdict and has since been folded
// into mismatch_type "unmatched" by the pipeline (a real, evidence-backed
// "couldn't verify against reference data" case, not an unconfirmed one)
// — no longer excluded here, since it's no longer a distinct verdict.
var ConfirmedProblemVerdicts = []string{"mismatch", "duplicate"}
var UnconfirmedVerdicts = []string{"unassigned"}

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
	// Invoices with verdict "unassigned" — genuinely
	// unresolved, not counted in MismatchCount since they aren't proven
	// problems. Tracked here rather than silently dropped.
	UnconfirmedCount int64  `json:"unconfirmedCount"`
	TopType          string `json:"topType"`
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