#!/usr/bin/env python3
"""Generate a small reproducible dataset; output is ignored by Git."""
import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.fraud.synthetic import as_rows

parser = argparse.ArgumentParser()
parser.add_argument("--rows", type=int, default=10_000)
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--output", default="data/generated/transfers.csv")
args = parser.parse_args()
rows = as_rows(args.seed, args.rows)
output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
with output.open("w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
print(f"wrote {len(rows)} synthetic transactions to {output}")
