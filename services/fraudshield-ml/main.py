import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.fraud.service import DeterministicFraudEngine

app = FastAPI(title="FraudShield ML", version="1.0.0")
engine = DeterministicFraudEngine()
MODEL_DIR = Path("models/credit-card-fraud")

class AssessmentRequest(BaseModel):
    amount_minor: int = Field(gt=0, le=100_000_000)

class ULBFeatures(BaseModel):
    """The 30 numeric features of the public Hugging Face/U LB educational model."""
    values: list[float] = Field(min_length=30, max_length=30)

def load_hf_artifact():
    """Lazy loading keeps health checks independent from inference warm-up."""
    try:
        import joblib
        config = json.loads((MODEL_DIR / "config.json").read_text())
        return joblib.load(MODEL_DIR / "model.joblib"), config
    except Exception as error:
        raise HTTPException(503, "Hugging Face model artifact unavailable") from error

@app.get("/healthz")
def healthz(): return {"status": "ok", "model_artifact_present": (MODEL_DIR / "model.joblib").exists()}

@app.get("/readyz")
def readyz(): return {"status": "ready"}

@app.post("/v1/assessments")
def assess(body: AssessmentRequest):
    """Deterministic guardrails are authoritative; model evidence is additive."""
    decision = engine.assess(body.amount_minor)
    return {"score": decision.score, "decision": decision.decision,
            "reason_codes": decision.reason_codes, "model_version": "policy-v1"}

@app.post("/v1/model-scores")
def model_score(body: ULBFeatures):
    """Batch/analyst inference for the packaged public Hugging Face artifact."""
    model, config = load_hf_artifact()
    score = float(model.predict_proba([body.values])[0][1])
    threshold = float(config["models"][config["best"]]["threshold"])
    return {"score": score, "decision": "REVIEW" if score >= threshold else "ALLOW",
            "reason_codes": ["HF_MODEL_THRESHOLD"] if score >= threshold else [],
            "model_version": config["best"]}
