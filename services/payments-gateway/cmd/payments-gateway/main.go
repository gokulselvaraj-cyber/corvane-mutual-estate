package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/corvane/payments-gateway/internal/clearriver"
	"github.com/corvane/payments-gateway/internal/config"
	"github.com/corvane/payments-gateway/internal/consumer"
	"github.com/corvane/payments-gateway/internal/payout"
	"github.com/corvane/payments-gateway/internal/publisher"
	"github.com/corvane/payments-gateway/internal/store"
	"go.uber.org/zap"
)

func main() {
	log, _ := zap.NewProduction()
	defer log.Sync()
	cfg := config.Load()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	db, err := store.Open(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatal("database", zap.Error(err))
	}
	bank := clearriver.New(cfg.ClearRiverURL, cfg.ClearRiverClientID, cfg.ClearRiverSecret, cfg.HTTPTimeout)
	pub := publisher.New(cfg.KafkaBootstrap, cfg.SettledTopic)
	svc := payout.NewService(bank, db, pub, cfg.MaxRetries, log)

	go func() {
		mux := http.NewServeMux()
		mux.HandleFunc("/health/ready", func(w http.ResponseWriter, _ *http.Request) {
			if svc.BreakerOpen() {
				w.WriteHeader(http.StatusServiceUnavailable)
				return
			}
			w.Write([]byte("ok"))
		})
		mux.HandleFunc("/health/live", func(w http.ResponseWriter, _ *http.Request) { w.Write([]byte("ok")) })
		srv := &http.Server{Addr: ":8085", Handler: mux, ReadHeaderTimeout: 5 * time.Second}
		_ = srv.ListenAndServe()
	}()

	c := consumer.NewApprovedClaimConsumer(cfg.KafkaBootstrap, cfg.ApprovedTopic, "payments-gateway", svc, log)
	if err := c.Run(ctx); err != nil {
		log.Fatal("consumer stopped", zap.Error(err))
	}
}
