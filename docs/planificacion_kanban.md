# Planificación Del TFM

Enfoque: **Kanban** + hitos académicos. Es adecuado para un TFM individual de 6 ECTS, con alcance acotado y orientado a una PoC reproducible.

Alcance recordatorio:

- Se gobiernan **metadatos**, no datos de negocio.
- La PoC usa `DCAT-AP-ES` con el caso `hvd` activo para los datasets `gold`.
- El flujo técnico es ingesta -> enriquecimiento -> exportación -> validación.

## Metodología

- Método principal: Kanban.
- WIP: máximo 2-3 tareas simultáneas.
- Revisión: semanal o por cierre de fase.
- Herramienta: GitHub Projects v2.
- Objetivos oficiales y decisiones de alcance: `docs/tfm_oficial_objetivos_decisiones.md`.

## Estados

1. `Backlog`
2. `Por definir`
3. `En curso`
4. `Bloqueado`
5. `En revision`
6. `Hecho`

## Fases

1. `01_Planificacion`
2. `02_Modelo_DCAT-AP-ES`
3. `03_OpenMetadata_Config`
4. `04_Pipeline_Ingesta`
5. `05_Validacion`
6. `06_Memoria`

## Estado Actual

El estado canónico está en `scripts/planning/github_project_mvp.json`.

- `01_Planificacion`: `Hecho`
- `02_Modelo_DCAT-AP-ES`: `Hecho`
- `03_OpenMetadata_Config`: `Hecho`
- `04_Pipeline_Ingesta`: `Hecho`
- `05_Validacion`: `Hecho`
- `06_Memoria`: `Backlog`

Con este estado, la funcionalidad técnica de la PoC queda cerrada y la siguiente fase es redactar y consolidar la memoria.

## Backlog Maestro Por Fase

### 01_Planificacion

- Definir alcance, objetivos y no-objetivos del TFM.
- Definir tablero Kanban y criterios DoR/DoD.
- Configurar GitHub Project con vistas y campos.
- Definir métricas semanales e hitos académicos.
- Registrar riesgos iniciales y mitigaciones.

### 02_Modelo_DCAT-AP-ES

- Analizar `Catalog`, `Dataset`, `Distribution`, `DataService` y `Agent` en el perfil activo.
- Justificar la activación del caso `hvd` en la PoC.
- Cerrar decisiones de mapeo `DCAT-AP-ES` -> OpenMetadata.
- Definir el set mínimo de custom properties activas.
- Documentar limitaciones y riesgo controlado: `Dataset` DCAT frente a tabla SQL, HVD demo y `DataService` derivado.
- Justificar la exclusión de GeoDCAT-AP y HealthDCAT-AP.

### 03_OpenMetadata_Config

- Validar prerrequisitos del entorno.
- Desplegar stack OpenMetadata + dependencias en Kubernetes.
- Verificar acceso a UI y API.
- Crear tags y custom properties base para gobierno.
- Mantener configuración Helm declarativa para reducir drift.

### 04_Pipeline_Ingesta

- Desplegar PostgreSQL demo con capas `bronze`, `silver` y `gold`.
- Ejecutar ingesta técnica oficial hacia OpenMetadata.
- Ajustar `governance_defaults.yaml` y `mapping_rules.yaml`.
- Definir un contrato canónico de entrada de gobierno desacoplado del formato `CSV`.
- Separar adaptadores de entrada (`CSV`, `YAML`, `CKAN`, futura UI) del modelo interno.
- Extraer una capa de servicios para planificación, aplicación y exportación.
- Crear un workflow canónico único para CLI y ETL.
- Centralizar la configuración operativa con `operational_profile.yaml`.
- Ejecutar `python -m om_dcat_sync workflow run --dry-run` y después `python -m om_dcat_sync workflow run --allow-warnings`.
- Implementar harvesting desde CKAN.
- Exportar el catálogo a `DCAT-AP-ES` usando el perfil activo del repositorio.

### 05_Validacion

- Validar entidades técnicas creadas.
- Verificar metadatos de gobierno aplicados.
- Comprobar idempotencia en segunda ejecución.
- Validar harvesting, exportación JSON-LD y SHACL HVD.
- Ejecutar `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; python -m pytest`.
- Revisar higiene Git antes de push con `scripts/quality/pre_push_checks.ps1`.
- Evaluar beneficios y limitaciones.

### 06_Memoria

- Consolidar anexos técnicos reproducibles.
- Consolidar diagramas y figuras para defensa.
- Redactar resultados, limitaciones y trabajo futuro.
- Cerrar hitos y registrar avance final.
- Relacionar contribuciones con competencias `CN02` y `CP03`.
