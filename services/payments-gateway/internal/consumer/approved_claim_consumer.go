package consumer

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
