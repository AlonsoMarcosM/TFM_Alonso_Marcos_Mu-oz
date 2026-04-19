export type ControlledOption = {
  value: string;
  label: string;
  uri?: string;
  hint?: string;
};

const sectorBaseUri = "http://datos.gob.es/kos/sector-publico/sector";

export const publishOptions: ControlledOption[] = [
  {
    value: "si",
    label: "si - publicar en el catálogo",
    hint: "La fila se exporta como dcat:Dataset y debe tener todos los campos funcionales.",
  },
  {
    value: "no",
    label: "no - dejar fuera de la publicación",
    hint: "La fila queda documentada, pero no entra en el contrato publicable de la PoC.",
  },
];

export const themeOptions: ControlledOption[] = [
  { value: "ciencia_tecnologia", label: "Ciencia y tecnología", uri: `${sectorBaseUri}/ciencia-tecnologia` },
  { value: "comercio", label: "Comercio", uri: `${sectorBaseUri}/comercio` },
  { value: "cultura_ocio", label: "Cultura y ocio", uri: `${sectorBaseUri}/cultura-ocio` },
  { value: "demografia", label: "Demografía", uri: `${sectorBaseUri}/demografia` },
  { value: "deporte", label: "Deporte", uri: `${sectorBaseUri}/deporte` },
  { value: "economia", label: "Economía", uri: `${sectorBaseUri}/economia` },
  { value: "educacion", label: "Educación", uri: `${sectorBaseUri}/educacion` },
  { value: "empleo", label: "Empleo", uri: `${sectorBaseUri}/empleo` },
  { value: "energia", label: "Energía", uri: `${sectorBaseUri}/energia` },
  { value: "hacienda", label: "Hacienda", uri: `${sectorBaseUri}/hacienda` },
  { value: "industria", label: "Industria", uri: `${sectorBaseUri}/industria` },
  { value: "legislacion_justicia", label: "Legislación y justicia", uri: `${sectorBaseUri}/legislacion-justicia` },
  { value: "medio_ambiente", label: "Medio ambiente", uri: `${sectorBaseUri}/medio-ambiente` },
  { value: "medio_rural_pesca", label: "Medio rural y pesca", uri: `${sectorBaseUri}/medio-rural-pesca` },
  { value: "salud", label: "Salud", uri: `${sectorBaseUri}/salud` },
  { value: "sector_publico", label: "Sector público", uri: `${sectorBaseUri}/sector-publico` },
  { value: "seguridad", label: "Seguridad", uri: `${sectorBaseUri}/seguridad` },
  { value: "sociedad_bienestar", label: "Sociedad y bienestar", uri: `${sectorBaseUri}/sociedad-bienestar` },
  { value: "transporte", label: "Transporte", uri: `${sectorBaseUri}/transporte` },
  { value: "turismo", label: "Turismo", uri: `${sectorBaseUri}/turismo` },
  {
    value: "urbanismo_infraestructuras",
    label: "Urbanismo e infraestructuras",
    uri: `${sectorBaseUri}/urbanismo-infraestructuras`,
  },
  { value: "vivienda", label: "Vivienda", uri: `${sectorBaseUri}/vivienda` },
];

export const hvdCategoryOptions: ControlledOption[] = [
  {
    value: "geoespacial",
    label: "Geoespacial",
    uri: "http://data.europa.eu/bna/c_ac64a52d",
  },
  {
    value: "observacion_de_la_tierra_y_medio_ambiente",
    label: "Observación de la Tierra y medio ambiente",
    uri: "http://data.europa.eu/bna/c_dd313021",
  },
  {
    value: "meteorologia",
    label: "Meteorología",
    uri: "http://data.europa.eu/bna/c_164e0bf5",
  },
  {
    value: "estadisticas",
    label: "Estadística",
    uri: "http://data.europa.eu/bna/c_e1da4e07",
  },
  {
    value: "sociedades_y_propiedad_de_sociedades",
    label: "Sociedades y propiedad de sociedades",
    uri: "http://data.europa.eu/bna/c_a9135398",
  },
  {
    value: "movilidad",
    label: "Movilidad",
    uri: "http://data.europa.eu/bna/c_b79e35eb",
  },
];

