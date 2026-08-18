package handler

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"

	"tollmatch-backend/internal/models"
	"tollmatch-backend/internal/service"
)

// MismatchHandler only knows about HTTP: parsing query params off a
// gin.Context and writing JSON back. It never touches Mongo directly and
// never contains business rules — those live in the service layer. If a
// query param needs new validation, that change belongs in service, not here.
type MismatchHandler struct {
	service *service.MismatchService
}

func NewMismatchHandler(s *service.MismatchService) *MismatchHandler {
	return &MismatchHandler{service: s}
}

// parseFilters is shared by every handler below — summary and list MUST
// parse filters identically, or the cards and table could silently
// represent different underlying queries.
func parseFilters(c *gin.Context) models.Filters {
	f := models.Filters{
		Unit:          c.Query("unit"),
		Type:          c.Query("type"),
		TransactionID: c.Query("transactionId"),
		TagNo:         c.Query("tagNo"),
	}

	if start := c.Query("start"); start != "" {
		if t, err := time.Parse(time.RFC3339, start); err == nil {
			f.Start = &t
		}
	}
	if end := c.Query("end"); end != "" {
		if t, err := time.Parse(time.RFC3339, end); err == nil {
			f.End = &t
		}
	}

	return f
}

// GetSummary handles GET /api/summary
func (h *MismatchHandler) GetSummary(c *gin.Context) {
	filters := parseFilters(c)

	summary, err := h.service.GetSummary(c.Request.Context(), filters)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, summary)
}

// ListMismatches handles GET /api/mismatches
func (h *MismatchHandler) ListMismatches(c *gin.Context) {
	filters := parseFilters(c)

	sortField := c.DefaultQuery("sort", "entry_time")
	sortOrder := c.DefaultQuery("order", "desc")
	page, _ := strconv.ParseInt(c.DefaultQuery("page", "1"), 10, 64)
	limit, _ := strconv.ParseInt(c.DefaultQuery("limit", "25"), 10, 64)

	result, err := h.service.ListMismatches(c.Request.Context(), filters, sortField, sortOrder, page, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, result)
}

// GetUnits handles GET /api/units
func (h *MismatchHandler) GetUnits(c *gin.Context) {
	units, err := h.service.DistinctUnits(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"units": units})
}

// GetMismatchTypes handles GET /api/mismatch-types
func (h *MismatchHandler) GetMismatchTypes(c *gin.Context) {
	filters := parseFilters(c)

	types, err := h.service.TypeCounts(c.Request.Context(), filters)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"types": types})
}