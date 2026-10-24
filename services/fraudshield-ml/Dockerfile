FROM python:3.12-slim
WORKDIR /srv
COPY pyproject.toml README.md ./
COPY app ./app
COPY services ./services
COPY models ./models
RUN pip install --no-cache-dir '.[ml]'
EXPOSE 8001
USER 65532:65532
CMD ["uvicorn", "main:app", "--app-dir", "services/fraudshield-ml", "--host", "0.0.0.0", "--port", "8001"]
