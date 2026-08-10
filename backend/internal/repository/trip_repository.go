package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"tollmatch-backend/internal/models"
)

// TripRepository is the only place that queries `physical_trips`. It joins
// against `mismatches` via $lookup so "does this trip have mismatches" is
// answered in one database round-trip, not one query per trip in a loop.
type TripRepository struct {
	collection *mongo.Collection // physical_trips
}

func NewTripRepository(collection *mongo.Collection) *TripRepository {
	return &TripRepository{collection: collection}
}

// ListByUnit returns every trip for one unit, each annotated with how many
// mismatches it has and which types — this is the data the "Unit view"
// requirement needs: select a vehicle, see its trips, see which had
// mismatches.
func (r *TripRepository) ListByUnit(ctx context.Context, unit string) ([]models.Trip, error) {
	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: bson.M{"unit": unit}}},
		{{Key: "$sort", Value: bson.M{"start_time": -1}}},
		// Deliberately exclude gps_points before the join — this list view
		// never needs the raw trace, and it can be large per trip.
		{{Key: "$project", Value: bson.M{"gps_points": 0}}},
		{{Key: "$lookup", Value: bson.M{
			"from":         "mismatches",
			"localField":   "trip_id",
			"foreignField": "trip_id",
			"as":           "matchedMismatches",
		}}},
		{{Key: "$addFields", Value: bson.M{
			"mismatchCount": bson.M{"$size": "$matchedMismatches"},
			"mismatchTypes": bson.M{
				"$setUnion": bson.A{"$matchedMismatches.mismatch_type", bson.A{}},
			},
		}}},
		{{Key: "$project", Value: bson.M{"matchedMismatches": 0}}},
	}

	cursor, err := r.collection.Aggregate(ctx, pipeline, options.Aggregate())
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var trips []models.Trip
	if err := cursor.All(ctx, &trips); err != nil {
		return nil, err
	}

	// Never return nil for an empty result — the frontend should see a
	// real empty array, not distinguish between "no trips" and "error"
	// by checking for null.
	if trips == nil {
		trips = []models.Trip{}
	}

	return trips, nil
}
