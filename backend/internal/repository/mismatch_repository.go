package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"

	"tollmatch-backend/internal/models"
)

// MismatchRepository is the ONLY place that constructs a Mongo query or
// aggregation pipeline for mismatch data. Nothing above this layer (service,
// handler) should ever import the Mongo driver — if a future engineer needs
// to add a query, this is the one file to open.
type MismatchRepository struct {
	collection *mongo.Collection
}

func NewMismatchRepository(collection *mongo.Collection) *MismatchRepository {
	return &MismatchRepository{collection: collection}
}

// verdictLevelTypes covers every value that actually lives on `verdict`,
// not `mismatch_type`, under the new schema. Only "misread", "unmatched",
// and "max_toll" are real mismatch_type values now — "matched",
// "unassigned", "duplicate", and "insufficient_gps" are all top-level
// verdicts. Filtering by any of the latter against mismatch_type would
// silently match nothing, since that field is null/absent for all of them.
var verdictLevelTypes = map[string]bool{
	"matched":          true,
	"unassigned":       true,
	"duplicate":        true,
	"insufficient_gps": true,
}

// buildFilter turns Filters into a bson.M once, shared by every query below
// — the summary and the list must apply IDENTICAL filtering, or the cards
// and table could show numbers for different underlying data.
func buildFilter(f models.Filters) bson.M {
	filter := bson.M{}

	if f.Unit != "" {
		filter["unit"] = f.Unit
	}
	if f.Type != "" {
		if verdictLevelTypes[f.Type] {
			filter["verdict"] = f.Type
		} else {
			filter["mismatch_type"] = f.Type
		}
	}
	if f.TransactionID != "" {
		filter["transaction_id"] = f.TransactionID
	}
	if f.Start != nil || f.End != nil {
		dateFilter := bson.M{}
		if f.Start != nil {
			dateFilter["$gte"] = *f.Start
		}
		if f.End != nil {
			dateFilter["$lte"] = *f.End
		}
		filter["entry_time"] = dateFilter
	}

	return filter
}

func (r *MismatchRepository) GetSummary(ctx context.Context, f models.Filters) (models.SummaryResponse, error) {
	filter := buildFilter(f)

	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$group", Value: bson.M{
			"_id":            nil,
			"totalTollSpend": bson.M{"$sum": "$billed_amount"},
			"mismatchCount": bson.M{
				"$sum": bson.M{"$cond": bson.A{bson.M{"$in": bson.A{"$verdict", models.ConfirmedProblemVerdicts}}, 1, 0}},
			},
			"mismatchAmount": bson.M{
				"$sum": bson.M{"$cond": bson.A{
					bson.M{"$in": bson.A{"$verdict", models.ConfirmedProblemVerdicts}},
					bson.M{"$abs": "$delta_amount"},
					0,
				}},
			},
			"unconfirmedCount": bson.M{
				"$sum": bson.M{"$cond": bson.A{bson.M{"$in": bson.A{"$verdict", models.UnconfirmedVerdicts}}, 1, 0}},
			},
		}}},
	}

	cursor, err := r.collection.Aggregate(ctx, pipeline)
	if err != nil {
		return models.SummaryResponse{}, err
	}
	defer cursor.Close(ctx)

	var results []struct {
		TotalTollSpend   float64 `bson:"totalTollSpend"`
		MismatchCount    int64   `bson:"mismatchCount"`
		MismatchAmount   float64 `bson:"mismatchAmount"`
		UnconfirmedCount int64   `bson:"unconfirmedCount"`
	}
	if err := cursor.All(ctx, &results); err != nil {
		return models.SummaryResponse{}, err
	}

	summary := models.SummaryResponse{}
	if len(results) > 0 {
		summary.TotalTollSpend = results[0].TotalTollSpend
		summary.MismatchCount = results[0].MismatchCount
		summary.MismatchAmount = results[0].MismatchAmount
		summary.UnconfirmedCount = results[0].UnconfirmedCount
	}

	topType, err := r.getTopType(ctx, filter)
	if err != nil {
		return models.SummaryResponse{}, err
	}
	summary.TopType = topType

	return summary, nil
}

// getTopType groups by the "effective category" — mismatch_type when the
// verdict is a confirmed mismatch, otherwise the verdict itself — so
// "unassigned", "insufficient_gps", and "duplicate" (all verdicts, not
// mismatch_type values in the new schema) show up correctly instead of
// being invisible to a query that only ever looked at mismatch_type.
func (r *MismatchRepository) getTopType(ctx context.Context, filter bson.M) (string, error) {
	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$match", Value: bson.M{"verdict": bson.M{"$ne": "matched"}}}},
		{{Key: "$group", Value: bson.M{
			"_id": bson.M{"$cond": bson.A{
				bson.M{"$eq": bson.A{"$verdict", "mismatch"}},
				"$mismatch_type",
				"$verdict",
			}},
			"count": bson.M{"$sum": 1},
		}}},
		{{Key: "$sort", Value: bson.M{"count": -1}}},
		{{Key: "$limit", Value: 1}},
	}

	cursor, err := r.collection.Aggregate(ctx, pipeline)
	if err != nil {
		return "", err
	}
	defer cursor.Close(ctx)

	var results []models.TypeCount
	if err := cursor.All(ctx, &results); err != nil {
		return "", err
	}
	if len(results) == 0 {
		return "", nil // legitimate empty state — no mismatches for these filters
	}
	return results[0].Type, nil
}

func (r *MismatchRepository) List(ctx context.Context, f models.Filters, sortField, sortOrder string, page, limit int64) ([]models.Mismatch, int64, error) {
	filter := buildFilter(f)

	total, err := r.collection.CountDocuments(ctx, filter)
	if err != nil {
		return nil, 0, err
	}

	order := 1
	if sortOrder == "desc" {
		order = -1
	}
	if sortField == "" {
		sortField = "entry_time"
	}

	opts := options.Find().
		SetSort(bson.D{{Key: sortField, Value: order}}).
		SetSkip((page - 1) * limit).
		SetLimit(limit)

	cursor, err := r.collection.Find(ctx, filter, opts)
	if err != nil {
		return nil, 0, err
	}
	defer cursor.Close(ctx)

	var items []models.Mismatch
	if err := cursor.All(ctx, &items); err != nil {
		return nil, 0, err
	}

	return items, total, nil
}

func (r *MismatchRepository) DistinctUnits(ctx context.Context) ([]string, error) {
	var units []string
	if err := r.collection.Distinct(ctx, "unit", bson.M{}).Decode(&units); err != nil {
		return nil, err
	}
	return units, nil
}

// TypeCounts groups by the "effective category" (see getTopType above) so
// the breakdown includes every real outcome the pipeline can produce —
// matched, duplicate, unassigned, insufficient_gps, and the three
// mismatch_type values — not just whatever happened to be non-null in
// mismatch_type.
func (r *MismatchRepository) TypeCounts(ctx context.Context, f models.Filters) ([]models.TypeCount, error) {
	filter := buildFilter(f)

	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$group", Value: bson.M{
			"_id": bson.M{"$cond": bson.A{
				bson.M{"$eq": bson.A{"$verdict", "mismatch"}},
				"$mismatch_type",
				"$verdict",
			}},
			"count": bson.M{"$sum": 1},
		}}},
		{{Key: "$sort", Value: bson.M{"count": -1}}},
	}

	cursor, err := r.collection.Aggregate(ctx, pipeline)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var results []models.TypeCount
	if err := cursor.All(ctx, &results); err != nil {
		return nil, err
	}
	if results == nil {
		results = []models.TypeCount{}
	}
	return results, nil
}
