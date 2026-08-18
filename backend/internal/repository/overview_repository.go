package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"

	"tollmatch-backend/internal/models"
)

// OverviewRepository powers the dashboard's summary components (screenshots
// 1, 2, 3, 4, 6). It reads from `mismatches` for everything except the
// cost-center breakdown, which needs a $lookup into `invoice_raw` since
// cost_center isn't stored on the mismatch document itself.
type OverviewRepository struct {
	mismatches *mongo.Collection
	invoices   *mongo.Collection // invoice_raw — only used for the cost-center join
}

func NewOverviewRepository(mismatches, invoices *mongo.Collection) *OverviewRepository {
	return &OverviewRepository{mismatches: mismatches, invoices: invoices}
}

// isMismatchCond is the one place "match vs mismatch" is defined as a Mongo
// expression — every aggregation below that needs this split reuses it, so
// the definition can never drift between endpoints.
var isMismatchCond = bson.M{"$ne": bson.A{"$mismatch_type", "matched"}}

var positiveDeltaCond = bson.M{
	"$cond": bson.A{bson.M{"$gt": bson.A{"$delta_amount", 0}}, "$delta_amount", 0},
}

// GetOverview powers screenshot 1: Vehicles | Tolls Paid | Tolls Expected |
// Tolls Overpaid | Tolls Refunded.
func (r *OverviewRepository) GetOverview(ctx context.Context, f models.Filters) (models.OverviewResponse, error) {
	filter := buildFilter(f)

	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$group", Value: bson.M{
			"_id":           nil,
			"units":         bson.M{"$addToSet": "$unit"},
			"tollsPaid":     bson.M{"$sum": "$billed_amount"},
			"tollsExpected": bson.M{"$sum": "$expected_amount"},
			"tollsOverpaid": bson.M{"$sum": positiveDeltaCond},
		}}},
	}

	cursor, err := r.mismatches.Aggregate(ctx, pipeline)
	if err != nil {
		return models.OverviewResponse{}, err
	}
	defer cursor.Close(ctx)

	var results []struct {
		Units         []string `bson:"units"`
		TollsPaid     float64  `bson:"tollsPaid"`
		TollsExpected float64  `bson:"tollsExpected"`
		TollsOverpaid float64  `bson:"tollsOverpaid"`
	}
	if err := cursor.All(ctx, &results); err != nil {
		return models.OverviewResponse{}, err
	}

	resp := models.OverviewResponse{}
	if len(results) > 0 {
		resp.Vehicles = int64(len(results[0].Units))
		resp.TollsPaid = results[0].TollsPaid
		resp.TollsExpected = results[0].TollsExpected
		resp.TollsOverpaid = results[0].TollsOverpaid
		if resp.TollsPaid > 0 {
			resp.OverpaidPct = (resp.TollsOverpaid / resp.TollsPaid) * 100
		}
	}
	// No refund/dispute workflow exists in this pipeline's data at all —
	// always 0. Not a placeholder we forgot to fill in; there is nothing
	// to compute here yet.
	resp.TollsRefunded = 0

	return resp, nil
}

// matchMismatchAmounts is shared by GetCostOverview and
// GetCostOverviewByCostCenter — both need the identical header figures.
func (r *OverviewRepository) matchMismatchAmounts(ctx context.Context, filter bson.M) (matchAmt, mismatchAmt float64, err error) {
	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$group", Value: bson.M{
			"_id":            "$mismatch_type",
			"amount":         bson.M{"$sum": "$billed_amount"},
			"isMismatchType": bson.M{"$first": isMismatchCond},
		}}},
	}

	cursor, aggErr := r.mismatches.Aggregate(ctx, pipeline)
	if aggErr != nil {
		return 0, 0, aggErr
	}
	defer cursor.Close(ctx)

	var rows []struct {
		ID     string  `bson:"_id"`
		Amount float64 `bson:"amount"`
	}
	if decErr := cursor.All(ctx, &rows); decErr != nil {
		return 0, 0, decErr
	}

	for _, row := range rows {
		if row.ID == "matched" {
			matchAmt += row.Amount
		} else {
			mismatchAmt += row.Amount
		}
	}
	return matchAmt, mismatchAmt, nil
}

