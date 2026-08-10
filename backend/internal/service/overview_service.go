package service

import (
	"context"

	"tollmatch-backend/internal/models"
	"tollmatch-backend/internal/repository"
)

const defaultTopUnitsLimit = int64(10)

type OverviewService struct {
	overviewRepo *repository.OverviewRepository
	// Reused, not duplicated — MismatchRepository.TypeCounts already
	// computes exactly what the breakdown pie (screenshot 5) needs.
	mismatchRepo *repository.MismatchRepository
}

func NewOverviewService(overviewRepo *repository.OverviewRepository, mismatchRepo *repository.MismatchRepository) *OverviewService {
	return &OverviewService{overviewRepo: overviewRepo, mismatchRepo: mismatchRepo}
}

func (s *OverviewService) GetOverview(ctx context.Context, f models.Filters) (models.OverviewResponse, error) {
	return s.overviewRepo.GetOverview(ctx, f)
}

func (s *OverviewService) GetCostOverview(ctx context.Context, f models.Filters) (models.CostOverviewResponse, error) {
	return s.overviewRepo.GetCostOverview(ctx, f)
}

func (s *OverviewService) GetCostOverviewByCostCenter(ctx context.Context, f models.Filters) (models.CostOverviewByCostCenterResponse, error) {
	return s.overviewRepo.GetCostOverviewByCostCenter(ctx, f)
}

func (s *OverviewService) GetInvoiceOverview(ctx context.Context, f models.Filters) (models.InvoiceOverviewResponse, error) {
	return s.overviewRepo.GetInvoiceOverview(ctx, f)
}

func (s *OverviewService) GetMismatchBreakdown(ctx context.Context, f models.Filters) ([]models.TypeCount, error) {
	return s.mismatchRepo.TypeCounts(ctx, f)
}

func (s *OverviewService) GetTopUnitsByMismatch(ctx context.Context, f models.Filters, limit int64) ([]models.TopUnitRow, error) {
	if limit < 1 {
		limit = defaultTopUnitsLimit
	}
	return s.overviewRepo.GetTopUnitsByMismatch(ctx, f, limit)
}
