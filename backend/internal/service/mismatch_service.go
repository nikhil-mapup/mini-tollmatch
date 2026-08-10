package service

import (
	"context"
	"fmt"

	"tollmatch-backend/internal/models"
	"tollmatch-backend/internal/repository"
)

const (
	defaultPage  = int64(1)
	defaultLimit = int64(25)
	maxLimit     = int64(200)
)

// MismatchService sits between the HTTP layer and the repository. It owns
// defaults and validation (page numbers, limit caps, sort field whitelist)
// so the repository can stay a dumb, trustworthy query layer, and the
// handler can stay a dumb HTTP layer. Business rules live in exactly one
// place: here.
type MismatchService struct {
	repo *repository.MismatchRepository
}

func NewMismatchService(repo *repository.MismatchRepository) *MismatchService {
	return &MismatchService{repo: repo}
}

var allowedSortFields = map[string]bool{
	"entry_time":    true,
	"billed_amount": true,
	"delta_amount":  true,
	"unit":          true,
	"mismatch_type": true,
}

func (s *MismatchService) GetSummary(ctx context.Context, f models.Filters) (models.SummaryResponse, error) {
	return s.repo.GetSummary(ctx, f)
}

func (s *MismatchService) ListMismatches(ctx context.Context, f models.Filters, sortField, sortOrder string, page, limit int64) (models.MismatchListResponse, error) {
	if page < 1 {
		page = defaultPage
	}
	if limit < 1 {
		limit = defaultLimit
	}
	if limit > maxLimit {
		limit = maxLimit
	}
	if !allowedSortFields[sortField] {
		// Never let an arbitrary client-supplied field reach the database
		// sort — silently falling back is safer than erroring here, since
		// an unrecognized sort is a UI bug, not a user-facing failure.
		sortField = "entry_time"
	}

	items, total, err := s.repo.List(ctx, f, sortField, sortOrder, page, limit)
	if err != nil {
		return models.MismatchListResponse{}, fmt.Errorf("list mismatches: %w", err)
	}

	return models.MismatchListResponse{
		Items: items,
		Total: total,
		Page:  page,
		Limit: limit,
	}, nil
}

func (s *MismatchService) DistinctUnits(ctx context.Context) ([]string, error) {
	return s.repo.DistinctUnits(ctx)
}

func (s *MismatchService) TypeCounts(ctx context.Context, f models.Filters) ([]models.TypeCount, error) {
	return s.repo.TypeCounts(ctx, f)
}
