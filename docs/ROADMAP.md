# Roadmap

1. **Foundation (atual):** transferências simuladas, ledger, risco determinístico, outbox e documentação.
2. **Hardening:** migrations SQL explícitas com triggers, worker NATS JetStream, Redis rate limit, OTel/metrics, RBAC/OIDC e testes de integração em CI.
3. **Operação:** resolução explícita de REVIEW, command/admin API, reconciliação, DLQ e painéis.
4. **Inteligência:** velocity/beneficiário novo/perfil, explicabilidade e avaliação de modelos offline.
5. **Extração:** event publisher, FraudShield e read models podem ser serviços; payment+ledger só se uma estratégia de consistência/Saga justificá-la.
