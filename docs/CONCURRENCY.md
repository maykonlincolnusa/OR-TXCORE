# Concorrência e consistência

O coordinator abre uma transação PostgreSQL, persiste/consulta a idempotência e bloqueia ambas contas com `SELECT ... FOR UPDATE`. Contas são selecionadas em ordem estável de UUID: transferências A→B e B→A não invertem a ordem dos locks. Não há mutex local nem dependência de Redis.

```mermaid
sequenceDiagram
 participant A as Transferência A
 participant P as PostgreSQL
 participant B as Transferência B
 A->>P: lock source,destination
 B->>P: aguarda source
 A->>P: saldo, journal, outbox, commit
 P-->>B: lock liberado
 B->>P: relê saldo e falha/posta
```

Use `READ COMMITTED` com locks pessimistas para saldo. Trate SQLSTATE `40P01` (deadlock) e `40001` (serialization failure) no adaptador HTTP/worker: retry limitado, com jitter exponencial, somente quando a operação for idempotente. A constraint única de idempotência cobre múltiplos processos; uma colisão durante insert retorna erro transitório de retry. Testes de contenção exigem PostgreSQL real, nunca SQLite.
