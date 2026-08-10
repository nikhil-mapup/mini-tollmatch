package handler

import (
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"

	"tollmatch-backend/internal/service"
)

type TripHandler struct {
	service *service.TripService
}

func NewTripHandler(s *service.TripService) *TripHandler {
	return &TripHandler{service: s}
}

// ListTrips handles GET /api/trips?unit=...
func (h *TripHandler) ListTrips(c *gin.Context) {
	unit := c.Query("unit")

	trips, err := h.service.ListByUnit(c.Request.Context(), unit)
	if err != nil {
		if errors.Is(err, service.ErrUnitRequired) {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"trips": trips})
}
