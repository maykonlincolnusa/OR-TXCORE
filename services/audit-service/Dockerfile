FROM python:3.12-slim
WORKDIR /srv
COPY pyproject.toml README.md ./
COPY app ./app
COPY services ./services
RUN pip install --no-cache-dir .
EXPOSE 8002
USER 65532:65532
CMD ["uvicorn", "main:app", "--app-dir", "services/audit-service", "--host", "0.0.0.0", "--port", "8002"]
