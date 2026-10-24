"""Idempotent JetStream consumer plus minimal health endpoint."""
import asyncio
import os
from uuid import UUID
import nats
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from app.audit.models import AuditBase, AuditRecord

app = FastAPI(title="OR-TXCORE Audit Service", version="1.0.0")
DATABASE_URL = os.getenv("AUDIT_DATABASE_URL", "postgresql+psycopg://ortxcore:ortxcore@postgres:5432/ortxcore_audit")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(engine)

@app.on_event("startup")
async def start_consumer():
    AuditBase.metadata.create_all(engine)
    app.state.task = asyncio.create_task(consume())

@app.on_event("shutdown")
async def stop_consumer():
    app.state.task.cancel()

@app.get("/healthz")
def healthz(): return {"status": "ok"}
@app.get("/readyz")
def readyz():
    with engine.connect() as connection: connection.exec_driver_sql("SELECT 1")
    return {"status": "ready"}

async def consume():
    nc = await nats.connect(os.getenv("NATS_URL", "nats://nats:4222"))
    js = nc.jetstream()
    await js.add_stream(name="PAYMENTS", subjects=["payment.*", "ledger.*"])
    sub = await js.subscribe("payment.*", durable="audit-service", stream="PAYMENTS")
    while True:
        messages = await sub.fetch(10, timeout=1)
        for message in messages:
            payload = message.json()
            try:
                with Session.begin() as db:
                    db.add(AuditRecord(event_id=UUID(payload["event_id"]), event_type=payload["event_type"],
                        aggregate_id=UUID(payload["aggregate_id"]), correlation_id=UUID(payload["correlation_id"]), envelope=payload))
                await message.ack()
            except IntegrityError:  # already committed: safe redelivery acknowledgement
                await message.ack()
