"""Builder C core part 2: payments-gateway (Go) and notifications (TS). Run: python3 -I c_core2.py <estate_root>"""
import os
import sys

ROOT = sys.argv[1]
F = {}
P = "services/payments-gateway/"

F[P + "go.mod"] = '''module github.com/corvane/payments-gateway

go 1.22

require (
	github.com/confluentinc/confluent-kafka-go/v2 v2.4.0
	github.com/jackc/pgx/v5 v5.6.0
	github.com/sony/gobreaker v1.0.0
	go.uber.org/zap v1.27.0
)
'''

F[P + "Dockerfile"] = '''FROM golang:1.22 AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=1 go build -o /out/payments-gateway ./cmd/payments-gateway

FROM gcr.io/distroless/base-debian12
COPY --from=build /out/payments-gateway /payments-gateway
EXPOSE 8085
USER 10001
ENTRYPOINT ["/payments-gateway"]
'''

F[P + "catalog-info.yaml"] = '''apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: payments-gateway
  description: Pays approved claims through ClearRiver Bank and reports settlement back to claims.
  tags: [go, payments]
spec:
  type: service
  lifecycle: production
  owner: team-payments
  system: corvane-claims
  consumesApis: [clearriver-payouts-v2]
  dependsOn: [resource:claimsdb, resource:kafka-claims]
'''

F[P + "README.md"] = '''# payments-gateway

Consumes `claims.approved.v1`, pays the claimant through the ClearRiver Bank Payouts API v2, records the
payment in `claims.payment` and publishes `payments.settled.v1` (claims-service marks the claim PAID).

* Outbound call: 5 s timeout, up to 3 retries with exponential back-off, circuit breaker (opens after
  5 consecutive failures, half-open after 60 s).
* Idempotency: the claim id + approval sequence is the `idempotency_key`; ClearRiver dedupes on the
  `Idempotency-Key` header and we keep a unique index on `claims.payment.idempotency_key`.
* No automated tests yet (PAY-77). Owner: team-payments.
'''

F[P + "cmd/payments-gateway/main.go"] = '''package main

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
'''

F[P + "internal/config/config.go"] = '''package config

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
'''

F[P + "internal/consumer/approved_claim_consumer.go"] = '''package consumer

import (
	"context"
	"encoding/json"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/corvane/payments-gateway/internal/payout"
	"go.uber.org/zap"
)

// ClaimApproved mirrors contracts/avro/ClaimApproved.avsc (published by claims-service ClaimApprovalService).
type ClaimApproved struct {
	ClaimID          string `json:"claimId"`
	ApprovalSeq      int    `json:"approvalSeq"`
	PolicyNumber     string `json:"policyNumber"`
	LineCode         string `json:"lineCode"`
	PayeeName        string `json:"payeeName"`
	PayeeSortCode    string `json:"payeeSortCode"`
	PayeeAccount     string `json:"payeeAccount"`
	SettlementAmount string `json:"settlementAmount"`
	Currency         string `json:"currency"`
	ApprovedBy       string `json:"approvedBy"`
}

// ApprovedClaimConsumer reads claims.approved.v1 and hands each approval to PayoutService.Pay.
type ApprovedClaimConsumer struct {
	c     *kafka.Consumer
	topic string
	svc   *payout.Service
	log   *zap.Logger
}

func NewApprovedClaimConsumer(bootstrap, topic, group string, svc *payout.Service, log *zap.Logger) *ApprovedClaimConsumer {
	c, err := kafka.NewConsumer(&kafka.ConfigMap{
		"bootstrap.servers":  bootstrap,
		"group.id":           group,
		"enable.auto.commit": false,
		"auto.offset.reset":  "earliest",
	})
	if err != nil {
		log.Fatal("kafka consumer", zap.Error(err))
	}
	return &ApprovedClaimConsumer{c: c, topic: topic, svc: svc, log: log}
}

func (a *ApprovedClaimConsumer) Run(ctx context.Context) error {
	if err := a.c.SubscribeTopics([]string{a.topic}, nil); err != nil {
		return err
	}
	defer a.c.Close()
	for ctx.Err() == nil {
		msg, err := a.c.ReadMessage(500)
		if err != nil {
			continue
		}
		var evt ClaimApproved
		if err := json.Unmarshal(msg.Value, &evt); err != nil {
			a.log.Error("bad event, skipping", zap.Error(err))
			_, _ = a.c.CommitMessage(msg)
			continue
		}
		if err := a.svc.Pay(ctx, payout.Request{
			ClaimID: evt.ClaimID, ApprovalSeq: evt.ApprovalSeq, PayeeName: evt.PayeeName,
			SortCode: evt.PayeeSortCode, Account: evt.PayeeAccount, Amount: evt.SettlementAmount,
			Currency: evt.Currency,
		}); err != nil {
			// Not committed: the message is re-delivered after the breaker closes.
			a.log.Error("payout failed", zap.String("claim", evt.ClaimID), zap.Error(err))
			continue
		}
		_, _ = a.c.CommitMessage(msg)
	}
	return nil
}
'''

