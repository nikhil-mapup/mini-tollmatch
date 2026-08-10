package router

import (
	"github.com/gin-gonic/gin"

	"tollmatch-backend/internal/handler"
	"tollmatch-backend/internal/middleware"
)

// New wires every route to its handler. This file should only ever grow by
// adding lines here — no logic belongs in this file.
func New(mismatchHandler *handler.MismatchHandler, allowedOrigin string) *gin.Engine {
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(middleware.RequestLogger())
	r.Use(middleware.CORS(allowedOrigin))

	r.GET("/healthz", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok"})
	})

	api := r.Group("/api")
	{
		api.GET("/summary", mismatchHandler.GetSummary)
		api.GET("/mismatches", mismatchHandler.ListMismatches)
		api.GET("/units", mismatchHandler.GetUnits)
		api.GET("/mismatch-types", mismatchHandler.GetMismatchTypes)
	}

	return r
}
