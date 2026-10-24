FROM python:3.12-slim
WORKDIR /srv
COPY pyproject.toml README.md ./
COPY app ./app
COPY services ./services
RUN pip install --no-cache-dir .
USER 65532:65532
CMD ["python", "services/outbox-worker/main.py"]