F[P + "internal/payout/service.go"] = '''package payout

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
'''

F[P + "internal/clearriver/client.go"] = '''package clearriver

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"time"
)

// Client calls the ClearRiver Bank Payouts API v2 (external, outside the Corvane boundary).
type Client struct {
	baseURL  string
	clientID string
	secret   string
	http     *http.Client
}

type PayoutRequest struct {
	Reference     string `json:"reference"`
	PayeeName     string `json:"payee_name"`
	SortCode      string `json:"sort_code"`
	AccountNumber string `json:"account_number"`
	Amount        string `json:"amount"`
	Currency      string `json:"currency"`
}

type PayoutResult struct {
	PayoutID string `json:"payout_id"`
	Status   string `json:"status"`
}

type permanentError struct{ msg string }

func (e permanentError) Error() string { return e.msg }

func IsPermanent(err error) bool { var p permanentError; return errors.As(err, &p) }

func New(baseURL, clientID, secret string, timeout time.Duration) *Client {
	return &Client{baseURL: baseURL, clientID: clientID, secret: secret, http: &http.Client{Timeout: timeout}}
}

func (c *Client) CreatePayout(ctx context.Context, p PayoutRequest, idempotencyKey string) (*PayoutResult, error) {
	body, _ := json.Marshal(p)
	req, _ := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/payouts", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Idempotency-Key", idempotencyKey)
	req.SetBasicAuth(c.clientID, c.secret)
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	switch {
	case resp.StatusCode == http.StatusCreated || resp.StatusCode == http.StatusOK:
		var out PayoutResult
		return &out, json.NewDecoder(resp.Body).Decode(&out)
	case resp.StatusCode == http.StatusUnprocessableEntity:
		return nil, permanentError{msg: "clearriver rejected payee details"}
	default:
		return nil, fmt.Errorf("clearriver status %d", resp.StatusCode)
	}
}
'''

F[P + "internal/store/store.go"] = '''package store

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
'''

F[P + "internal/publisher/publisher.go"] = '''package publisher

import (
	"context"
	"encoding/json"
	"time"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
)

// PaymentSettled mirrors contracts/avro/PaymentSettled.avsc; consumed by claims-service PaymentSettledListener.
type PaymentSettled struct {
	ClaimID    string    `json:"claimId"`
	PaymentRef string    `json:"paymentRef"`
	Amount     string    `json:"amount"`
	Currency   string    `json:"currency"`
	SettledAt  time.Time `json:"settledAt"`
}

type Publisher struct {
	p     *kafka.Producer
	topic string
}

func New(bootstrap, topic string) *Publisher {
	p, _ := kafka.NewProducer(&kafka.ConfigMap{"bootstrap.servers": bootstrap, "enable.idempotence": true, "acks": "all"})
	return &Publisher{p: p, topic: topic}
}

func (p *Publisher) Settled(ctx context.Context, e PaymentSettled) error {
	b, _ := json.Marshal(e)
	return p.p.Produce(&kafka.Message{TopicPartition: kafka.TopicPartition{Topic: &p.topic, Partition: kafka.PartitionAny},
		Key: []byte(e.ClaimID), Value: b}, nil)
}
'''

N = "services/notifications/"
F[N + "package.json"] = '''{
  "name": "@corvane/notifications",
  "version": "2.4.0",
  "private": true,
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc -p .",
    "start": "node dist/index.js",
    "test": "jest"
  },
  "dependencies": {
    "handlebars": "4.7.8",
    "kafkajs": "2.2.4",
    "nodemailer": "6.9.14",
    "undici": "6.19.2"
  },
  "devDependencies": {
    "@types/jest": "29.5.12",
    "@types/node": "20.14.9",
    "@types/nodemailer": "6.4.15",
    "jest": "29.7.0",
    "ts-jest": "29.1.5",
    "typescript": "5.5.2"
  }
}
'''

