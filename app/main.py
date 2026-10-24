from uuid import UUID
from fastapi import Depends, FastAPI, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.errors import DomainError
from app.core.security import require_admin
from app.payments.models import Account, LedgerEntry, LedgerJournal, Payment, RiskAssessment
from app.payments.schemas import AccountCreate, BalanceCredit, TransferRequest
from app.payments.service import PaymentService

app = FastAPI(title="OR-TXCORE", version="0.1.0")

def account_view(account: Account) -> dict:
    return {"id": str(account.id), "currency": account.currency,
            "available_balance_minor": account.available_balance_minor, "status": account.status}

def payment_view(payment: Payment) -> dict:
    return {"id": str(payment.id), "source_account_id": str(payment.source_account_id),
            "destination_account_id": str(payment.destination_account_id), "amount_minor": payment.amount_minor,
            "currency": payment.currency, "status": payment.status, "risk_decision": payment.risk_decision,
            "correlation_id": str(payment.correlation_id)}

@app.exception_handler(DomainError)
def domain_error(_, error: DomainError): return JSONResponse(error.status_code, {"code": error.code, "detail": error.detail})

@app.get("/healthz")
def healthz(): return {"status": "ok"}

@app.get("/readyz")
def readyz(db: Session = Depends(get_db)):
    db.execute(select(1)); return {"status": "ready"}

@app.post("/v1/accounts", status_code=201)
def create_account(body: AccountCreate, db: Session = Depends(get_db)):
    account = Account(currency=body.currency); db.add(account); db.commit(); return account_view(account)

@app.post("/v1/accounts/{account_id}/test-credit")
def test_credit(account_id: UUID, body: BalanceCredit, _: None = Depends(require_admin), db: Session = Depends(get_db)):
    account = db.get(Account, account_id)
    if not account: raise HTTPException(404, "account not found")
    account.available_balance_minor += body.amount_minor; account.version += 1; db.commit(); return account_view(account)

@app.post("/v1/payments/transfers", status_code=201)
def transfer(body: TransferRequest, response: Response, idempotency_key: str = Header(..., alias="Idempotency-Key"), db: Session = Depends(get_db)):
    try:
        payment = PaymentService().transfer(db, body.model_dump(mode="json"), idempotency_key)
        db.commit()
    except Exception:
        db.rollback(); raise
    response.headers["Location"] = f"/v1/payments/{payment.id}"
    return payment_view(payment)

@app.get("/v1/payments/{payment_id}")
def get_payment(payment_id: UUID, db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if not payment: raise HTTPException(404, "payment not found")
    risk = db.scalar(select(RiskAssessment).where(RiskAssessment.payment_id == payment_id))
    return {"payment": payment_view(payment), "risk_assessment": {"score": risk.score, "decision": risk.decision,
            "reason_codes": risk.reason_codes} if risk else None}

@app.get("/v1/payments/{payment_id}/ledger")
def get_ledger(payment_id: UUID, db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if not payment: raise HTTPException(404, "payment not found")
    entries = db.scalars(select(LedgerEntry).join(LedgerJournal).where(LedgerJournal.payment_id == payment_id)).all()
    return [{"id": str(e.id), "account_id": str(e.account_id), "direction": e.direction,
             "amount_minor": e.amount_minor, "currency": e.currency} for e in entries]
