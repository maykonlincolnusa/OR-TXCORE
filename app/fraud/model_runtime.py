"""Local, bounded model adapter. It is never an authority over ledger invariants."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelScore:
    probability: float
    model_version: str
    feature_schema_version: int


class LocalRiskModel:
    def __init__(self, artifact_path: str):
        self.artifact_path = Path(artifact_path)

    def score(self, features: dict[str, Any]) -> ModelScore:
        try:
            import joblib
            import pandas as pd
        except ImportError as error:
            raise RuntimeError("install optional dependency: pip install -e '.[ml]'") from error
        artifact = joblib.load(self.artifact_path)
        vector = pd.DataFrame([{name: features[name] for name in artifact["feature_names"]}])
        probability = float(artifact["pipeline"].predict_proba(vector)[0][1])
        return ModelScore(probability, artifact["model_version"], artifact["feature_schema_version"])
