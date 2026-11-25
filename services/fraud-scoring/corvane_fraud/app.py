"""FastAPI app: POST /v1/score is called by claims-service FraudScoringClient during FNOL."""
from fastapi import Depends, FastAPI, Header, HTTPException

from .engine import ScoringEngine
from .llm_triage import LlmTriageClient
from .models import ScoreRequest, ScoreResponse
from .settings import settings
from .store import ScoreStore

app = FastAPI(title="Corvane fraud-scoring", version="1.9.2")
_engine: ScoringEngine | None = None
_store = ScoreStore(settings.db_dsn)


def engine() -> ScoringEngine:
    global _engine
    if _engine is None:
        _engine = ScoringEngine(LlmTriageClient() if settings.llm_triage_enabled else None)
    return _engine


def require_service_token(authorization: str = Header(default="")) -> None:
    # Service-to-service: claims-service relays its workload identity token (audience fraud-scoring).
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")


@app.get("/health")
def health() -> dict:
    return {"status": "UP", "llm_triage": settings.llm_triage_enabled}


@app.post("/v1/score", response_model=ScoreResponse, dependencies=[Depends(require_service_token)])
async def score(req: ScoreRequest, eng: ScoringEngine = Depends(engine)) -> ScoreResponse:
    result = await eng.score(req)
    _store.save(result)
    return result
