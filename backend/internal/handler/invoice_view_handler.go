package handler

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"

	"tollmatch-backend/internal/service"
)

type InvoiceViewHandler struct {
	service *service.InvoiceViewService
}

func NewInvoiceViewHandler(s *service.InvoiceViewService) *InvoiceViewHandler {
	return &InvoiceViewHandler{service: s}
}

// List handles GET /api/invoices (screenshot 7). Deliberately does NOT
// implement export, dispute creation, "Open in TollPay", "Enable Edit
// Invoices", or a Match Type filter dropdown — none of those have real
// backing functionality in this pipeline, per the request to only build
// what we actually have.
func (h *InvoiceViewHandler) List(c *gin.Context) {
	filters := parseFilters(c)
	tab := c.DefaultQuery("tab", "all")
	search := c.Query("search")
	sortField := c.DefaultQuery("sort", "entry_time")
	sortOrder := c.DefaultQuery("order", "desc")
	page, _ := strconv.ParseInt(c.DefaultQuery("page", "1"), 10, 64)
	limit, _ := strconv.ParseInt(c.DefaultQuery("limit", "50"), 10, 64)

	result, err := h.service.List(c.Request.Context(), filters, tab, search, sortField, sortOrder, page, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, result)
}