func (r *OverviewRepository) totalUnitsAndPaidTolls(ctx context.Context, filter bson.M) (int64, float64, error) {
	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$group", Value: bson.M{
			"_id":       nil,
			"units":     bson.M{"$addToSet": "$unit"},
			"paidTolls": bson.M{"$sum": "$billed_amount"},
		}}},
	}

	cursor, err := r.mismatches.Aggregate(ctx, pipeline)
	if err != nil {
		return 0, 0, err
	}
	defer cursor.Close(ctx)

	var results []struct {
		Units     []string `bson:"units"`
		PaidTolls float64  `bson:"paidTolls"`
	}
	if err := cursor.All(ctx, &results); err != nil {
		return 0, 0, err
	}
	if len(results) == 0 {
		return 0, 0, nil
	}
	return int64(len(results[0].Units)), results[0].PaidTolls, nil
}

// GetCostOverview powers screenshot 2. Match $ / Mismatch $ are portions of
// total paid tolls (they sum to PaidTolls), not the overpaid delta — this
// matches the two-color proportion bar shown above the list in the UI.
func (r *OverviewRepository) GetCostOverview(ctx context.Context, f models.Filters) (models.CostOverviewResponse, error) {
	filter := buildFilter(f)

	matchAmt, mismatchAmt, err := r.matchMismatchAmounts(ctx, filter)
	if err != nil {
		return models.CostOverviewResponse{}, err
	}
	totalUnits, paidTolls, err := r.totalUnitsAndPaidTolls(ctx, filter)
	if err != nil {
		return models.CostOverviewResponse{}, err
	}

	resp := models.CostOverviewResponse{
		MatchAmount:    matchAmt,
		MismatchAmount: mismatchAmt,
		TotalUnits:     totalUnits,
		PaidTolls:      paidTolls,
	}
	total := matchAmt + mismatchAmt
	if total > 0 {
		resp.MatchPct = (matchAmt / total) * 100
		resp.MismatchPct = (mismatchAmt / total) * 100
	}
	return resp, nil
}

// GetCostOverviewByCostCenter powers screenshot 3 — same header as
// GetCostOverview, plus a per-cost-center table via $lookup into
// invoice_raw, since cost_center only exists there.
func (r *OverviewRepository) GetCostOverviewByCostCenter(ctx context.Context, f models.Filters) (models.CostOverviewByCostCenterResponse, error) {
	filter := buildFilter(f)

	matchAmt, mismatchAmt, err := r.matchMismatchAmounts(ctx, filter)
	if err != nil {
		return models.CostOverviewByCostCenterResponse{}, err
	}
	totalUnits, paidTolls, err := r.totalUnitsAndPaidTolls(ctx, filter)
	if err != nil {
		return models.CostOverviewByCostCenterResponse{}, err
	}

	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$lookup", Value: bson.M{
			"from":         "invoice_raw",
			"localField":   "transaction_id",
			"foreignField": "transaction_id",
			"as":           "invoice",
		}}},
		{{Key: "$unwind", Value: bson.M{"path": "$invoice", "preserveNullAndEmptyArrays": true}}},
		{{Key: "$addFields", Value: bson.M{
			"costCenterResolved": bson.M{"$ifNull": bson.A{"$invoice.cost_center", "Unassigned"}},
		}}},
		{{Key: "$group", Value: bson.M{
			"_id":            "$costCenterResolved",
			"totalTxns":      bson.M{"$sum": 1},
			"units":          bson.M{"$addToSet": "$unit"},
			"totalTollsPaid": bson.M{"$sum": "$billed_amount"},
			"tollsOverpaid":  bson.M{"$sum": positiveDeltaCond},
		}}},
		{{Key: "$sort", Value: bson.M{"totalTollsPaid": -1}}},
	}

	cursor, err := r.mismatches.Aggregate(ctx, pipeline)
	if err != nil {
		return models.CostOverviewByCostCenterResponse{}, err
	}
	defer cursor.Close(ctx)

	var rawRows []struct {
		ID             string   `bson:"_id"`
		TotalTxns      int64    `bson:"totalTxns"`
		Units          []string `bson:"units"`
		TotalTollsPaid float64  `bson:"totalTollsPaid"`
		TollsOverpaid  float64  `bson:"tollsOverpaid"`
	}
	if err := cursor.All(ctx, &rawRows); err != nil {
		return models.CostOverviewByCostCenterResponse{}, err
	}

	rows := make([]models.CostCenterRow, 0, len(rawRows))
	for _, r := range rawRows {
		rows = append(rows, models.CostCenterRow{
			CostCenter:     r.ID,
			TotalTxns:      r.TotalTxns,
			Units:          int64(len(r.Units)),
			TotalTollsPaid: r.TotalTollsPaid,
			TollsOverpaid:  r.TollsOverpaid,
		})
	}

	resp := models.CostOverviewByCostCenterResponse{
		MatchAmount: matchAmt, MismatchAmount: mismatchAmt,
		Rows: rows, TotalUnits: totalUnits, PaidTolls: paidTolls,
	}
	total := matchAmt + mismatchAmt
	if total > 0 {
		resp.MatchPct = (matchAmt / total) * 100
		resp.MismatchPct = (mismatchAmt / total) * 100
	}
	return resp, nil
}

