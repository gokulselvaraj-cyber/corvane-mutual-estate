package store

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Payment is a row of claims.payment (DDL in data/postgres; unique index on idempotency_key).
type Payment struct {
	IdempotencyKey string
	ClaimID        string
	Amount         string
	Currency       string
	Status         string
	BankReference  string
	FailureReason  string
}

type Store struct{ pool *pgxpool.Pool }

func Open(ctx context.Context, url string) (*Store, error) {
	p, err := pgxpool.New(ctx, url)
	return &Store{pool: p}, err
}

func (s *Store) Exists(ctx context.Context, key string) (bool, error) {
	var n int
	err := s.pool.QueryRow(ctx,
		"SELECT count(*) FROM claims.payment WHERE idempotency_key = $1 AND status = 'SETTLED'", key).Scan(&n)
	return n > 0, err
}

func (s *Store) Insert(ctx context.Context, p Payment) error {
	_, err := s.pool.Exec(ctx, `INSERT INTO claims.payment
	  (idempotency_key, claim_id, amount, currency, status, bank_reference, failure_reason, created_at)
	  VALUES ($1, $2, $3::numeric, $4, $5, NULLIF($6,''), NULLIF($7,''), now())
	  ON CONFLICT (idempotency_key) DO UPDATE SET status = EXCLUDED.status,
	    bank_reference = EXCLUDED.bank_reference, failure_reason = EXCLUDED.failure_reason`,
		p.IdempotencyKey, p.ClaimID, p.Amount, p.Currency, p.Status, p.BankReference, p.FailureReason)
	return err
}
