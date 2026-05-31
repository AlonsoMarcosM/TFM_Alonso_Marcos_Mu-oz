# Estructura y nomenclatura del repositorio

## Objetivo

Este documento fija cómo leer el repositorio y qué nombres se consideran canónicos. La prioridad es que el proyecto sea simple, reproducible y defendible como TFM, sin renombrar piezas técnicas que ya están integradas en comandos, tests y documentación.

## Criterio de nomenclatura

Regla general:

- documentación y textos de interfaz en español;
- nombres de paquetes, módulos, comandos, variables de entorno y ficheros de configuración técnica en inglés o snake_case cuando forman parte de convenciones de Python, Node, OpenMetadata, DCAT o Kubernetes;
- aliases legacy conservados solo para compatibilidad, no como vía recomendada.

Esta mezcla es intencional. Renombrar ahora `tfm_ingestor`, `om_dcat_sync`, los YAML de configuración o los comandos del CLI aportaría poca claridad y rompería demasiadas referencias operativas.

## Nombres canónicos

| Elemento | Nombre canónico | Motivo |
| --- | --- | --- |
| CLI principal | `python -m om_dcat_sync ...` | Describe la sincronización OpenMetadata/DCAT y es el punto de entrada recomendado. |
| Paquete Python | `tfm_ingestor` | Nombre histórico del paquete; se conserva por compatibilidad de imports y distribución editable. |
| Alias legacy | `python -m tfm_ingestor ...` | Se mantiene para no romper ejecuciones anteriores. No es la vía recomendada en documentación nueva. |
| App web | `web/` | Convención clara para una aplicación Next.js autocontenida. |
| Infraestructura | `scripts/infra/` | Scripts operativos de despliegue, ingesta y validación viva. |
| Planificación | `scripts/planning/` | Automatización de GitHub Project y roadmap. |
| Calidad | `scripts/quality/` | Chequeos reproducibles antes de push. |
| Documentación | `docs/` | Fuente principal para memoria, defensa y operación. |
| Anexos replicables | `docs/anexos_instalacion/` | Pasos de instalación orientados a memoria y evidencia. |
| Kubernetes | `k8s/` | Values Helm y configuración declarativa de despliegue. |
| SQL de referencia | `sql/` | Fuente reproducible de los esquemas `bronze`, `silver` y `gold`. |

## Configuración principal

Los ficheros siguientes no se renombran porque están integrados en CLI, scripts, tests y documentación:

| Fichero | Papel |
| --- | --- |
| `tfm_ingestor/config/operational_profile.yaml` | Perfil operativo del workflow canónico. |
| `tfm_ingestor/config/governance_defaults.yaml` | Defaults globales de catálogo, HVD, licencias y servicios. |
| `tfm_ingestor/config/mapping_rules.yaml` | Reglas de selección, tags y mapeo sobre tablas OpenMetadata. |
| `tfm_ingestor/config/gold_governance.csv` | Hoja funcional editable por persona responsable del catálogo. |

En documentación en español se debe explicar su función, no traducir su nombre de fichero.

## Estructura publicable y no publicable

Directorios versionables:

- `docs/`
- `k8s/`
- `scripts/`
- `sql/`
- `tfm_ingestor/`
- `web/`

Directorios locales o generados que no deben subirse:

- `.env`
- `.pytest_cache/`
- `.pytest_tmp/`
- `.tools/`
- `data_local/`
- `docs_private/`
- `openmetadata_codigo/`
- `state/`
- `tmp_pytest/`
- `TFM/`
- `web/.next/`
- `web/node_modules/`
- `*.tsbuildinfo`

## Rutas que no se deben modificar

- `docs/tfe_ficha_oficial_uclm.txt`: copia literal congelada de la ficha oficial UCLM.
- `tfm_ingestor/src/tfm_ingestor/resources/shacl/`: bundle SHACL local congelado desde el repositorio oficial `datosgobes/DCAT-AP-ES`.

## Reglas para nuevos nombres

Para documentación nueva:

- usar español claro y descriptivo;
- mantener snake_case en nombres de archivo;
- evitar abreviaturas que no estén ya asentadas en el TFM;
- preferir `validacion`, `gobierno`, `ingesta`, `infraestructura`, `estructura`, `planificacion` frente a nombres genéricos.

Para código y configuración técnica:

- usar inglés técnico cuando el ecosistema lo espere (`workflow`, `runtime`, `export`, `validate`, `governance`, `mapping`);
- mantener comandos estables antes que traducirlos;
- si se añade un alias en español, documentarlo como capa de comodidad, no como sustitución del contrato técnico.

## Decisión actual de no renombrar

Tras revisar `docs/tfm_ingestor.md` y `docs/tfm_oficial_objetivos_decisiones.md`, no se cambia la estructura principal ni los nombres técnicos canónicos. El proyecto ya cumple mejor con reproducibilidad y legibilidad manteniendo:

- `om_dcat_sync` como CLI recomendado;
- `tfm_ingestor` como paquete Python y alias legacy;
- `web/` como app operativa;
- `docs/` como fuente de explicación en español;
- scripts PowerShell como envoltorios finos de operación.

Los cambios adecuados en esta fase son documentales y de higiene: explicar nombres, mantener textos visibles en español, ignorar artefactos generados y evitar introducir rutas paralelas.
