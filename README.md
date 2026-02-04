# TFM — OpenMetadata + DCAT-AP-ES (PoC simple, consistente y gratuita)

Trabajo Fin de Master (6 ECTS).

**Titulo (ES):** Diseno y configuracion de un modelo de metadatos en OpenMetadata conforme al estandar DCAT-AP para la interoperabilidad de catalogos de datos.  
**Titulo (EN):** Design and Configuration of a Metadata Model in OpenMetadata According to the DCAT-AP Standard for Data Catalog Interoperability.

Idea guia: **lo minimo que funciona**, bien explicado y reproducible. Sin meterse en escalabilidad/resiliencia/seguridad (se documenta como trabajo futuro).

Nota (portfolio): se intenta que la solucion sea **replicable** y facilmente **desplegable en un VPS o cloud** (no es requisito imprescindible, pero guia la arquitectura).

## Alcance (MVP)

Lo que SI:
- Despliegue de OpenMetadata en Kubernetes local (Docker Desktop + Helm).
- Fuente tecnica dummy en PostgreSQL con esquemas `bronze/silver/gold` y datos inventados.
- Ingesta tecnica con conector oficial PostgreSQL (crea Service/Database/Schemas/Tables/Columns).
- Modelo de gobierno en OpenMetadata alineado con conceptos DCAT-AP-ES (dominios, owners, tags, custom properties).
- Enriquecimiento automatico via API REST de OpenMetadata (script Python `tfm_ingestor`), con reglas simples e idempotentes.
- Tests minimos con `pytest` para que cambios en reglas/mapeo no rompan el flujo.

Lo que NO (trabajo futuro):
- HA, hardening, RBAC avanzado, SSO/LDAP, cifrado, backups, escalado, observabilidad avanzada, etc.

## Idea clave (para evitar confusiones)

OpenMetadata **no ingesta DCAT-AP-ES de forma nativa** como "conector DCAT/CKAN" completo.
DCAT se **representa** mediante el metamodelo de OpenMetadata + gobierno (domains/tags/owners) + **custom properties**.

Flujo:
1) Ingesta tecnica (conector DB) -> entidades tecnicas automaticas.
2) Enriquecimiento (API OpenMetadata) -> metadatos de gobierno "DCAT-like".

## Estructura del repositorio

- `docs/`: documentacion tecnica (publicable).
- `sql/`: DDL + datos de ejemplo para PostgreSQL (fuente dummy).
- `docker-compose.yml`: arranque local de PostgreSQL (demo).
- `tfm_ingestor/`: script Python (CLI) para enriquecer metadatos via API OpenMetadata + tests.

Carpetas **privadas/locales** (NO publicables) que se mantienen en el repo pero **ignoradas por Git**:
- `openmetadata_codigo/`
- `OpenMetadata_documentacion/`
- `TFM/`

Si alguna vez se llegaran a "trackear" por error, hay que sacarlas del indice antes de hacer `push`:
`git rm -r --cached openmetadata_codigo OpenMetadata_documentacion TFM`

## Quickstart (resumen)

1) Desplegar OpenMetadata en Kubernetes local:
   - Ver `docs/openmetadata_k8s.md`

2) Levantar PostgreSQL dummy:
   - `docker compose up -d`
   - Ver `docs/postgres_demo.md`

3) Conectar PostgreSQL en OpenMetadata (UI) y ejecutar la ingesta tecnica:
   - Ver `docs/ingesta_tecnica_postgres.md`

4) Enriquecer metadatos de gobierno (API):
   - Ver `docs/tfm_ingestor.md`

Indice de documentacion: `docs/README.md`

## Referencias

- DCAT-AP-ES (norma principal del trabajo).
- OpenMetadata (despliegue en Kubernetes con Helm).