export const fieldGuidance = [
  {
    field: "publicar",
    text: "Usa si para datasets que se van a defender y validar en la PoC. Usa no si la fila está incompleta o no debe salir en el catálogo.",
  },
  {
    field: "titulo_dataset",
    text: "Nombre funcional, claro y legible. Evita códigos internos y nombres técnicos de tabla.",
  },
  {
    field: "descripcion_dataset",
    text: "Obligatoria si publicar=si. Debe explicar qué contiene el dataset, granularidad y finalidad de reutilización.",
  },
  {
    field: "publicador",
    text: "Nombre de la organización responsable. Si está vacío se sugiere el publicador demo configurado.",
  },
  {
    field: "tematica_dcat",
    text: "Sector NTI-RISP usado en dcat:theme. La lista procede de las SHACL locales congeladas de DCAT-AP-ES.",
  },
  {
    field: "categoria_hvd",
    text: "Categoría superior del vocabulario europeo HVD. En la PoC se usan Movilidad y Estadística, pero la app ofrece las seis categorías oficiales.",
  },
  {
    field: "access_url_distribucion",
    text: "URL http(s) de acceso a la distribución. Para la demo puede ser una URL estable de evidencia o documentación publicable.",
  },
];

export const allowedThemeValues = themeOptions.map((option) => option.value);
export const allowedHvdCategoryValues = hvdCategoryOptions.map((option) => option.value);

export type GovernanceSuggestion = {
  publicar: string;
  titulo_dataset: string;
  descripcion_dataset: string;
  publicador: string;
  tematica_dcat: string;
  categoria_hvd: string;
  access_url_distribucion: string;
};

export const defaultPublisher = "UCLM (Demo)";

export const defaultSuggestionsByTable: Record<string, GovernanceSuggestion> = {
  agenda_cultural_publica: {
    publicar: "si",
    titulo_dataset: "Agenda cultural pública",
    descripcion_dataset:
      "Relación de eventos culturales públicos con fecha, municipio, categoría y asistentes estimados para difusión abierta.",
    publicador: defaultPublisher,
    tematica_dcat: "cultura_ocio",
    categoria_hvd: "estadisticas",
    access_url_distribucion: "https://www.uclm.es/datos/poc/gold/agenda-cultural-publica",
  },
  movilidad_resumen_municipio: {
    publicar: "si",
    titulo_dataset: "Resumen de movilidad por municipio",
    descripcion_dataset:
      "Resumen diario agregado de viajes por municipio para su publicación como conjunto de datos abierto.",
    publicador: defaultPublisher,
    tematica_dcat: "transporte",
    categoria_hvd: "movilidad",
    access_url_distribucion: "https://www.uclm.es/datos/poc/gold/movilidad-resumen-municipio",
  },
};

export function fallbackSuggestion(tableName: string, schemaName = "gold"): GovernanceSuggestion {
  const normalizedTitle = tableName
    .replaceAll("_", " ")
    .replace(/\b\w/g, (value) => value.toUpperCase());
  const urlSlug = tableName.replaceAll("_", "-").toLowerCase();
  return {
    publicar: "si",
    titulo_dataset: normalizedTitle || "Dataset gold de la PoC",
    descripcion_dataset: `Dataset publicable de la PoC para ${tableName || "una tabla gold"}.`,
    publicador: defaultPublisher,
    tematica_dcat: "transporte",
    categoria_hvd: "movilidad",
    access_url_distribucion: `https://www.uclm.es/datos/poc/${schemaName || "gold"}/${urlSlug || "dataset"}`,
  };
}
