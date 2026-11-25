package publisher

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
