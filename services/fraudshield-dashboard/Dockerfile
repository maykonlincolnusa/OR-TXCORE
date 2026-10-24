FROM python:3.12-slim
WORKDIR /srv
COPY pyproject.toml README.md ./
COPY dashboards ./dashboards
COPY models ./models
RUN pip install --no-cache-dir '.[dashboard]'
EXPOSE 8501
USER 65532:65532
CMD ["streamlit", "run", "dashboards/fraudshield_live.py", "--server.address=0.0.0.0"]
