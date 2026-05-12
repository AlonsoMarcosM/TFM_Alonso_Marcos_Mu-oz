# Mapeo DCAT-AP-ES -> OpenMetadata

## Alcance funcional real

Este TFM trabaja sobre metadatos, no sobre datos de negocio.

- Las tablas del PostgreSQL de referencia se usan como soporte técnico para crear assets gobernables.
- La plataforma publica solo la capa `gold`.
- El objetivo es exportar un catálogo `DCAT-AP-ES` válido frente a SHACL.
- El caso activo del repositorio es `hvd`.
- La identidad del catálogo queda fijada como UCLM mediante `governance_defaults.yaml`.

Importante:

- `DCAT-AP` sigue siendo el marco oficial del TFM.
- `DCAT-AP-ES` es la concreción operativa aplicada en la plataforma.
- La activación HVD en esta plataforma es una hipótesis de diseño para ejercitar la extensión `HVD` con trazabilidad y validación reproducible.

Formulación defendible para memoria y tribunal: la plataforma genera un catálogo `JSON-LD` validado contra las shapes `DCAT-AP-ES` vendorizadas. Por tanto, la salida queda preparada para interoperabilidad y publicación en ecosistemas compatibles como `datos.gob.es`, pero el TFM no realiza una publicación efectiva ni certifica aceptación automática por parte de ese portal.

Desde el punto de vista RDF, el JSON-LD es una serialización del grafo de catálogo. En esta plataforma representa el catálogo de datos gobernados de la UCLM, construido desde activos técnicos conectados a OpenMetadata y completado con metadatos funcionales y defaults globales de gobierno.

## Referencia normativa

Fuentes oficiales:

- Perfil DCAT-AP-ES: `https://datosgobes.github.io/DCAT-AP-ES/`
- Relaciones del modelo: `https://datosgobes.github.io/DCAT-AP-ES/#dcat-ap-es-model-relations`
- Comparativa DCAT-AP -> DCAT-AP-ES: `https://datosgobes.github.io/DCAT-AP-ES/#annex-3-dcat-ap-to-dcat-ap-es`
- Validación: `https://datosgobes.github.io/DCAT-AP-ES/validation/`
- Convenciones: `https://datosgobes.github.io/DCAT-AP-ES/conventions/`

Implementación versionada en este repositorio:

- `tfm_ingestor/src/tfm_ingestor/resources/shacl/`
- `tfm_ingestor/src/tfm_ingestor/resources/shacl/manifest.json`
- `tfm_ingestor/src/tfm_ingestor/shacl_validation.py`

El directorio de shapes replica el árbol oficial `shacl/1.0.0` del repositorio `datosgobes/DCAT-AP-ES`, congelado en el commit `f2c8a88868b89239c9f54bffdf621cded2401b9f` con fecha `2026-04-13`. La validación en ejecución usa exclusivamente estos ficheros locales y no descarga shapes remotas.

## Clases activas en la plataforma

### `dcat:Catalog`

Se construye desde `tfm_ingestor/config/governance_defaults.yaml`. Ese fichero fija el catálogo UCLM: título, descripción, publicador, URI de organismo, página principal, taxonomía temática, idioma, licencia, legislación HVD, contacto y URLs base.

### `dcat:Dataset`

Se aproxima con entidades `Table/View` de OpenMetadata limitadas a la capa `gold`.

### `dcat:Distribution`

Se genera una distribución mínima por dataset a partir de `dcat_access_url`.

### `dcat:DataService`

Se deriva en la exportación JSON-LD a partir de defaults HVD del sistema.

### `foaf:Agent`

Se materializa a partir del publicador configurado del catálogo y del dataset.

## Contraste con una plataforma comercial

El artículo de Anjana Data sobre gobierno de datos abiertos conforme a `DCAT-AP-ES` se usa como benchmark de mercado. No sustituye a las fuentes normativas oficiales ni amplía el alcance técnico del TFM.

