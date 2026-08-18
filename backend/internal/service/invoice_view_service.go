package service

import (
	"context"

	"tollmatch-backend/internal/models"
	"tollmatch-backend/internal/repository"
)

const (
	defaultInvoicePage  = int64(1)
	defaultInvoiceLimit = int64(50) 
	maxInvoiceLimit     = int64(200)
)

var validTabs = map[string]repository.Tab{
	"all":        repository.TabAll,
	"matched":    repository.TabMatched,
	"mismatched": repository.TabMismatched,
}

type InvoiceViewService struct {
	repo *repository.InvoiceViewRepository
}

func NewInvoiceViewService(repo *repository.InvoiceViewRepository) *InvoiceViewService {
	return &InvoiceViewService{repo: repo}
}

func (s *InvoiceViewService) List(
	ctx context.Context,
	f models.Filters,
	tabParam, search, sortField, sortOrder string,
	page, limit int64,
) (models.InvoiceListResponse, error) {
	tab, ok := validTabs[tabParam]
	if !ok {
		tab = repository.TabAll
	}

	if page < 1 {
		page = defaultInvoicePage
	}
	if limit < 1 {
		limit = defaultInvoiceLimit
	}
	if limit > maxInvoiceLimit {
		limit = maxInvoiceLimit
	}
	if !allowedSortFields[sortField] {
		sortField = "entry_time"
	}

	return s.repo.List(ctx, f, tab, search, sortField, sortOrder, page, limit)
}
