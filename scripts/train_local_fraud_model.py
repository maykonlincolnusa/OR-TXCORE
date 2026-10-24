#!/usr/bin/env python3
"""Train a local baseline on an externally acquired educational dataset.

This script intentionally excludes `gender` and `state`; location/identity proxies
need a documented fairness review before any production use.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

parser = argparse.ArgumentParser()
parser.add_argument("--dataset", default="data/external/credit-card-fraud-CLEAN.csv")
parser.add_argument("--output", default="models/local-fraud-baseline.joblib")
args = parser.parse_args()
UTC = timezone.utc

try:
    import joblib
    import pandas as pd
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
except ImportError as error:
    raise SystemExit("Install ML extras first: pip install -e '.[ml]'") from error

features = ["category", "amt", "city_pop", "lat", "long", "merch_lat", "merch_long"]
frame = pd.read_csv(args.dataset, usecols=features + ["is_fraud"])
X_train, X_test, y_train, y_test = train_test_split(frame[features], frame["is_fraud"].astype(int),
    test_size=.2, random_state=42, stratify=frame["is_fraud"])
pipeline = Pipeline([("imputer", ColumnTransformer([("numeric", SimpleImputer(strategy="median"), features)])),
    ("model", HistGradientBoostingClassifier(max_iter=200, learning_rate=.08, max_leaf_nodes=31,
                                                l2_regularization=1.0, random_state=42))])
pipeline.fit(X_train, y_train)
probability = pipeline.predict_proba(X_test)[:, 1]
precision, recall, thresholds = precision_recall_curve(y_test, probability)
eligible = [index for index, value in enumerate(precision[:-1]) if value >= .20]
threshold = float(thresholds[eligible[-1]]) if eligible else .5
metrics = {"roc_auc": float(roc_auc_score(y_test, probability)), "average_precision": float(average_precision_score(y_test, probability)),
           "review_threshold": threshold, "test_rows": int(len(y_test)), "positive_rate": float(y_test.mean())}
artifact = {"pipeline": pipeline, "feature_names": features, "feature_schema_version": 1,
            "model_version": datetime.now(UTC).strftime("local-hgb-%Y%m%dT%H%M%SZ"), "metrics": metrics}
output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True); joblib.dump(artifact, output)
output.with_suffix(".metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps({"artifact": str(output), **metrics}, indent=2))