// GetInvoiceOverview powers screenshot 4 — counts, not dollar amounts.
func (r *OverviewRepository) GetInvoiceOverview(ctx context.Context, f models.Filters) (models.InvoiceOverviewResponse, error) {
	filter := buildFilter(f)

	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$group", Value: bson.M{
			"_id":           nil,
			"matchCount":    bson.M{"$sum": bson.M{"$cond": bson.A{isMismatchCond, 0, 1}}},
			"mismatchCount": bson.M{"$sum": bson.M{"$cond": bson.A{isMismatchCond, 1, 0}}},
		}}},
	}

	cursor, err := r.mismatches.Aggregate(ctx, pipeline)
	if err != nil {
		return models.InvoiceOverviewResponse{}, err
	}
	defer cursor.Close(ctx)

	var results []struct {
		MatchCount    int64 `bson:"matchCount"`
		MismatchCount int64 `bson:"mismatchCount"`
	}
	if err := cursor.All(ctx, &results); err != nil {
		return models.InvoiceOverviewResponse{}, err
	}

	resp := models.InvoiceOverviewResponse{}
	if len(results) > 0 {
		resp.MatchCount = results[0].MatchCount
		resp.MismatchCount = results[0].MismatchCount
	}
	resp.TotalInvoices = resp.MatchCount + resp.MismatchCount
	if resp.TotalInvoices > 0 {
		resp.MatchPct = (float64(resp.MatchCount) / float64(resp.TotalInvoices)) * 100
		resp.MismatchPct = (float64(resp.MismatchCount) / float64(resp.TotalInvoices)) * 100
	}
	return resp, nil
}

// GetTopUnitsByMismatch powers screenshot 6.
func (r *OverviewRepository) GetTopUnitsByMismatch(ctx context.Context, f models.Filters, limit int64) ([]models.TopUnitRow, error) {
	filter := buildFilter(f)

	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$group", Value: bson.M{
			"_id":           "$unit",
			"tollsPaid":     bson.M{"$sum": "$billed_amount"},
			"tollsMismatch": bson.M{"$sum": bson.M{"$cond": bson.A{isMismatchCond, "$billed_amount", 0}}},
		}}},
		{{Key: "$sort", Value: bson.M{"tollsMismatch": -1}}},
		{{Key: "$limit", Value: limit}},
	}

	cursor, err := r.mismatches.Aggregate(ctx, pipeline)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var rows []models.TopUnitRow
	if err := cursor.All(ctx, &rows); err != nil {
		return nil, err
	}
	if rows == nil {
		rows = []models.TopUnitRow{}
	}
	return rows, nil
}
