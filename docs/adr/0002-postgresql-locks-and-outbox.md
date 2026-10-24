# ADR 0002 — PostgreSQL como fonte de verdade e transactional outbox

**Decisão:** saldos, idempotência, journal e evento são confirmados na mesma transação PostgreSQL; Redis nunca é fonte de integridade.

**Consequência:** consumers recebem at-least-once e precisam deduplicar. Não prometemos exactly-once distribuído.
