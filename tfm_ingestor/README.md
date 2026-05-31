# om_dcat_sync (alias `tfm_ingestor`)

CLI para enriquecer metadatos de gobierno en OpenMetadata y exportarlos como `DCAT-AP-ES`.

Incluye:

- enriquecimiento idempotente de metadatos sobre `Table/View`;
- hoja funcional CSV para curación no técnica;
- workflow canónico sobre activos PostgreSQL ingeridos en OpenMetadata;
- exportación JSON-LD con `Catalog`, `Dataset`, `Distribution`, `DataService` y `Agent`;
- validación SHACL reproducible con el caso `hvd`;
- validación estructural del estado vivo frente al SQL de referencia y la hoja funcional.

Perfil activo:

- `DCAT-AP-ES`
- caso de validación `hvd`
- datasets `gold` tratados como HVD de la plataforma para ejercitar la extensión y su validación

Documentación de uso:

- `../docs/tfm_ingestor.md`
