# Segurança e threat model

O sistema é de simulação. A rota de crédito de teste exige `X-Admin-Key`; em produção, substitua por OIDC, RBAC (`operator`, `auditor`, `admin`), rotação de segredos e identidade de serviço. Segredos vêm do ambiente e não entram no repositório. Validação Pydantic limita valores e moeda; logs não devem conter cabeçalhos, chaves ou PII.

| Ameaça | Controle atual | Evolução |
|---|---|---|
| Replay/duplicidade | `Idempotency-Key` persistente e hash do payload | TTL/política de retenção |
| Abuso de API | limites de entrada | rate-limit Redis por principal/IP |
| Escalação de privilégio | key administrativa demo | OIDC/RBAC/auditoria de autorização |
| Double spending | locks PostgreSQL e saldo não negativo | retries classificados/monitoramento |
| Inconsistência contábil | journal + duas entries na mesma transação | triggers de imutabilidade/balanceamento |
| Evento falsificado | outbox interno | assinatura, ACL e credenciais NATS |

TLS, CORS restrito, limites de payload, observabilidade e alertas devem ser obrigatórios antes de exposição pública.
