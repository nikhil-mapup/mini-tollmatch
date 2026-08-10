package models

// Screenshot 1 — top summary strip.
type OverviewResponse struct {
	Vehicles      int64   `json:"vehicles"`
	TollsPaid     float64 `json:"tollsPaid"`
	TollsExpected float64 `json:"tollsExpected"`
	TollsOverpaid float64 `json:"tollsOverpaid"`
	OverpaidPct   float64 `json:"overpaidPct"`
	// No refund/dispute workflow exists anywhere in this pipeline's data —
	// always 0, not faked. See handler comment for why this stays hardcoded
	// rather than silently omitted.
	TollsRefunded float64 `json:"tollsRefunded"`
}

// Screenshot 2 — "Cost Overview" card.
type CostOverviewResponse struct {
	MatchAmount    float64 `json:"matchAmount"`
	MatchPct       float64 `json:"matchPct"`
	MismatchAmount float64 `json:"mismatchAmount"`
	MismatchPct    float64 `json:"mismatchPct"`
	TotalUnits     int64   `json:"totalUnits"`
	PaidTolls      float64 `json:"paidTolls"`
}

// Screenshot 3 — "Cost Overview by Cost Center" — the header matches figures
// plus a per-cost-center breakdown table, requiring a join against
// invoice_raw since `cost_center` isn't stored on `mismatches`.
type CostCenterRow struct {
	CostCenter     string  `bson:"_id" json:"costCenter"`
	TotalTxns      int64   `bson:"totalTxns" json:"totalTxns"`
	Units          int64   `bson:"units" json:"units"`
	TotalTollsPaid float64 `bson:"totalTollsPaid" json:"totalTollsPaid"`
	TollsOverpaid  float64 `bson:"tollsOverpaid" json:"tollsOverpaid"`
}

type CostOverviewByCostCenterResponse struct {
	MatchAmount    float64         `json:"matchAmount"`
	MatchPct       float64         `json:"matchPct"`
	MismatchAmount float64         `json:"mismatchAmount"`
	MismatchPct    float64         `json:"mismatchPct"`
	Rows           []CostCenterRow `json:"rows"`
	TotalUnits     int64           `json:"totalUnits"`
	PaidTolls      float64         `json:"paidTolls"`
}

// Screenshot 4 — "Invoice Overview" — counts, not dollar amounts.
type InvoiceOverviewResponse struct {
	MatchCount    int64   `json:"matchCount"`
	MatchPct      float64 `json:"matchPct"`
	MismatchCount int64   `json:"mismatchCount"`
	MismatchPct   float64 `json:"mismatchPct"`
	TotalInvoices int64   `json:"totalInvoices"`
}

// Screenshot 5 — relabeled "by Mismatch Type" since no invoice-status
// lifecycle (Disputed/Refunded/Denied/etc) exists in this data.
type MismatchBreakdownItem struct {
	Type  string `bson:"_id" json:"type"`
	Count int64  `bson:"count" json:"count"`
}

// Screenshot 6 — "Top Units by Mismatch".
type TopUnitRow struct {
	Unit          string  `bson:"_id" json:"unit"`
	TollsPaid     float64 `bson:"tollsPaid" json:"tollsPaid"`
	TollsMismatch float64 `bson:"tollsMismatch" json:"tollsMismatch"`
}
