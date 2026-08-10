package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"tollmatch-backend/internal/models"
)

// InvoiceViewRepository powers the Invoices table (screenshot 7). It joins
// `mismatches` against `invoice_raw` to surface tag_no/toll_class/
// entry_plaza, which only exist on the raw invoice, not the mismatch
// document. This is intentionally separate from MismatchRepository — that
// one serves the original dashboard's table; this one serves a richer,
// enriched view for this specific screen.
type InvoiceViewRepository struct {
	mismatches *mongo.Collection
}

func NewInvoiceViewRepository(mismatches *mongo.Collection) *InvoiceViewRepository {
	return &InvoiceViewRepository{mismatches: mismatches}
}

// Tab mirrors the screenshot's tab bar — but only the two tabs we actually
// have data for. "Fleet Resolving", "Disputed", "Refunded", "Denied", and
// "Non-Actionable" all require a dispute/refund workflow that does not
// exist anywhere in this pipeline's schema, so they are not built here
// rather than faked with data that isn't real.
type Tab string

const (
	TabAll        Tab = "all"
	TabMatched    Tab = "matched"
	TabMismatched Tab = "mismatched"
)

func (r *InvoiceViewRepository) List(
	ctx context.Context,
	f models.Filters,
	tab Tab,
	search string,
	sortField, sortOrder string,
	page, limit int64,
) (models.InvoiceListResponse, error) {
	filter := buildFilter(f)

	switch tab {
	case TabMatched:
		filter["mismatch_type"] = "reconciled"
	case TabMismatched:
		filter["mismatch_type"] = bson.M{"$ne": "reconciled"}
	}

	if search != "" {
		filter["$or"] = bson.A{
			bson.M{"transaction_id": bson.M{"$regex": search, "$options": "i"}},
			bson.M{"unit": bson.M{"$regex": search, "$options": "i"}},
		}
	}

	order := 1
	if sortOrder == "desc" {
		order = -1
	}
	if sortField == "" {
		sortField = "entry_time"
	}

	basePipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$lookup", Value: bson.M{
			"from":         "invoice_raw",
			"localField":   "transaction_id",
			"foreignField": "transaction_id",
			"as":           "invoice",
		}}},
		{{Key: "$unwind", Value: bson.M{"path": "$invoice", "preserveNullAndEmptyArrays": true}}},
	}

	// Count against the same $match (pre-lookup filter is sufficient for
	// counting — the lookup only adds fields, never removes documents
	// since preserveNullAndEmptyArrays keeps unmatched invoice_raw joins).
	total, err := r.mismatches.CountDocuments(ctx, filter)
	if err != nil {
		return models.InvoiceListResponse{}, err
	}

	pipeline := append(basePipeline,
		bson.D{{Key: "$sort", Value: bson.D{{Key: sortField, Value: order}}}},
		bson.D{{Key: "$skip", Value: (page - 1) * limit}},
		bson.D{{Key: "$limit", Value: limit}},
		bson.D{{Key: "$project", Value: bson.M{
			"transactionId": "$transaction_id",
			"unit":          "$unit",
			"tollsPaid":     "$billed_amount",
			"expected":      "$expected_amount",
			"overpaid":      "$delta_amount",
			"matchType":     "$mismatch_type",
			"status":        "$status",
			"tripId":        "$trip_id",
			"entryTime":     "$entry_time",
			"tagNo":         "$invoice.tag_no",
			"tollClass":     "$invoice.toll_class",
			"entryPlaza":    "$invoice.entry_plaza",
		}}},
	)

	cursor, err := r.mismatches.Aggregate(ctx, pipeline)
	if err != nil {
		return models.InvoiceListResponse{}, err
	}
	defer cursor.Close(ctx)

	var items []models.InvoiceRow
	if err := cursor.All(ctx, &items); err != nil {
		return models.InvoiceListResponse{}, err
	}
	if items == nil {
		items = []models.InvoiceRow{}
	}

	return models.InvoiceListResponse{Items: items, Total: total, Page: page, Limit: limit}, nil
}
