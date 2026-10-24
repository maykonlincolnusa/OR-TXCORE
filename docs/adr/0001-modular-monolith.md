# ADR 0001 — Modular monolith primeiro

**Decisão:** iniciar em um deploy com módulos e interfaces explícitas.

**Motivo:** pagamentos e ledger compartilham invariantes ACID. Microsserviços prematuros aumentariam latência, sagas e superfície de falha sem validação de produto. Eventos/outbox preservam caminho de extração.
