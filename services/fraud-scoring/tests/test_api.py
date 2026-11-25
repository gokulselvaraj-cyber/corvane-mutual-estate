from fastapi.testclient import TestClient

from corvane_fraud.app import app

client = TestClient(app)

BODY = {"claim_id": "CLM-1", "policy_number": "HOM-1", "line_code": "HOM", "loss_date": "2026-01-02",
        "reported_date": "2026-01-03", "policy_start_date": "2025-01-01", "claimed_amount": "900.10",
        "loss_cause": "ESCAPE_OF_WATER", "claimant": {"full_name": "A Tester"}}


def test_health():
    assert client.get("/health").json()["status"] == "UP"


def test_score_requires_token():
    assert client.post("/v1/score", json=BODY).status_code == 401


def test_rejects_unknown_line():
    r = client.post("/v1/score", json={**BODY, "line_code": "XXX"}, headers={"Authorization": "Bearer t"})
    assert r.status_code == 422
