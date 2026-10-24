# Dataset policy

The repository contains no downloaded datasets, customer data, secrets, or model weights.

Initial external benchmark: [`MaxPrestige/credit-card-fraud-CLEAN`](https://huggingface.co/datasets/MaxPrestige/credit-card-fraud-CLEAN), about 71 MB. Its card lists educational/research use but an `other` license; use it locally only after reviewing upstream terms, never commit or redistribute it. It is a benchmark, not a production event schema; store it outside Git under `data/external/`.

The canonical local source is `scripts/generate_synthetic_data.py`. It emits deterministic, fake transfers with controlled velocity, device, country-change and fraud labels. This enables reproducible concurrency/risk experiments while preserving privacy.

Never mix benchmark labels into online decisions, train on sensitive attributes, or commit downloaded data. Model artifacts must record dataset/version/hash, feature schema, metrics and decision threshold.
