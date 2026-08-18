package db

import (
	"context"
	"time"

	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"

	"tollmatch-backend/internal/config"
)

type Mongo struct {
	client *mongo.Client
	dbName string
}

func Connect(cfg config.Config) (*Mongo, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	clientOptions := options.Client().
		ApplyURI(cfg.MongoURI).
		SetConnectTimeout(10 * time.Second).
		SetServerSelectionTimeout(10 * time.Second).
		SetDisableOCSPEndpointCheck(true)

	client, err := mongo.Connect(clientOptions)
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

const (
	CollectionMismatches   = "mismatches"
	CollectionQualityRepts = "quality_reports"
	CollectionGPSGapEvents = "gps_gap_events"
	CollectionPhysicalTrip = "physical_trips"
	CollectionInvoiceRaw   = "invoice_raw"
)
