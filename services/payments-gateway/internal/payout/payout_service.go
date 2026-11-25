package payout

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/corvane/payments-gateway/internal/clearriver"
	"github.com/corvane/payments-gateway/internal/publisher"
	"github.com/corvane/payments-gateway/internal/store"
	"github.com/sony/gobreaker"
	"go.uber.org/zap"
)

type Request struct {
	ClaimID     string
	ApprovalSeq int
	PayeeName   string
	SortCode    string
	Account     string
	Amount      string
	Currency    string
}

// Service is PayoutService: pays one approved claim exactly once.
type Service struct {
	bank       *clearriver.Client
	db         *store.Store
	pub        *publisher.Publisher
	maxRetries int
	breaker    *gobreaker.CircuitBreaker
	log        *zap.Logger
}

func NewService(bank *clearriver.Client, db *store.Store, pub *publisher.Publisher, maxRetries int, log *zap.Logger) *Service {
	cb := gobreaker.NewCircuitBreaker(gobreaker.Settings{
		Name:        "clearriver",
		MaxRequests: 1,
		Timeout:     60 * time.Second,
		ReadyToTrip: func(c gobreaker.Counts) bool { return c.ConsecutiveFailures >= 5 },
	})
	return &Service{bank: bank, db: db, pub: pub, maxRetries: maxRetries, breaker: cb, log: log}
}

func (s *Service) BreakerOpen() bool { return s.breaker.State() == gobreaker.StateOpen }

// Pay sends the payout with retries, stores claims.payment and publishes payments.settled.v1.
func (s *Service) Pay(ctx context.Context, r Request) error {
	key := fmt.Sprintf("%s-%d", r.ClaimID, r.ApprovalSeq)
	if done, err := s.db.Exists(ctx, key); err != nil {
		return err
	} else if done {
		s.log.Info("duplicate approval ignored", zap.String("key", key))
		return nil
	}
	var res *clearriver.PayoutResult
	var err error
	backoff := 500 * time.Millisecond
	for attempt := 0; attempt <= s.maxRetries; attempt++ {
		out, cbErr := s.breaker.Execute(func() (interface{}, error) {
			return s.bank.CreatePayout(ctx, clearriver.PayoutRequest{
				Reference: r.ClaimID, PayeeName: r.PayeeName, SortCode: r.SortCode,
				AccountNumber: r.Account, Amount: r.Amount, Currency: r.Currency,
			}, key)
		})
		if cbErr == nil {
			res = out.(*clearriver.PayoutResult)
			break
		}
		err = cbErr
		if errors.Is(cbErr, gobreaker.ErrOpenState) || clearriver.IsPermanent(cbErr) {
			break
		}
		time.Sleep(backoff)
		backoff *= 2
	}
	if res == nil {
		_ = s.db.Insert(ctx, store.Payment{IdempotencyKey: key, ClaimID: r.ClaimID, Amount: r.Amount,
			Currency: r.Currency, Status: "FAILED", FailureReason: err.Error()})
		return err
	}
	if err := s.db.Insert(ctx, store.Payment{IdempotencyKey: key, ClaimID: r.ClaimID, Amount: r.Amount,
		Currency: r.Currency, Status: "SETTLED", BankReference: res.PayoutID}); err != nil {
		return err
	}
	return s.pub.Settled(ctx, publisher.PaymentSettled{ClaimID: r.ClaimID, PaymentRef: res.PayoutID,
		Amount: r.Amount, Currency: r.Currency, SettledAt: time.Now().UTC()})
}
