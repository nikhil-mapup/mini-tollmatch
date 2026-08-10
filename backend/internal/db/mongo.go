package db

import (
	"context"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"tollmatch-backend/internal/config"
)

// Mongo wraps the driver client and exposes collection getters, so callers
// never construct a *mongo.Collection by hand or repeat the DB name string.
type Mongo struct {
	client *mongo.Client
	dbName string
}

func Connect(cfg config.Config) (*Mongo, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(cfg.MongoURI))
	if err != nil {
		return nil, err
	}

	if err := client.Ping(ctx, nil); err != nil {
		return nil, err
	}

	return &Mongo{client: client, dbName: cfg.MongoDB}, nil
}

func (m *Mongo) Collection(name string) *mongo.Collection {
	return m.client.Database(m.dbName).Collection(name)
}

func (m *Mongo) Disconnect(ctx context.Context) error {
	return m.client.Disconnect(ctx)
}

// Collection name constants — mirrors config/constants.py from the Python
// pipeline. Keeping these in one place means a typo in a collection name
// is a compile error here, not a silent empty-result query at runtime.
const (
	CollectionMismatches   = "mismatches"
	CollectionQualityRepts = "quality_reports"
	CollectionGPSGapEvents = "gps_gap_events"
	CollectionPhysicalTrip = "physical_trips"
	CollectionInvoiceRaw   = "invoice_raw"
)
