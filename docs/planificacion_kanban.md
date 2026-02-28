# Planificación del TFM (enfoque agil ligero)

Enfoque: **Kanban** + hitos académicos. Adecuado para un TFM individual con alcance acotado y orientado a portfolio.

## Metodologia

- Método principal: Kanban (flujo continuo).
- WIP: máximo 2-3 tareas simultaneas.
- Revisiones: semanal (actualizar tablero antes de cada reunion/hito).
- Herramienta sugerida: GitHub Projects (v2) para trazabilidad dentro del repositorio.
- Objetivos oficiales + alcance real: `docs/tfm_oficial_objetivos_decisiones.md`.

## Tablero Kanban (columnas)

1. Backlog (tareas identificadas)
2. Por definir (pendiente de decisión del tutor)
3. En curso (tareas activas)
4. Bloqueado (dependencias externas)
5. En revisión (validación técnica / revisión del tutor)
6. Hecho (cerrado y documentado)

## Tipos de tarjetas

- Diseño
- Implementación
- Validación
- Documentación
- Riesgo

## Orden canonico de fases (fuente para GitHub Projects)

Este es el orden total acordado para el TFM:

1. `01_Planificacion`
2. `02_Modelo_DCAT-AP`
3. `03_OpenMetadata_Config`
4. `04_Pipeline_Ingesta`
5. `05_Validacion`
6. `06_Memoria`

## Backlog maestro por fase

### 01_Planificacion

- Definir alcance, objetivos y no-objetivos del TFM.
- Definir tablero Kanban, WIP y criterios DoR/DoD.
- Configurar GitHub Project con vistas y campos.
- Definir métricas semanales e hitos académicos.
- Registrar riesgos iniciales y mitigaciones.

### 02_Modelo_DCAT-AP

- Analizar clases DCAT-AP-ES para la PoC (`Catalog`, `Dataset`, `Distribution`, `DataService`).
- Cerrar decisiones de mapeo DCAT-AP-ES -> OpenMetadata.
- Definir set mínimo de propiedades DCAT-like.
- Documentar limitaciones y riesgo controlado (dataset DCAT vs tabla SQL).

### 03_OpenMetadata_Config

- Validar prerrequisitos del entorno (`docker`, `kubectl`, `kind`, `helm`, `python`).
- Desplegar stack OpenMetadata + dependencias en Kubernetes.
- Verificar estado de pods/servicios y acceso a UI.
- Crear tags y custom properties base para gobierno.

### 04_Pipeline_Ingesta

- Desplegar PostgreSQL dummy (`bronze/silver/gold`).
- Ejecutar ingesta técnica oficial hacia OpenMetadata.
- Ajustar `governance_defaults.yaml` y `mapping_rules.yaml`.
- Ejecutar `tfm_ingestor --dry-run` y después aplicación real.
- Implementar harvesting desde CKAN (prioridad MITECO, fallback datos.gob.es) con límite configurable (MVP: 10 datasets).
- Exportar/federar el catálogo a DCAT-AP (JSON-LD) usando un subconjunto mínimo alineado con propiedades obligatorias DCAT-AP-ES.

### 05_Validacion

- Validar entidades técnicas creadas (service/db/schema/table/column).
- Verificar enrichment (tags, domains, custom properties).
- Comprobar idempotencia en segunda ejecución.
- Validar harvesting (CKAN -> custom properties/tags) y export DCAT (JSON-LD) con ejemplos reales.
- Ejecutar `pytest` y revisar higiene Git antes de push.
- Evaluar beneficios y limitaciones (interoperabilidad, automatizacion, mantenimiento).

### 06_Memoria

- Consolidar anexos tecnicos reproducibles.
- Consolidar diagramas y figuras para defensa.
- Redactar resultados, limitaciones y trabajo futuro.
- Cerrar hitos y registrar avance final.

## Estructura sugerida de evidencias

- `01_Planificacion` (roadmap, tablero, actas)
- `02_Modelo_DCAT-AP` (análisis del estándar)
- `03_OpenMetadata_Config` (configuración y custom metadata)
- `04_Pipeline_Ingesta` (desarrollo del codigo)
- `05_Validacion` (pruebas y evidencias)
- `06_Memoria` (documento final)

## Métricas simples

- Numero de tareas completadas por semana
- Porcentaje de avance por hito
- Numero de bloqueos abiertos por semana
