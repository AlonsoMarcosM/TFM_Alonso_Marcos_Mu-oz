# Mapeo DCAT-AP-ES -> OpenMetadata (version simple)

DCAT-AP-ES (referencia) define principalmente: **Catalogo**, **Dataset**, **Distribucion** y **Servicio de datos**.

OpenMetadata no representa DCAT 1:1; el objetivo del TFM es **alinear conceptos** usando el metamodelo de OM + gobierno + custom properties.

## Decisiones de modelado (PoC)

- **dcat:Catalog**
  - En OpenMetadata: se representa como **Domain** (y convenciones de tags/owners).
  - Metadatos globales (publisher/contact/licencia por defecto): como **defaults** en configuracion del ingestor y/o custom properties en assets.

- **dcat:Dataset**
  - En OpenMetadata: se representa como **Table** (o View) porque es el "asset gobernable" que el conector crea automaticamente.
  - `dct:title` / `dct:description`: se reflejan en `displayName` y `description`.
  - Otros campos DCAT-like: via **custom properties** y **tags**.

- **dcat:Distribution**
  - En OpenMetadata (PoC): como custom properties a nivel de Table (p.ej. `dcat_access_url`, `dcat_download_url`).
  - Nota: DCAT permite multiples distribuciones; aqui usamos 1 por simplicidad.

- **dcat:DataService**
  - En OpenMetadata (PoC): como custom property (p.ej. `dcat_endpoint_url`) cuando aplica.

## Riesgo controlado (y como lo explicamos en la memoria)

- DCAT "dataset" != SQL "tabla" por definicion.
  - En catalogos empresariales, el dataset suele materializarse como entidad tecnica gobernable (table/view),
    y el resto de elementos (distribucion/servicio) se modelan como enlaces o metadatos adicionales.

