# Operação local de microsserviços

## Limites de consistência

`payment-core` mantém Accounts, Payments e Ledger no mesmo PostgreSQL e na mesma
transação. O `outbox-worker` publica somente após esse commit. A confirmação do
JetStream e a atualização do outbox não são uma transação distribuída: portanto,
a entrega é **at-least-once**. Um crash entre elas pode redeliver um envelope.

`audit-service` usa um armazenamento separado e sua chave única em `event_id`
torna a aplicação idempotente. Eventos repetidos são confirmados sem inserir uma
segunda trilha. Não há garantia de ordem global; a ordem prática é apenas a de
publicação por agregado e consumidores devem aceitar eventos atrasados. Falhas
persistentes devem ser encaminhadas para um consumidor/stream DLQ operacional,
após um número configurado de tentativas.

## Laboratório Kubernetes

Requer Docker, `kind`, `kubectl`, Helm e o metrics-server (o HPA só escala se as
métricas de recursos estiverem disponíveis). Execute `make kind-up`, `make deploy`,
`make status`, e `make port-forward`. O acesso inicial é somente por port-forward;
não há Ingress. PostgreSQL/PVC são exclusivos do laboratório; produção exige banco
gerenciado, backups, TLS, identidade de workload e um gestor de segredos.

## Observabilidade

Logs devem ser estruturados e sempre incluir `correlation_id`, nunca segredos ou
dados de cartão. Métricas a expor/alertar: pagamentos/segundo, p50/p95/p99,
outbox pendente/publicado, erros, REVIEW/DENY, locks/deadlocks e CPU/memória. A
instrumentação OpenTelemetry é preparada como preocupação de borda; não altera as
invariantes financeiras.

O `fraudshield-ml` carrega o artefato educacional público empacotado pelo painel
para `/v1/model-scores`; o caminho síncrono de pagamento usa regras determinísticas
e explicáveis até que exista um contrato de features transacionais compatível. Isso
evita aplicar silenciosamente um modelo treinado em outro esquema de dados.