La lectura de negocio es relevante: la plataforma se apoya sobre OpenMetadata como herramienta base de gobierno del dato. En el estado actual del mercado no se ha identificado una extensión estándar ampliamente adoptada sobre OpenMetadata que cubra de forma nativa el cumplimiento operativo de `DCAT-AP-ES`. Ese hueco ayuda a explicar por qué existen productos y servicios especializados compitiendo en este terreno.

| Capacidad observada en una plataforma comercial | Cobertura en la Plataforma de Gobierno del Dato |
| --- | --- |
| Clases principales del perfil `DCAT-AP-ES` | Exporta `Catalog`, `Dataset`, `Distribution`, `DataService` y `Agent`. |
| Vocabularios controlados | Usa sectores NTI-RISP para `dcat:theme` y categorías superiores HVD controladas. |
| Datos de alto valor | Activa el caso `hvd` con `hvdCategory`, legislación aplicable, licencias y `DataService`. |
| Relaciones entre dataset, distribución y servicio | Conecta `Dataset`, `Distribution`, `accessService` y `servesDataset`. |
| Validación formal | Ejecuta validación SHACL local con shapes oficiales congeladas. |
| Exportación interoperable | Genera `JSON-LD` preparado para intercambio con catálogos compatibles. |
| Trazabilidad desde activo técnico | Parte de tablas reales descubiertas en OpenMetadata y gobierna solo la capa `gold`. |

Quedan fuera del alcance actual funciones propias de suites comerciales más amplias, como búsqueda editorial avanzada, flujos de aprobación, publicación automática en portales externos o gestión completa del ciclo de vida de catálogo.

Desde esa perspectiva, el TFM puede defenderse también como una solución de negocio: añade sobre OpenMetadata una capa específica de interoperabilidad, exportación y validación `DCAT-AP-ES` que no viene resuelta de forma nativa en la herramienta base.

## Matriz del modelo aplicado en la plataforma

La siguiente matriz resume el subconjunto que aplica hoy el repositorio. El objetivo de esta tabla es servir como referencia de implementación y como parte reutilizable de la memoria del TFM.

