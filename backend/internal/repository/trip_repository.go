package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"

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
		// A trip's joined mismatches now include EVERY invoice GPS-confirmed
		// against it, regardless of outcome — a genuinely correct match
		// (verdict "matched") also gets trip_id set, since trip_id is
		// assigned whenever GPS confirms presence, not only on a problem.
		// $size of the raw join would therefore count "how many invoices
		// touched this trip", not "how many were actually wrong" — filter
		// down to confirmed-problem verdicts first.
		{{Key: "$addFields", Value: bson.M{
			"confirmedProblems": bson.M{"$filter": bson.M{
				"input": "$matchedMismatches",
				"as":    "m",
				"cond":  bson.M{"$in": bson.A{"$$m.verdict", bson.A{"mismatch", "duplicate"}}},
			}},
		}}},
		{{Key: "$addFields", Value: bson.M{
			"mismatchCount": bson.M{"$size": "$confirmedProblems"},
			// Effective category per problem record: mismatch_type when
			// verdict is "mismatch", otherwise the verdict itself
			// ("duplicate") — same computation used everywhere else in
			// this API, so a trip's badge here always agrees with what
			// the invoices table and breakdown pie would show for the
			// same records.
			"mismatchTypes": bson.M{"$setUnion": bson.A{
				bson.M{"$map": bson.M{
					"input": "$confirmedProblems",
					"as":    "m",
					"in": bson.M{"$cond": bson.A{
						bson.M{"$eq": bson.A{"$$m.verdict", "mismatch"}},
						"$$m.mismatch_type",
						"$$m.verdict",
					}},
				}},
				bson.A{},
			}},
		}}},
		{{Key: "$project", Value: bson.M{"matchedMismatches": 0, "confirmedProblems": 0}}},
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
