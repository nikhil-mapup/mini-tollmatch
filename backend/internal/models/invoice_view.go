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
	TransactionID string    `bson:"transactionId" json:"transactionId"`
	Unit          string    `bson:"unit" json:"unit"`
	TollsPaid     float64   `bson:"tollsPaid" json:"tollsPaid"`
	Expected      *float64  `bson:"expected,omitempty" json:"expected,omitempty"`
	Overpaid      *float64  `bson:"overpaid,omitempty" json:"overpaid,omitempty"`
	MatchType     string    `bson:"matchType" json:"matchType"` // the raw mismatch_type value
	Status        string    `bson:"status" json:"status"`       // open | reconciled — our real status field, not a full lifecycle
	TripID        *string   `bson:"tripId,omitempty" json:"tripId,omitempty"`
	TagNo         *string   `bson:"tagNo,omitempty" json:"tagNo,omitempty"`
	TollClass     *string   `bson:"tollClass,omitempty" json:"tollClass,omitempty"`
	EntryPlaza    *string   `bson:"entryPlaza,omitempty" json:"entryPlaza,omitempty"`
	EntryTime     time.Time `bson:"entryTime" json:"entryTime"`
}

type InvoiceListResponse struct {
	Items []InvoiceRow `json:"items"`
	Total int64        `json:"total"`
	Page  int64        `json:"page"`
	Limit int64        `json:"limit"`
}
