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

// buildFilter turns Filters into a bson.M once, shared by every query below
// — the summary and the list must apply IDENTICAL filtering, or the cards
// and table could show numbers for different underlying data.
func buildFilter(f models.Filters) bson.M {
	filter := bson.M{}

	if f.Unit != "" {
		filter["unit"] = f.Unit
	}
	if f.Type != "" {
		filter["mismatch_type"] = f.Type
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
				"$sum": bson.M{"$cond": bson.A{bson.M{"$ne": bson.A{"$mismatch_type", "reconciled"}}, 1, 0}},
			},
			"mismatchAmount": bson.M{
				"$sum": bson.M{"$cond": bson.A{
					bson.M{"$ne": bson.A{"$mismatch_type", "reconciled"}},
					bson.M{"$abs": "$delta_amount"},
					0,
				}},
			},
		}}},
	}

	cursor, err := r.collection.Aggregate(ctx, pipeline)
	if err != nil {
		return models.SummaryResponse{}, err
	}
	defer cursor.Close(ctx)

	var results []struct {
		TotalTollSpend float64 `bson:"totalTollSpend"`
		MismatchCount  int64   `bson:"mismatchCount"`
		MismatchAmount float64 `bson:"mismatchAmount"`
	}
	if err := cursor.All(ctx, &results); err != nil {
		return models.SummaryResponse{}, err
	}

	summary := models.SummaryResponse{}
	if len(results) > 0 {
		summary.TotalTollSpend = results[0].TotalTollSpend
		summary.MismatchCount = results[0].MismatchCount
		summary.MismatchAmount = results[0].MismatchAmount
	}

	topType, err := r.getTopType(ctx, filter)
	if err != nil {
		return models.SummaryResponse{}, err
	}
	summary.TopType = topType

	return summary, nil
}

func (r *MismatchRepository) getTopType(ctx context.Context, filter bson.M) (string, error) {
	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$match", Value: bson.M{"mismatch_type": bson.M{"$ne": "reconciled"}}}},
		{{Key: "$group", Value: bson.M{"_id": "$mismatch_type", "count": bson.M{"$sum": 1}}}},
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

func (r *MismatchRepository) TypeCounts(ctx context.Context, f models.Filters) ([]models.TypeCount, error) {
	filter := buildFilter(f)

	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$group", Value: bson.M{"_id": "$mismatch_type", "count": bson.M{"$sum": 1}}}},
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
	return results, nil
}
