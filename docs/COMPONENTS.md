# Componentes e dependências

| Contexto | Responsabilidade | Depende de |
|---|---|---|
| Accounts | saldo disponível por moeda | PostgreSQL |
| Payments/Coordinator | estado, idempotência, locks e débito/crédito | Accounts, Fraud, Ledger |
| Ledger | journal imutável e duas entradas | Accounts, Payments |
| FraudShield | score determinístico explicável | configuração |
| Events | grava eventos na mesma transação | PostgreSQL |
| Audit | registra ação de posting | PostgreSQL |

Adapters externos (Redis, NATS, OTel) não são dependências do domínio. Redis será apenas cache/rate limit; NATS receberá eventos pelo worker do outbox.
