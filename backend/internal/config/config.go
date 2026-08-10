package config

import (
	"log"
	"os"
)

// Config holds every environment-driven setting the app needs. One place,
// nothing scattered across files as os.Getenv calls.
type Config struct {
	MongoURI      string
	MongoDB       string
	Port          string
	AllowedOrigin string
}

func Load() Config {
	cfg := Config{
		MongoURI:      getEnv("MONGO_URI", "mongodb+srv://nikhilsahu1312_db_user:ypErXYXnAdK3d7zy@cluster0.mdfqf9x.mongodb.net/?appName=Cluster0"),
		MongoDB:       getEnv("MONGO_DB", "tollmatch"),
		Port:          getEnv("PORT", "8080"),
		AllowedOrigin: getEnv("ALLOWED_ORIGIN", "http://localhost:3000"),
	}
	log.Printf("config loaded: db=%s port=%s", cfg.MongoDB, cfg.Port)
	return cfg
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