F[N + "tsconfig.json"] = '''{
  "compilerOptions": {
    "target": "ES2022", "module": "commonjs", "outDir": "dist", "rootDir": "src",
    "strict": true, "esModuleInterop": true
  },
  "include": ["src"]
}
'''

F[N + "Dockerfile"] = '''FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY dist ./dist
COPY src/templates ./dist/templates
USER node
EXPOSE 8070
CMD ["node", "dist/index.js"]
'''

F[N + "catalog-info.yaml"] = '''apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: notifications
  description: Emails and texts customers when claims are registered and policies are bound.
spec:
  type: service
  lifecycle: production
  owner: team-digital
  system: corvane-claims
  dependsOn: [resource:kafka-claims, resource:smtp-relay]
'''

F[N + "src/index.ts"] = '''import { Kafka } from "kafkajs";
import { ClaimRegisteredHandler } from "./handlers/claimRegisteredHandler";
import { PolicyBoundHandler } from "./handlers/policyBoundHandler";
import { Mailer } from "./channels/mailer";
import { SmsClient } from "./channels/smsClient";
import { config } from "./config";

async function main(): Promise<void> {
  const kafka = new Kafka({ clientId: "notifications", brokers: config.kafkaBrokers });
  const consumer = kafka.consumer({ groupId: "notifications" });
  const mailer = new Mailer(config.smtp);
  const sms = new SmsClient(config.smsUrl, config.smsApiKey);
  const handlers: Record<string, { handle(evt: any): Promise<void> }> = {
    "claims.registered.v1": new ClaimRegisteredHandler(mailer, sms),
    "policies.bound.v1": new PolicyBoundHandler(mailer),
  };
  await consumer.connect();
  await consumer.subscribe({ topics: Object.keys(handlers), fromBeginning: false });
  await consumer.run({
    eachMessage: async ({ topic, message }) => {
      const evt = JSON.parse(message.value?.toString() ?? "{}");
      await handlers[topic].handle(evt);
    },
  });
}

main().catch((err) => {
  console.error("notifications stopped", err);
  process.exit(1);
});
'''

F[N + "src/config.ts"] = '''export const config = {
  kafkaBrokers: (process.env.KAFKA_BOOTSTRAP ?? "kafka.corvane.internal:9092").split(","),
  smtp: {
    host: process.env.SMTP_HOST ?? "smtp.corvane.internal",
    port: Number(process.env.SMTP_PORT ?? 587),
    user: process.env.SMTP_USER ?? "notifications",
    password: process.env.SMTP_PASSWORD ?? "", // ${SMTP_PASSWORD}
    from: "Corvane Mutual Claims <claims@corvane.example>",
  },
  smsUrl: process.env.SMS_URL ?? "https://sms.textwave.example/v3/messages",
  smsApiKey: process.env.SMS_API_KEY ?? "", // ${SMS_API_KEY}
  portalUrl: process.env.PORTAL_URL ?? "https://my.corvane.example",
};
'''

F[N + "src/channels/mailer.ts"] = '''import nodemailer from "nodemailer";
import fs from "fs";
import path from "path";
import Handlebars from "handlebars";

export interface SmtpConfig { host: string; port: number; user: string; password: string; from: string }

export class Mailer {
  private transport;
  constructor(private cfg: SmtpConfig) {
    this.transport = nodemailer.createTransport({
      host: cfg.host, port: cfg.port, secure: false, requireTLS: true,
      auth: { user: cfg.user, pass: cfg.password },
    });
  }

  render(template: string, data: object): string {
    const file = path.join(__dirname, "..", "templates", `${template}.hbs`);
    return Handlebars.compile(fs.readFileSync(file, "utf8"))(data);
  }

  async send(to: string, subject: string, template: string, data: object): Promise<void> {
    await this.transport.sendMail({ from: this.cfg.from, to, subject, html: this.render(template, data) });
  }
}
'''

F[N + "src/channels/smsClient.ts"] = '''import { request } from "undici";

export class SmsClient {
  constructor(private url: string, private apiKey: string) {}

  async send(to: string, text: string): Promise<void> {
    const res = await request(this.url, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${this.apiKey}` },
      body: JSON.stringify({ to, text, sender: "CORVANE" }),
      headersTimeout: 3000,
    });
    if (res.statusCode >= 300) throw new Error(`sms failed: ${res.statusCode}`);
  }
}
'''

