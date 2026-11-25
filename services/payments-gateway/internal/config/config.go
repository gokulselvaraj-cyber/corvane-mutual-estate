package config

import (
	"os"
	"strconv"
	"time"
)

// Config is read from the environment; secrets arrive from Secret Manager as env vars.
type Config struct {
	DatabaseURL        string
	KafkaBootstrap     string
	ApprovedTopic      string
	SettledTopic       string
	ClearRiverURL      string
	ClearRiverClientID string
	ClearRiverSecret   string
	HTTPTimeout        time.Duration
	MaxRetries         int
}

func Load() Config {
	return Config{
		DatabaseURL:        env("CLAIMSDB_URL", "postgres://payments@claimsdb:5432/claimsdb"),
		KafkaBootstrap:     env("KAFKA_BOOTSTRAP", "kafka.corvane.internal:9092"),
		ApprovedTopic:      env("APPROVED_TOPIC", "claims.approved.v1"),
		SettledTopic:       env("SETTLED_TOPIC", "payments.settled.v1"),
		ClearRiverURL:      env("CLEARRIVER_URL", "https://api.clearriver-bank.example/payouts/v2"),
		ClearRiverClientID: env("CLEARRIVER_CLIENT_ID", ""),
		ClearRiverSecret:   env("CLEARRIVER_CLIENT_SECRET", ""), // ${CLEARRIVER_CLIENT_SECRET}
		HTTPTimeout:        dur("CLEARRIVER_TIMEOUT", 5*time.Second),
		MaxRetries:         num("CLEARRIVER_MAX_RETRIES", 3),
	}
}

func env(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func dur(k string, d time.Duration) time.Duration {
	if v, err := time.ParseDuration(os.Getenv(k)); err == nil {
		return v
	}
	return d
}

func num(k string, d int) int {
	if v, err := strconv.Atoi(os.Getenv(k)); err == nil {
		return v
	}
	return d
}
