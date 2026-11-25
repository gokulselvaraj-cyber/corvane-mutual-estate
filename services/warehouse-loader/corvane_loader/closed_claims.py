"""Consumes claims.closed.v1 and appends to dw.claim_closed_fact for loss-ratio reporting."""
import json
import logging

log = logging.getLogger("corvane_loader.closed_claims")

UPSERT = """INSERT INTO dw.claim_closed_fact (claim_id, policy_number, line_code, closed_on, paid_amount, reserve_released, currency)
VALUES (%(claimId)s, %(policyNumber)s, %(lineCode)s, %(closedOn)s, %(paidAmount)s, %(reserveReleased)s, %(currency)s)
ON CONFLICT (claim_id) DO UPDATE SET paid_amount = EXCLUDED.paid_amount, closed_on = EXCLUDED.closed_on"""


def run(cfg) -> None:
    from confluent_kafka import Consumer
    import psycopg
    c = Consumer({"bootstrap.servers": cfg["kafka"]["bootstrap"], "group.id": cfg["kafka"]["group"],
                  "enable.auto.commit": False})
    c.subscribe([cfg["kafka"]["closed_topic"]])
    with psycopg.connect(cfg["warehouse"]["dsn"]) as conn:
        while True:
            msg = c.poll(1.0)
            if msg is None or msg.error():
                continue
            conn.execute(UPSERT, json.loads(msg.value()))
            conn.commit()
            c.commit(msg)
