package service

import (
	"context"
	"errors"

	"tollmatch-backend/internal/models"
	"tollmatch-backend/internal/repository"
)

var ErrUnitRequired = errors.New("unit is required")

type TripService struct {
	repo *repository.TripRepository
}

func NewTripService(repo *repository.TripRepository) *TripService {
	return &TripService{repo: repo}
}

func (s *TripService) ListByUnit(ctx context.Context, unit string) ([]models.Trip, error) {
	if unit == "" {
		// A unit-scoped query with no unit would return every trip in the
		// fleet under a "unit view" — that's a different feature. Fail
		// clearly instead of silently returning everything.
		return nil, ErrUnitRequired
	}
	return s.repo.ListByUnit(ctx, unit)
}