| Entidad | Metadato | Propiedad | T (DCAT-AP-ES) | DCAT-AP T | C (DCAT-AP-ES) | DCAT-AP C | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Catalog` | Nombre | `dct:title` | Obligatorio | Obligatorio | `1..n` | `1..n` | Activo en `governance_defaults.yaml`. |
| `Catalog` | Descripción | `dct:description` | Obligatorio | Obligatorio | `1..n` | `1..n` | Activo en `governance_defaults.yaml`. |
| `Catalog` | Órgano publicador | `dct:publisher` | Obligatorio | Obligatorio | `1..1` | `1..1` | Se exporta con URI DIR3-like y nodo `foaf:Agent`. |
| `Catalog` | Temática(s) | `dcat:themeTaxonomy` | Obligatorio | Recomendado | `1..3` | `0..n` | Se usa la taxonomía sectorial de `datos.gob.es`. |
| `Catalog` | Idioma(s) | `dct:language` | Obligatorio | Recomendado | `1..n` | `0..n` | Incluye español. |
| `Catalog` | Fecha de creación | `dct:issued` | Obligatorio | Recomendado | `1..1` | `0..1` | Elevada a obligatoria por DCAT-AP-ES. |
| `Catalog` | Fecha de actualización | `dct:modified` | Obligatorio | Recomendado | `1..1` | `0..1` | Elevada a obligatoria por DCAT-AP-ES. |
| `Catalog` | Página web | `foaf:homepage` | Obligatorio | Recomendado | `1..1` | `0..1` | Elevada a obligatoria por DCAT-AP-ES. |
| `Catalog` | Términos de uso | `dct:license` | Obligatorio | Recomendado | `1..1` | `0..1` | Se gobierna por configuración global, no por tabla. |
| `Dataset` | Nombre | `dct:title` | Obligatorio | Obligatorio | `1..n` | `1..n` | Sale de `displayName` o `name`. |
| `Dataset` | Descripción | `dct:description` | Obligatorio | Obligatorio | `1..n` | `1..n` | Sale de `description`. |
| `Dataset` | Publicador | `dct:publisher` | Obligatorio | Recomendado | `1..1` | `0..1` | Se apoya en `dcat_publisher_name` y `catalog.publisher_uri`. |
| `Dataset` | Temática(s) | `dcat:theme` | Obligatorio | Recomendado | `1..n` | `0..n` | Sale de tags `dcat_theme.*`. |
| `Dataset` | Distribución | `dcat:distribution` | `R / Ob (HVD)` | Recomendado | `0..n / 1..n (HVD)` | `0..n` | En la plataforma HVD activa se genera siempre una distribución. |
| `Dataset` | Categoría HVD | `dcatap:hvdCategory` | `Op / Ob (HVD)` | No existe | `0..n / 1..n (HVD)` | `-` | Se gobierna con `dcat_hvd_category`. |
| `Dataset` | Legislación aplicable | `dcatap:applicableLegislation` | `R / Ob (HVD)` | Opcional | `0..n / 1..n (HVD)` | `0..n` | Se deriva desde `hvd_defaults.applicable_legislation`. |
| `Distribution` | URL de acceso | `dcat:accessURL` | Obligatorio | Obligatorio | `1..n` | `1..n` | Se gobierna con `dcat_access_url`. |
| `Distribution` | Licencia | `dct:license` | `R / Ob (HVD)` | Recomendado | `0..1 / 1..1 (HVD)` | `0..1` | En la plataforma HVD se deriva desde `hvd_defaults.distribution_license`. |
| `Distribution` | Legislación aplicable | `dcatap:applicableLegislation` | `R / Ob (HVD)` | No existe | `0..n / 1..n (HVD)` | `-` | En la plataforma HVD se deriva desde defaults. |
| `Distribution` | Servicio de acceso | `dcat:accessService` | Opcional | Opcional | `0..n` | `0..n` | La plataforma lo activa para conectar la distribución con `DataService`. |
| `DataService` | Nombre | `dct:title` | Obligatorio | Obligatorio | `1..n` | `1..n` | Se deriva del título del dataset. |
| `DataService` | URL de acceso | `dcat:endpointURL` | Obligatorio | Obligatorio | `1..n` | `1..n` | Se deriva desde `hvd_defaults.service_endpoint_url_base`. |
| `DataService` | Temática(s) | `dcat:theme` | Obligatorio | Recomendado | `1..n` | `0..n` | Hereda la temática del dataset. |
| `DataService` | Publicador | `dct:publisher` | Obligatorio | No existe | `1..1` | `-` | DCAT-AP-ES incorpora la propiedad y la eleva a obligatoria. |
| `DataService` | Descripción del punto de acceso | `dcat:endpointDescription` | Recomendado | Recomendado | `0..n` | `0..n` | La plataforma lo deriva desde `hvd_defaults.service_endpoint_description_base`. |
| `DataService` | Categoría HVD | `dcatap:hvdCategory` | `Op / Ob (HVD)` | No existe | `0..n / 1..n (HVD)` | `-` | Se deriva del dataset. |
| `DataService` | Legislación aplicable | `dcatap:applicableLegislation` | `R / Ob (HVD)` | Opcional | `0..n / 1..n (HVD)` | `0..n` | Se deriva desde defaults HVD. |
| `DataService` | Punto de contacto | `dcat:contactPoint` | `R / Ob (HVD)` | `Op / Ob (HVD)` | `0..n / 1..n (HVD)` | `0..n / 1..n (HVD)` | La plataforma lo deriva desde `hvd_defaults.contact`. |
| `DataService` | Página de documentación | `foaf:page` | `Op / Ob (HVD por shapes oficiales)` | Opcional | `0..n / 1..n (HVD)` | `0..n` | La shape HVD lo eleva a `Violation`; la plataforma lo deriva por configuración. |
| `DataService` | Conjunto de datos servido | `dcat:servesDataset` | `R / Ob (HVD)` | `Op / Ob (HVD)` | `0..n / 1..n (HVD)` | `0..n / 1..n (HVD)` | La plataforma referencia explícitamente el dataset servido. |
| `DataService` | Información legal | `dct:license` / `dct:accessRights` | Obligatorio en la validación HVD | Opcional | `1..1` en alguno de los dos | `0..1` | La shape HVD exige aportar información legal; la plataforma exporta ambos. |
| `Agent` | Nombre | `foaf:name` | Obligatorio | Obligatorio | `1..n` | `1..n` | Se exporta en español. |

## Qué gobierna realmente OpenMetadata

En OpenMetadata solo se mantienen metadatos personalizados imprescindibles para no alargar artificialmente el modelo:

- `displayName`
- `description`
- `dcat_publisher_name`
- `dcat_hvd_category`
- `dcat_access_url`
- tags `dcat_theme.*`

## Qué deriva el sistema

El resto del perfil activo se deriva por configuración y exportación:

- `Catalog` completo desde `governance_defaults.yaml`, con UCLM como organismo publicador
- `dcatap:applicableLegislation` desde `hvd_defaults.applicable_legislation`
- licencia HVD y `accessRights`
- `DataService` completo
- `contactPoint`
- `endpointURL`
- `endpointDescription`
- `foaf:page`

## Qué aporta activar HVD

La activación HVD no se limita a añadir una etiqueta de clasificación. En el perfil activo de la plataforma implica:

- `dcatap:hvdCategory` en el dataset y en el servicio de datos.
- `dcatap:applicableLegislation` derivada para dataset, distribución y servicio.
- `dct:license` en la distribución y en el servicio.
- `dcat:DataService` como recurso explícito de acceso.
- `dcat:contactPoint` derivado desde la configuración global.
- `dct:accessRights` en el servicio.
- validación SHACL específica del caso `hvd`.

## Correspondencia OpenMetadata -> DCAT-AP-ES

- OpenMetadata `Table/View` -> `dcat:Dataset`
- custom property `dcat_access_url` -> `dcat:Distribution / dcat:accessURL`
- custom property `dcat_hvd_category` -> `dcatap:hvdCategory`
- custom property `dcat_publisher_name` -> `foaf:name` del publicador
- tags `dcat_theme.*` -> `dcat:theme`
- defaults del catálogo -> `dcat:Catalog`
- defaults HVD -> `dcat:DataService` y restricciones HVD derivadas

## Riesgos y limitaciones del mapeo

- `dcat:Dataset` no equivale semánticamente a una tabla SQL; en la plataforma se usa `Table/View` como aproximación técnica gobernable.
- La categoría HVD de `gold.agenda_cultural_publica` se usa como clasificación de validación para ejercitar la extensión HVD; no constituye una calificación jurídica automática fuera de la plataforma.
- La plataforma modela una única `Distribution` por dataset.
- El `DataService` exportado es metadata de acceso reproducible para la plataforma; no equivale a una API de explotación productiva completa.
- El pipeline gobierna metadatos, no profiling ni calidad del dato de negocio.

## Orden correcto del flujo

1. Ingesta técnica a OpenMetadata.
2. Curación funcional en `gold_governance.csv`.
3. Sincronización de obligatorios en OpenMetadata.
4. Exportación JSON-LD del catálogo.
5. Validación estructural con `validate-runtime`.
6. Validación SHACL con `validate-dcat --profile-case hvd`.

CKAN no forma parte del flujo operativo activo. Se ha descartado como origen canónico porque actúa como catálogo de metadatos ya publicados, mientras que esta plataforma necesita evidenciar captura y gobierno de metadatos desde activos técnicos reproducibles en OpenMetadata.

En la app web, `Workflow` agrupa la orquestación canónica: refresca hoja, planifica, aplica gobierno y, en la ejecución completa, exporta y valida. La pantalla `DCAT` permite repetir solo la exportación y la validación JSON-LD como evidencias independientes sin volver a aplicar metadatos sobre OpenMetadata.
