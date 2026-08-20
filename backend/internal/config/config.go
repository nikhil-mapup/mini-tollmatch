package config

import (
	"log"
	"os"
)
type Config struct {
	MongoURI      string
	MongoDB       string
	Port          string
	AllowedOrigin string
}

func Load() Config {
	cfg := Config{
		MongoURI:      getEnv("MONGO_URI", "mongodb://nikhilsahu1312_db_user:ypErXYXnAdK3d7zy@ac-ccq1h0n-shard-00-00.mdfqf9x.mongodb.net:27017,ac-ccq1h0n-shard-00-01.mdfqf9x.mongodb.net:27017,ac-ccq1h0n-shard-00-02.mdfqf9x.mongodb.net:27017/?tls=true&authSource=admin&replicaSet=atlas-6pn8t3-shard-0&appName=Cluster0"),
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
