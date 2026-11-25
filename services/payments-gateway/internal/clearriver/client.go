package clearriver

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
