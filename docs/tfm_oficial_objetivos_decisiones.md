# TFM (oficial) - Objetivos, alcance y decisiones tecnicas

Este repositorio implementa una PoC reproducible (MVP) alrededor de OpenMetadata y DCAT-AP-ES, y mantiene trazabilidad
entre:
- enunciado/objetivos oficiales del TFM
- alcance real implementado en el repositorio
- decisiones tecnicas (y mitigacion de riesgos) tomadas para llegar a un resultado defendible en tiempo

## Ficha oficial del TFM (UCLM)

- Identificador: 29371
- Comision: E.Informatica-AB_CR-MUBDCN
- Area: Ingenieria y Arquitectura
- Tipo: Trabajo de fin de master
- Lugar: UCLM
- Idioma: castellano (realizacion y defensa)
- Fecha alta: 04/11/2025
- Vigencia maxima: 18/12/2027
- Tutor: Fernando Gualo Cejudo

Titulo (ES):
- DISEÑO Y CONFIGURACION DE UN MODELO DE METADATOS EN OPENMETADATA CONFORME AL ESTANDAR DCAT-AP-ES PARA LA INTEROPERABILIDAD DE CATALOGOS DE DATOS

Titulo (EN):
- Design and Configuration of a Metadata Model in OpenMetadata According to the DCAT-AP-ES Standard for Data Catalog Interoperability

## Descripcion oficial (resumen)

El TFM propone diseñar e implementar una configuracion de metadatos en OpenMetadata alineada con DCAT-AP-ES para mejorar la interoperabilidad de catalogos.
Incluye: analisis de clases DCAT-AP-ES (Dataset, Distribution, Catalog, Publisher, etc.), mapeo a entidades de OpenMetadata, configuracion de taxonomias y custom metadata,
pipeline de ingesta/sincronizacion (harvesting) desde una fuente externa (p.ej. CKAN), y validacion via exportacion/federacion en RDF, JSON-LD o equivalente.

## Objetivo general (oficial)

Diseñar y desplegar una configuracion de metadatos en OpenMetadata alineada con DCAT-AP-ES, para mejorar interoperabilidad y gestion semantica de catalogos
en entornos Big Data y cloud.

## Objetivos parciales (oficiales)

1. Analizar DCAT-AP-ES y extensiones (p.ej. DCAT-AP-ES for Health, GeoDCAT-AP-ES).
2. Mapear clases y propiedades DCAT-AP-ES con entidades equivalentes de OpenMetadata.
3. Configurar taxonomias, tipos personalizados y relaciones (custom metadata) en OpenMetadata para reflejar DCAT-AP-ES.
4. Implementar pipeline de ingesta/sincronizacion (harvesting) desde una fuente externa (p.ej. CKAN).
5. Validar mediante exportacion/federacion del catalogo en formato compatible con DCAT-AP-ES (RDF, JSON-LD o equivalente).
6. Evaluar beneficios y limitaciones en interoperabilidad, automatizacion y mantenimiento.

## Competencias (oficiales)

- CN02: arquitecturas para tratamiento masivo de datos + almacenamiento/orquestacion/pipelines.
- CP03: gobierno de datos y aseguramiento de calidad (integridad, seguridad, accesibilidad).

## Alcance real implementado en este repositorio (PoC)

Lo implementado hasta ahora prioriza simpleza, reproducibilidad e idempotencia:

- Despliegue reproducible de OpenMetadata en Kubernetes con Helm (stack unico).
- Fuente tecnica dummy PostgreSQL (capas `bronze/silver/gold`) dentro del mismo cluster.
- Ingesta tecnica oficial (service/db/schema/table/column) hacia OpenMetadata.
- Modelado DCAT-like mediante:
  - tags/clasificaciones
  - custom properties a nivel de `Table`
  - domains por convencion (PoC)
- Automatizacion idempotente via API (Python) con `tfm_ingestor` + configuracion YAML.
- Validacion minima con `pytest` centrada en reglas/config/higiene del repo.

## Alineacion objetivo -> evidencia (estado)

1) Analisis DCAT-AP-ES y extensiones
- Estado: Parcial
- Evidencia: `docs/dcat_mapping.md` (core) + tareas en GitHub Project.

2) Mapeo DCAT-AP-ES -> OpenMetadata
- Estado: Parcial/Hecho (para el subconjunto de la PoC)
- Evidencia: `docs/dcat_mapping.md`, `tfm_ingestor/config/mapping_rules.yaml`.

3) Taxonomias + custom metadata en OpenMetadata
- Estado: Hecho (MVP)
- Evidencia: `docs/custom_properties_openmetadata.md`, `scripts/infra/bootstrap_governance.py`.

4) Pipeline harvesting desde CKAN (u otra fuente externa)
- Estado: MVP implementado (pendiente de validar con un portal CKAN concreto)
- Evidencia: `tfm_ingestor/config/ckan_harvest.yaml`, `python -m tfm_ingestor harvest-ckan --dry-run`.

5) Exportacion/federacion DCAT-AP-ES (RDF/JSON-LD)
- Estado: MVP implementado (JSON-LD) (pendiente de validacion formal contra DCAT-AP-ES)
- Evidencia: `python -m tfm_ingestor export-dcat --output dcat_catalog.jsonld`.

6) Evaluacion de beneficios/limitaciones
- Estado: Parcial
- Evidencia: `docs/dcat_mapping.md`, `TFM/memoria_latex/sections/07_limitaciones_trabajo_futuro.tex`.

## Decisiones tecnicas y mitigacion de riesgos

Separar "objetivo oficial" de "decisiones tecnicas" ayuda a justificar por que el MVP es defendible y reproducible.

Decisiones clave:

- Kubernetes + Helm como via canon
  - Motivo: portabilidad (local/VPS/cloud) y practica alineada con industria/curriculum.
  - Riesgo: complejidad operativa.
  - Mitigacion: `kind` + scripts idempotentes + stack unico (sin HA/hardening).

- PostgreSQL dummy dentro del cluster
  - Motivo: dataset controlado y repetible para ingesta tecnica (reduce incertidumbre).
  - Riesgo: poca representatividad de un caso real.
  - Mitigacion: declarar limitacion y planificar validacion con ejemplo real como trabajo futuro.

- DCAT-AP-ES representado como metadatos de gobierno (tags + custom properties + domains)
  - Motivo: OpenMetadata no es DCAT 1:1; se evita intentar un conector completo en un TFM acotado.
  - Riesgo: confusion "dataset DCAT" vs "tabla SQL".
  - Mitigacion: documentar el trade-off (riesgo controlado) y mantener trazabilidad de decisiones.

- Configuracion por YAML/env vars (sin hardcode) + tests minimos
  - Motivo: reproducibilidad y facilidad de evolucion.
  - Riesgo: drift/errores de reglas.
  - Mitigacion: validaciones, dry-run y tests sobre config/reglas.

- GitHub Projects para planificacion
  - Motivo: trazabilidad dentro del repo y automatizacion por codigo (portfolio).
  - Riesgo: duplicados/ruido si se re-ejecuta.
  - Mitigacion: script idempotente + comandos de limpieza controlados.

## Notas de refactor pendiente

Si se detecta desviacion entre "oficial" y "alcance real", se debe:
- reflejarlo en la memoria como limitacion/trabajo futuro (no ocultarlo)
