# CLAUDE.md

Punto de entrada de contexto para Claude Code en este repositorio. Comparte propósito y reglas con `AGENTS.md` (instrucciones equivalentes para Codex). Mantener ambos archivos coherentes.

## Nombre funcional

**Plataforma de Gobierno del Dato**. La prueba ejecutada ante el tribunal se denomina **caso de uso de validación**. Evitar `PoC`, `MVP` y `demo` salvo como identificador técnico heredado (por ejemplo, el servicio Kubernetes `postgres-demo`).

## Qué es este proyecto

TFM de 6 ECTS centrado en gobierno de metadatos sobre OpenMetadata con conformidad DCAT-AP-ES y caso HVD activo. Trabaja sobre **metadatos**, no sobre datos de negocio. Capas técnicas reproducibles: PostgreSQL de referencia (`bronze/silver/gold`) ingerido en OpenMetadata, exportación JSON-LD DCAT-AP-ES y validación SHACL contra el bundle congelado en `tfm_ingestor/src/tfm_ingestor/resources/shacl`.

## Lectura mínima antes de actuar

1. `AGENTS.md`: principios de trabajo, terminología canónica, no-objetivos, higiene Git.
2. `docs/estructura_repositorio.md`: mapa del repo y nombres canónicos.
3. `docs/refactor_orquestacion_operativa.md`: arquitectura objetivo ya implantada (workflow Python canónico, CLI fino, scripts envoltorios, app web como cliente cerrado).
4. `docs/guia_centralizada.md`: orden operativo del flujo completo.
5. `docs/tfm_oficial_objetivos_decisiones.md`: alcance y decisiones académicas.
6. `docs/diagramas_mermaid.md`: diagramas reutilizables para memoria y defensa.

## Arquitectura en una frase

CLI fino (`om_dcat_sync`) y app web (`web/`) consumen una capa de servicios Python única (`workflow_service.py`, `governance_service.py`) que descubre activos en OpenMetadata, fusiona la curación funcional de `tfm_ingestor/config/gold_governance.csv` con los defaults globales y aplica gobierno, exportación DCAT-AP-ES y validación SHACL HVD de forma reproducible e idempotente.

## Puntos de entrada canónicos

- CLI principal: `python -m om_dcat_sync workflow run --dry-run`.
- Aplicación efectiva: `python -m om_dcat_sync workflow run --allow-warnings`.
- Alias legacy compatible: `python -m tfm_ingestor`.
- App web operativa: `cd web && npm install && npm run dev` (puerto 3000).
- Suite reproducible: `scripts/infra/run_validation_suite.ps1`.
- Tests: `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; python -m pytest`.

## Principios duros

- Simpleza primero. Edición quirúrgica. Solo tocar lo necesario para la petición.
- Una única lógica de negocio en Python. Ni la app web ni los scripts duplican reglas.
- Idempotencia obligatoria en cualquier script que toque OpenMetadata.
- Sin tokens en repo. Solo `GITHUB_TOKEN`/`GH_TOKEN` y `.env` cargado por `scripts/load_env.ps1`.
- No firmar commits, PRs ni contribuciones con nombres de agentes, bots o líneas `Co-authored-by` de agentes; GitHub debe reflejar solo la identidad Git configurada para `alonso.marcos@alu.uclm.es`.
- CKAN está descartado como flujo operativo. No reintroducirlo sin justificación explícita del usuario.

## No objetivos

Alta disponibilidad, hardening, SSO/LDAP, RBAC avanzado, backups productivos, observabilidad avanzada, escalado, harvesting CKAN activo.

## Para Claude Code en concreto

- Antes de cambios grandes, proponer plan y esperar confirmación.
- Para acciones destructivas (borrar archivos, reset de cluster, force-push), pedir confirmación incluso si el contexto sugiere autorización general.
- Respetar nomenclatura: documentación y UI en español; código, módulos, comandos y configuración técnica en inglés/snake_case.
- Antes de proponer comandos contra GitHub, comprobar que existe token en entorno; si no, dejar solo dry-run y explicar.
- Mantener `docs/tfe_ficha_oficial_uclm.txt` literal; existe test de integridad `test_official_tfe_file_is_unchanged`.

## Archivos congelados

- `docs/tfe_ficha_oficial_uclm.txt`: ficha oficial UCLM, literal.
- `tfm_ingestor/src/tfm_ingestor/resources/shacl/`: bundle SHACL congelado desde `datosgobes/DCAT-AP-ES/shacl/1.0.0` commit `f2c8a88868b89239c9f54bffdf621cded2401b9f`.
