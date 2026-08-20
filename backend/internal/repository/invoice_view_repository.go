package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"

	"tollmatch-backend/internal/models"
)

// InvoiceViewRepository powers the Invoices table. It joins `mismatches`
// against `invoice_raw` to surface tag_no/toll_class/entry_plaza/post_date,
// which only exist on the raw invoice, not the mismatch document.
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
	// buildFilter() already applies f.Type (routed to verdict when the
	// value is "matched", to mismatch_type otherwise — see buildFilter).
	// The tab below is a coarser split of the same underlying data — if
	// both are present, the more specific f.Type wins, applied AFTER the
	// tab switch so it can't be silently overwritten.
	filter := buildFilter(f)

	// buildFilter() also applies Start/End against `entry_time` (the GPS
	// crossing time) — correct for the dashboard's cards, but not what
	// this page needs. Strip it here and re-apply the same Start/End
	// range against invoice.post_date instead, after the $lookup, since
	// post date is what actually matters when reviewing invoices.
	delete(filter, "entry_time")

	switch tab {
	case TabMatched:
		filter["verdict"] = "matched"
	case TabMismatched:
		// "Mismatched" means a confirmed, evidence-backed problem —
		// mismatch or duplicate. "unassigned" is deliberately excluded:
		// it's unresolved, not proven wrong, so it only shows up under
		// the "All" tab, not here.
		filter["verdict"] = bson.M{"$in": bson.A{"mismatch", "duplicate"}}
	}
	if f.Type != "" {
		if verdictLevelTypes[f.Type] {
			filter["verdict"] = f.Type
			delete(filter, "mismatch_type")
		} else {
			filter["mismatch_type"] = f.Type
		}
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

	// TagNo and the post_date range can only be filtered AFTER the
	// $lookup, since neither field exists on `mismatches` itself.
	// Building this as a separate post-lookup match stage, rather than
	// folding it into `filter` above, keeps that distinction explicit
	// rather than accidental.
	postLookupMatch := bson.M{}
	if f.TagNo != "" {
		postLookupMatch["invoice.tag_no"] = f.TagNo
	}
	if f.Start != nil || f.End != nil {
		dateFilter := bson.M{}
		if f.Start != nil {
			dateFilter["$gte"] = *f.Start
		}
		if f.End != nil {
			dateFilter["$lte"] = *f.End
		}
		postLookupMatch["invoice.post_date"] = dateFilter
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
	}
	if len(postLookupMatch) > 0 {
		pipeline = append(pipeline, bson.D{{Key: "$match", Value: postLookupMatch}})
	}

	// A $facet computing count and the paginated page in ONE aggregation
	// call. This replaced a simpler pre-lookup CountDocuments() call —
	// that shortcut was only ever correct because no filter previously
	// depended on the joined invoice_raw data. Now that TagNo/PostDate
	// filters can exclude documents AFTER the join, counting before the
	// join would silently overcount whenever either filter is active.
	pipeline = append(pipeline, bson.D{{Key: "$facet", Value: bson.M{
		"data": bson.A{
			bson.M{"$sort": bson.D{{Key: sortField, Value: order}}},
			bson.M{"$skip": (page - 1) * limit},
			bson.M{"$limit": limit},
			bson.M{"$project": bson.M{
				"transactionId": "$transaction_id",
				"unit":          "$unit",
				"tollsPaid":     "$billed_amount",
				"expected":      "$expected_amount",
				"overpaid":      "$delta_amount",
				"verdict":       "$verdict",
				// Effective category for display: mismatch_type when the
				// verdict is a confirmed mismatch, otherwise the verdict
				// itself (matched/duplicate/unassigned).
				"matchType": bson.M{"$cond": bson.A{
					bson.M{"$eq": bson.A{"$verdict", "mismatch"}},
					"$mismatch_type",
					"$verdict",
				}},
				"status":                "$status",
				"tripId":                "$trip_id",
				"entryTime":             "$entry_time",
				"tagNo":                 "$invoice.tag_no",
				"tollClass":             "$invoice.toll_class",
				"entryPlaza":            "$invoice.entry_plaza",
				"postDate":              "$invoice.post_date",
				"reasonCode":            "$reason_code",
				"inferredVehicleType":   "$inferred_vehicle_type",
				"vehicleTypeConfidence": "$vehicle_type_confidence",
				"isDuplicate":           "$is_duplicate",
			}},
		},
		"totalCount": bson.A{
			bson.M{"$count": "count"},
		},
	}}})

	cursor, err := r.mismatches.Aggregate(ctx, pipeline)
	if err != nil {
		return models.InvoiceListResponse{}, err
	}
	defer cursor.Close(ctx)

	var facetResult []struct {
		Data       []models.InvoiceRow `bson:"data"`
		TotalCount []struct {
			Count int64 `bson:"count"`
		} `bson:"totalCount"`
	}
	if err := cursor.All(ctx, &facetResult); err != nil {
		return models.InvoiceListResponse{}, err
	}

	items := []models.InvoiceRow{}
	var total int64
	if len(facetResult) > 0 {
		if facetResult[0].Data != nil {
			items = facetResult[0].Data
		}
		if len(facetResult[0].TotalCount) > 0 {
			total = facetResult[0].TotalCount[0].Count
		}
	}

	return models.InvoiceListResponse{Items: items, Total: total, Page: page, Limit: limit}, nil
}