package handler

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"

	"tollmatch-backend/internal/service"
)

type OverviewHandler struct {
	service *service.OverviewService
}

func NewOverviewHandler(s *service.OverviewService) *OverviewHandler {
	return &OverviewHandler{service: s}
}

// GetOverview handles GET /api/overview (screenshot 1)
func (h *OverviewHandler) GetOverview(c *gin.Context) {
	result, err := h.service.GetOverview(c.Request.Context(), parseFilters(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, result)
}

// GetCostOverview handles GET /api/cost-overview (screenshot 2)
func (h *OverviewHandler) GetCostOverview(c *gin.Context) {
	result, err := h.service.GetCostOverview(c.Request.Context(), parseFilters(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, result)
}

// GetCostOverviewByCostCenter handles GET /api/cost-overview/by-cost-center (screenshot 3)
func (h *OverviewHandler) GetCostOverviewByCostCenter(c *gin.Context) {
	result, err := h.service.GetCostOverviewByCostCenter(c.Request.Context(), parseFilters(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, result)
}

// GetInvoiceOverview handles GET /api/invoice-overview (screenshot 4)
func (h *OverviewHandler) GetInvoiceOverview(c *gin.Context) {
	result, err := h.service.GetInvoiceOverview(c.Request.Context(), parseFilters(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, result)
}

// GetMismatchBreakdown handles GET /api/mismatch-breakdown (screenshot 5,
// relabeled from "Invoice Status" — see repository comment for why).
func (h *OverviewHandler) GetMismatchBreakdown(c *gin.Context) {
	result, err := h.service.GetMismatchBreakdown(c.Request.Context(), parseFilters(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"breakdown": result})
}

// GetTopUnitsByMismatch handles GET /api/top-units (screenshot 6)
func (h *OverviewHandler) GetTopUnitsByMismatch(c *gin.Context) {
	limit, _ := strconv.ParseInt(c.DefaultQuery("limit", "10"), 10, 64)
	result, err := h.service.GetTopUnitsByMismatch(c.Request.Context(), parseFilters(c), limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"units": result})
}
