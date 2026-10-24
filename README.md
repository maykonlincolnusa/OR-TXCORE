# OR-TXCORE

Motor educacional de pagamentos simulados, ledger de partidas dobradas e inteligência antifraude. Não processa dinheiro, cartões ou credenciais reais.

## Executar

```bash
cp .env.example .env
docker compose up -d
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
```

No macOS/VS Code, abra esta pasta e selecione `.venv/bin/python`. Documentação interativa: `http://127.0.0.1:8000/docs`.

## Fluxo demonstrável

1. `POST /v1/accounts` cria duas contas fictícias.
2. `POST /v1/accounts/{id}/test-credit` com `X-Admin-Key` disponibiliza saldo de teste.
3. `POST /v1/payments/transfers` com `Idempotency-Key` transfere unidades mínimas inteiras.
4. `GET /v1/payments/{id}` e `/ledger` consultam pagamento, risco e lançamentos.

Execute `pytest`; a integração de concorrência requer `TEST_DATABASE_URL` PostgreSQL e é deliberadamente ignorada sem ele. Veja `docs/` para invariantes e operação.

## Command Center

O painel operacional está em `frontend/dist/`. É uma projeção visual simulada para demonstrar como operadores acompanham transações, fraude, invariantes e saúde de componentes. A evolução de serviços está em `docs/MICROSERVICE_EVOLUTION.md`; o painel nunca deve acessar o ledger para escrever dados.

## Microsserviços locais

O vertical slice executável é `payment-core` + `fraudshield-ml` + PostgreSQL;
`outbox-worker`, NATS JetStream e `audit-service` completam o fluxo assíncrono.
Use `docker compose up --build` para o laboratório Docker. Para kind, consulte
[`docs/OPERATIONS.md`](docs/OPERATIONS.md) e use os alvos do `Makefile`.
