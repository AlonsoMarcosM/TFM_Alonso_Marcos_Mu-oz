# AGENTS.md

Instrucciones para agentes (Codex) trabajando en este repositorio.

## Objetivo

TFM (6 ECTS). Prioridad absoluta: **simpleza**, coherencia y reproducibilidad.

Adicionalmente (para portfolio): intenta que todo lo que se haga sea **replicable** y facilmente **desplegable en un VPS o cloud**.
No es requisito imprescindible, pero guia las decisiones de arquitectura.

## Principios de arquitectura (portfolio-friendly)

- Infra declarativa y portable:
  - Kubernetes + Helm como via "canon" para OpenMetadata.
  - Docker Compose para la fuente dummy (local), sin acoplarla a rutas/hosts especificos.
- Config por YAML/env vars (sin hardcode):
  - URLs, tokens, credenciales -> variables de entorno/secretos.
- Idempotencia:
  - El script debe poder ejecutarse multiples veces sin duplicar tags/owners/asignaciones.
- Evidencias reproducibles:
  - Comandos copy/paste en `docs/`.
  - Tests minimos para reglas/mapeo/config.

## No-objetivos (trabajo futuro)

- Alta disponibilidad, hardening, NetworkPolicies, SSO/LDAP, RBAC avanzado, cifrado, backups, escalado, observabilidad avanzada, etc.

## Higiene Git (critico)

- Nunca subir documentacion/codigo corporativo:
  - `openmetadata_codigo/`, `OpenMetadata_documentacion/`, `TFM/` deben permanecer ignoradas por Git.
- Antes de cualquier `push`: ejecutar `pytest` y revisar `git status --ignored`.

