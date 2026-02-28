# Mapeo DCAT-AP-ES -> OpenMetadata (versión simple)

Nota de alineacion: DCAT-AP-ES es un perfil nacional basado en DCAT-AP.  
En esta PoC usamos un subconjunto "DCAT-like" (compatible en espiritu con DCAT-AP) para acotar alcance y riesgo.

DCAT-AP-ES (referencia) define principalmente: **Catálogo**, **Dataset**, **Distribución** y **Servicio de datos**.

OpenMetadata no representa DCAT 1:1; el objetivo del TFM es **alinear conceptos** usando el metamodelo de OM + gobierno + custom properties.

## Propiedades obligatorias DCAT-AP-ES (mínimo viable)

Estas propiedades se toman como **mínimo obligatorio** por entidad (perfil ES), y son la base del mapping:

- **Catálogo**
  - `dct:title`, `dct:description`, `dct:publisher`
  - `foaf:homepage`, `dcat:themeTaxonomy`
  - `dct:issued`, `dct:modified`
  - `dct:language`, `dct:license`, `dct:spatial`

- **Dataset**
  - `dct:title`, `dct:description`, `dct:publisher`, `dcat:theme`

- **Distribución**
  - `dcat:accessURL` (obligatorio)
  - Nota: `dct:license` se modela a nivel de Distribución (no de Dataset) en DCAT-AP-ES.

## Cobertura en esta PoC

- **Catálogo**: se exporta desde `governance_defaults.yaml` (titulo, descripción, publisher, homepage, themeTaxonomy, issued/modified, language, license, spatial).
- **Dataset**: se toma de `Table.displayName`/`description`, publisher/contact por defaults o CKAN, y `dcat:theme` desde tags `dcat_theme.*`.
- **Distribución**: se usa la primera resource CKAN para `dcat:accessURL`/`downloadURL`, y `dct:license` desde custom property.

## Decisiones de modelado (PoC)

- **dcat:Catalog**
  - En OpenMetadata: se representa como **Domain** (y convenciones de tags/owners).
  - Metadatos globales (publisher/contact/licencia por defecto): como **defaults** en configuración del ingestor y/o custom properties en assets.
  - Nota práctica: OpenMetadata no tiene una entidad `Catalog` DCAT nativa 1:1; por eso los metadatos globales del catálogo se mantienen en `governance_defaults.yaml` y se proyectan sobre assets/export.

- **dcat:Dataset**
  - En OpenMetadata: se representa como **Table** (o View) porque es el "asset gobernable" que el conector crea automáticamente.
  - `dct:title` / `dct:description`: se reflejan en `displayName` y `description`.
  - Otros campos DCAT-like: vía **custom properties** y **tags**.

- **dcat:Distribution**
  - En OpenMetadata (PoC): como custom properties a nivel de Table (p.ej. `dcat_access_url`, `dcat_download_url`).
  - Nota: DCAT permite multiples distribuciones; aqui usamos 1 por simplicidad.

- **dcat:DataService**
  - En OpenMetadata (PoC): como custom property (p.ej. `dcat_endpoint_url`) cuando aplica.

## Riesgo controlado (y como lo explicamos en la memoria)

- DCAT "dataset" != SQL "tabla" por definición.
  - En catálogos empresariales, el dataset suele materializarse como entidad técnica gobernable (table/view),
    y el resto de elementos (distribución/servicio) se modelan como enlaces o metadatos adicionales.
