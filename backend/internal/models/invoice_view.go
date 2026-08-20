package models

import "time"

// InvoiceRow backs the Invoices table (screenshot 7). It's a MERGE of
// mismatches (the reconciliation result) and invoice_raw (the original
// billed line's tag_no/toll_class/entry_plaza) — built via a $lookup in
// the repository, since these fields were never denormalized onto
// `mismatches` when the Python pipeline created it.
//
// bson tags are REQUIRED here (unlike models.Mismatch, which reads
// mismatches directly) because this struct decodes the output of a
// $project stage using explicit camelCase field names — without bson tags
// matching those exactly, decoding would depend on the driver's undocumented
// default name-mapping behavior instead of an explicit, obvious contract.
type InvoiceRow struct {
	TransactionID string   `bson:"transactionId" json:"transactionId"`
	Unit          string   `bson:"unit" json:"unit"`
	TollsPaid     float64  `bson:"tollsPaid" json:"tollsPaid"`
	Expected      *float64 `bson:"expected,omitempty" json:"expected,omitempty"`
	Overpaid      *float64 `bson:"overpaid,omitempty" json:"overpaid,omitempty"`
	// Verdict is the raw top-level outcome (matched | mismatch |
	// unassigned | duplicate). MatchType is a
	// display-friendly EFFECTIVE category — mismatch_type when
	// Verdict == "mismatch", otherwise Verdict itself — so the table can
	// show one consistent badge value regardless of which field the
	// pipeline actually populated.
	Verdict               string     `bson:"verdict" json:"verdict"`
	MatchType             string     `bson:"matchType" json:"matchType"`
	Status                string     `bson:"status" json:"status"`
	TripID                *string    `bson:"tripId,omitempty" json:"tripId,omitempty"`
	TagNo                 *string    `bson:"tagNo,omitempty" json:"tagNo,omitempty"`
	TollClass             *string    `bson:"tollClass,omitempty" json:"tollClass,omitempty"`
	EntryPlaza            *string    `bson:"entryPlaza,omitempty" json:"entryPlaza,omitempty"`
	EntryTime             time.Time  `bson:"entryTime" json:"entryTime"`
	PostDate              *time.Time `bson:"postDate,omitempty" json:"postDate,omitempty"`
	ReasonCode            *string    `bson:"reasonCode,omitempty" json:"reasonCode,omitempty"`
	InferredVehicleType   *string    `bson:"inferredVehicleType,omitempty" json:"inferredVehicleType,omitempty"`
	VehicleTypeConfidence *string    `bson:"vehicleTypeConfidence,omitempty" json:"vehicleTypeConfidence,omitempty"`
	IsDuplicate           bool       `bson:"isDuplicate" json:"isDuplicate"`
}

type InvoiceListResponse struct {
	Items []InvoiceRow `json:"items"`
	Total int64        `json:"total"`
	Page  int64        `json:"page"`
	Limit int64        `json:"limit"`
}