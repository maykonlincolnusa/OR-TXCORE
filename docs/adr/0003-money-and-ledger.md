# ADR 0003 — Valores inteiros e ledger imutável

**Decisão:** dinheiro é inteiro em unidade mínima mais moeda explícita; pagamentos postados geram débito/crédito de mesmo valor em journal.

**Consequência:** evita arredondamento binário e permite auditoria/reconciliação. Estornos futuros serão novos journals, não alteração de entries.
