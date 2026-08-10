package main

import (
	"context"
	"log"

	"tollmatch-backend/internal/config"
	"tollmatch-backend/internal/db"
	"tollmatch-backend/internal/handler"
	"tollmatch-backend/internal/repository"
	"tollmatch-backend/internal/router"
	"tollmatch-backend/internal/service"
)

func main() {
	cfg := config.Load()

	mongo, err := db.Connect(cfg)
	if err != nil {
		log.Fatalf("mongo connect failed: %v", err)
	}
	defer mongo.Disconnect(context.Background())

	// Wiring: repository -> service -> handler -> router.
	// Each layer only depends on the one directly below it.
	mismatchRepo := repository.NewMismatchRepository(mongo.Collection(db.CollectionMismatches))
	mismatchService := service.NewMismatchService(mismatchRepo)
	mismatchHandler := handler.NewMismatchHandler(mismatchService)

	tripRepo := repository.NewTripRepository(mongo.Collection(db.CollectionPhysicalTrip))
	tripService := service.NewTripService(tripRepo)
	tripHandler := handler.NewTripHandler(tripService)

	overviewRepo := repository.NewOverviewRepository(
		mongo.Collection(db.CollectionMismatches),
		mongo.Collection(db.CollectionInvoiceRaw),
	)
	overviewService := service.NewOverviewService(overviewRepo, mismatchRepo)
	overviewHandler := handler.NewOverviewHandler(overviewService)

	invoiceViewRepo := repository.NewInvoiceViewRepository(mongo.Collection(db.CollectionMismatches))
	invoiceViewService := service.NewInvoiceViewService(invoiceViewRepo)
	invoiceViewHandler := handler.NewInvoiceViewHandler(invoiceViewService)

	r := router.New(mismatchHandler, tripHandler, overviewHandler, invoiceViewHandler, cfg.AllowedOrigin)

	log.Printf("listening on :%s", cfg.Port)
	if err := r.Run(":" + cfg.Port); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}
