---
tipo: fuente
dominio: ia
estado: curado
origen: web
fuentes:
  - "01_raw/web/karpathy-llm-wiki-2026.md"
confianza: firme
actualizado: 2026-04-07
---

# Karpathy — LLM Wiki (2026)

## Referencia

Andrej Karpathy. `LLM Wiki` / idea file. Public gist, 4 April 2026.

## Resumen

Karpathy proposes a reusable pattern for building personal knowledge bases with LLMs. The core move is to separate immutable raw captures from a compiled wiki and from later outputs, so that knowledge can accumulate instead of being rediscovered at every query.

## Takeaways para Ateneo-KB

- The pattern `raw -> wiki -> outputs` is strong enough to be reused across domains.
- The architecture is intentionally abstract: each domain should adapt the workflow to its own epistemic needs.
- Sharing the pattern matters more than sharing one fixed application.

## Relación con Ateneo

Karpathy provides the architectural intuition. Ateneo-KB keeps that pattern but adds explicit editorial governance, confidence, and the distinction between evidence and interpretation.

## Conceptos vinculados

- [[criterio-vs-acceso]]
- [[gobernanza-editorial]]