F[N + "src/handlers/claimRegisteredHandler.ts"] = '''import { Mailer } from "../channels/mailer";
import { SmsClient } from "../channels/smsClient";
import { config } from "../config";
import { lineName } from "../lines";

export interface ClaimRegistered {
  claimId: string; policyNumber: string; lineCode: string; claimantName: string;
  claimantEmail?: string; claimantMobile?: string; triageOutcome: "AUTO_APPROVED" | "ADJUSTER";
}

/** Last hop of journey J1 (FNOL): tells the customer their claim is registered. */
export class ClaimRegisteredHandler {
  constructor(private mailer: Mailer, private sms: SmsClient) {}

  async handle(evt: ClaimRegistered): Promise<void> {
    const data = {
      name: evt.claimantName, claimId: evt.claimId, line: lineName(evt.lineCode),
      autoApproved: evt.triageOutcome === "AUTO_APPROVED",
      trackUrl: `${config.portalUrl}/claims/${evt.claimId}`,
    };
    const template = `claim-registered-${evt.lineCode.toLowerCase()}`;
    if (evt.claimantEmail) {
      await this.mailer.send(evt.claimantEmail, `Your claim ${evt.claimId} is registered`, template, data);
    }
    if (evt.claimantMobile) {
      await this.sms.send(evt.claimantMobile, `Corvane: claim ${evt.claimId} registered. Track it at ${data.trackUrl}`);
    }
  }
}
'''

F[N + "src/handlers/policyBoundHandler.ts"] = '''import { Mailer } from "../channels/mailer";
import { lineName } from "../lines";

export interface PolicyBound { policyNumber: string; lineCode: string; holderName: string; holderEmail: string;
  annualPremium: string; currency: string; startDate: string }

export class PolicyBoundHandler {
  constructor(private mailer: Mailer) {}

  async handle(evt: PolicyBound): Promise<void> {
    await this.mailer.send(evt.holderEmail, `Welcome to Corvane: policy ${evt.policyNumber}`, "policy-welcome", {
      name: evt.holderName, policyNumber: evt.policyNumber, line: lineName(evt.lineCode),
      premium: `${evt.annualPremium} ${evt.currency}`, start: evt.startDate,
    });
  }
}
'''

F[N + "src/lines.ts"] = '''const NAMES: Record<string, string> = {
  MTR: "Motor", HOM: "Home buildings", CNT: "Home contents", TRV: "Travel", PET: "Pet", LLD: "Landlord",
  MAR: "Marine cargo", CPR: "Commercial property", PLB: "Public liability", PIN: "Professional indemnity",
  CYB: "Cyber", GDG: "Gadget",
};
export const lineName = (code: string): string => NAMES[code] ?? code;
'''

F[N + "src/templates/policy-welcome.hbs"] = '''<p>Dear {{name}},</p>
<p>Welcome to Corvane Mutual. Your {{line}} policy <strong>{{policyNumber}}</strong> starts on {{start}}.</p>
<p>Your annual premium is {{premium}}. You can see your documents at any time in My Corvane.</p>
<p>Corvane Mutual Insurance</p>
'''

F[N + "src/templates/.keep-empty.txt"] = ""

F[N + "test/claimRegisteredHandler.test.ts"] = '''import { ClaimRegisteredHandler } from "../src/handlers/claimRegisteredHandler";

test("emails and texts the claimant with the line-specific template", async () => {
  const mailer = { send: jest.fn().mockResolvedValue(undefined) } as any;
  const sms = { send: jest.fn().mockResolvedValue(undefined) } as any;
  await new ClaimRegisteredHandler(mailer, sms).handle({
    claimId: "CLM-1", policyNumber: "PET-9", lineCode: "PET", claimantName: "A Tester",
    claimantEmail: "a@example.test", claimantMobile: "+447700900000", triageOutcome: "ADJUSTER",
  });
  expect(mailer.send).toHaveBeenCalledWith("a@example.test", "Your claim CLM-1 is registered",
    "claim-registered-pet", expect.objectContaining({ line: "Pet", autoApproved: false }));
  expect(sms.send).toHaveBeenCalledTimes(1);
});
'''

for path, text in F.items():
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
print(f"wrote {len(F)} files")
