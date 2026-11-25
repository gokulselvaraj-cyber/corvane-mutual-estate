"""Runtime settings for fraud-scoring.

Values come from the environment so the same image runs in dev, test and prod. Thresholds are kept here
(not in config maps) because the model was calibrated against them; change them only with a new
calibration report from Fraud Analytics.
"""
import os
from dataclasses import dataclass, field

# Score at or above which a claim is referred to the counter-fraud team (status REFER).
# Calibrated Feb 2026 on 41k closed claims: precision 0.61 / recall 0.78 at this cut.
REFER_THRESHOLD = 0.72

# Score at or above which payment is held for a claims manager (status HOLD).
DECLINE_THRESHOLD = 0.91

# Weight of the LLM triage label in the final score (0 disables its influence without disabling the call).
LLM_WEIGHT = 0.15

# Maximum characters of narrative + injury notes sent to the AI gateway.
LLM_MAX_CHARS = 6000


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    env: str = field(default_factory=lambda: os.getenv("CORVANE_ENV", "dev"))
    # Feature flag fraud.llm-triage.enabled (env FRAUD_LLM_TRIAGE_ENABLED). On in prod since 2026-03.
    llm_triage_enabled: bool = field(default_factory=lambda: _flag("FRAUD_LLM_TRIAGE_ENABLED"))
    ai_gateway_url: str = field(
        default_factory=lambda: os.getenv("AI_GATEWAY_URL", "https://ai-gateway.corvane.internal/v1/chat"))
    ai_gateway_token: str = field(default_factory=lambda: os.getenv("AI_GATEWAY_TOKEN", ""))  # ${AI_GATEWAY_TOKEN}
    ai_model: str = field(default_factory=lambda: os.getenv("AI_MODEL", "corvane-triage-large"))
    ai_timeout_s: float = field(default_factory=lambda: float(os.getenv("AI_TIMEOUT_S", "8")))
    kafka_bootstrap: str = field(default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP", "kafka.corvane.internal:9092"))
    registered_topic: str = "claims.registered.v1"
    consumer_group: str = "fraud-scoring"
    db_dsn: str = field(default_factory=lambda: os.getenv("CLAIMSDB_DSN", "postgresql://fraud@claimsdb:5432/claimsdb"))
    prompt_dir: str = field(default_factory=lambda: os.getenv("PROMPT_DIR", "prompts"))


settings = Settings()
