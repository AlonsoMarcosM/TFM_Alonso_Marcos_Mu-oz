import fs from "node:fs";
import path from "node:path";

import { artifactFiles } from "./artifacts";
import type { Operation } from "./operations";
import { repoPath } from "./repoPaths";
import { redactSecrets } from "./redactSecrets";

export type JobArtifactResult = {
  path: string;
  exists: boolean;
  size: number;
  updatedAt: string | null;
  viewable: boolean;
  kind: string;
  summary: string[];
  preview?: string;
};

export type JobResult = {
  ok: boolean;
  message: string;
  details: string[];
  durationMs?: number;
  artifacts: JobArtifactResult[];
};

type JobForResult = {
  status: string;
  startedAt?: string;
  finishedAt?: string;
  exitCode?: number | null;
  error?: string;
  log: string;
};

const PREVIEW_LIMIT = 1800;

function truncate(value: string, limit = PREVIEW_LIMIT): string {
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, limit)}\n...`;
}

function unique(lines: string[]): string[] {
  return Array.from(new Set(lines.filter((line) => line.trim().length > 0)));
}

function yesNo(value: unknown): string {
  return value ? "sí" : "no";
}

function countItems(value: unknown): number | null {
  if (Array.isArray(value)) {
    return value.length;
  }
  if (typeof value === "number") {
    return value;
  }
  return null;
}

function getObject(value: unknown, key: string): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  const item = (value as Record<string, unknown>)[key];
  if (!item || typeof item !== "object" || Array.isArray(item)) {
    return null;
  }
  return item as Record<string, unknown>;
}

function hasKey(value: Record<string, unknown>, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(value, key);
}

function summarizeWorkflow(value: Record<string, unknown>, prefix = "Workflow"): string[] {
  const lines: string[] = [];
  if (hasKey(value, "dry_run")) {
    lines.push(`${prefix}: dry-run=${yesNo(value.dry_run)}.`);
  }
  if (hasKey(value, "tables_discovered")) {
    lines.push(`${prefix}: tablas descubiertas ${value.tables_discovered}.`);
  }
  if (hasKey(value, "sheet_rows_loaded")) {
    lines.push(`${prefix}: filas de hoja cargadas ${value.sheet_rows_loaded}.`);
  }
  if (hasKey(value, "sheet_valid")) {
    lines.push(`${prefix}: hoja funcional válida=${yesNo(value.sheet_valid)}.`);
  }
  if (value.sheet_validation_error) {
    lines.push(`${prefix}: ${String(value.sheet_validation_error)}`);
  }
  return lines;
}

function summarizeSync(value: Record<string, unknown>, prefix = "Sincronización"): string[] {
  const lines: string[] = [];
  const planned = countItems(value.planned);
  if (planned !== null) {
    lines.push(`${prefix}: cambios planificados ${planned}.`);
  }
  if (hasKey(value, "applied")) {
    lines.push(`${prefix}: cambios aplicados ${value.applied}.`);
  }
  if (hasKey(value, "dry_run")) {
    lines.push(`${prefix}: dry-run=${yesNo(value.dry_run)}.`);
  }
  return lines;
}

function summarizeValidation(value: Record<string, unknown>, prefix = "Validación"): string[] {
  const lines: string[] = [];
  if (hasKey(value, "conforms")) {
    lines.push(`${prefix}: conformidad=${yesNo(value.conforms)}.`);
  }
  if (hasKey(value, "violations")) {
    lines.push(`${prefix}: violaciones ${value.violations}.`);
  }
  if (hasKey(value, "warnings")) {
    lines.push(`${prefix}: warnings ${value.warnings}.`);
  }
  if (hasKey(value, "tables_exported")) {
    lines.push(`${prefix}: tablas exportadas ${value.tables_exported}.`);
  }
  if (hasKey(value, "preview_dataset_count")) {
    lines.push(`${prefix}: datasets en catálogo ${value.preview_dataset_count}.`);
  }
  return lines;
}

function summarizeRuntime(value: Record<string, unknown>, prefix = "Estado vivo"): string[] {
  const technical = getObject(value, "technical");
  const governance = getObject(value, "governance");
  if (!technical && !governance) {
    return [];
  }

  const lines: string[] = [];
  if (hasKey(value, "conforms")) {
    lines.push(`${prefix}: conformidad=${yesNo(value.conforms)}.`);
  }
  if (technical && hasKey(technical, "conforms")) {
    lines.push(`${prefix}: contrato técnico=${yesNo(technical.conforms)}.`);
  }
  if (governance && hasKey(governance, "conforms")) {
    lines.push(`${prefix}: gobierno=${yesNo(governance.conforms)}.`);
  }
  return lines;
}

function summarizePrereqs(value: Record<string, unknown>): string[] {
  if (!Array.isArray(value.commands) && !Array.isArray(value.missing)) {
    return [];
  }

  const lines: string[] = [];
  if (hasKey(value, "conforms")) {
    lines.push(`Prerrequisitos: conformidad=${yesNo(value.conforms)}.`);
  }
  if (Array.isArray(value.commands)) {
    const available = value.commands.filter((item) => Boolean((item as Record<string, unknown>).available)).length;
    lines.push(`Prerrequisitos: comandos disponibles ${available}/${value.commands.length}.`);
  }
  if (Array.isArray(value.missing)) {
    lines.push(value.missing.length > 0 ? `Faltan: ${value.missing.join(", ")}.` : "No faltan comandos obligatorios.");
  }
  return lines;
}

function summarizeBootstrap(value: Record<string, unknown>): string[] {
  const keys = [
    "classifications_created",
    "classifications_existing",
    "tags_created",
    "tags_existing",
    "custom_properties_created",
    "custom_properties_existing",
  ];
  if (!keys.some((key) => Array.isArray(value[key]))) {
    return [];
  }
  return [
    `Gobierno OpenMetadata: tags creados ${countItems(value.tags_created) ?? 0}, existentes ${countItems(value.tags_existing) ?? 0}.`,
    `Gobierno OpenMetadata: custom properties creadas ${countItems(value.custom_properties_created) ?? 0}, existentes ${countItems(value.custom_properties_existing) ?? 0}.`,
  ];
}

function summarizeJsonLd(value: Record<string, unknown>): string[] {
  const graph = value["@graph"];
  if (!Array.isArray(graph)) {
    return [];
  }
  const typeCounts = new Map<string, number>();
  for (const node of graph) {
    if (!node || typeof node !== "object") {
      continue;
    }
    const rawType = (node as Record<string, unknown>)["@type"];
    const types = Array.isArray(rawType) ? rawType : [rawType];
    for (const item of types) {
      if (!item) {
        continue;
      }
      const name = String(item).split(":").pop() ?? String(item);
      typeCounts.set(name, (typeCounts.get(name) ?? 0) + 1);
    }
  }
  const datasetCount = typeCounts.get("Dataset") ?? 0;
  const distributionCount = typeCounts.get("Distribution") ?? 0;
  const dataServiceCount = typeCounts.get("DataService") ?? 0;
  return [
    `JSON-LD: nodos en @graph ${graph.length}.`,
    `JSON-LD: datasets ${datasetCount}, distribuciones ${distributionCount}, data services ${dataServiceCount}.`,
  ];
}

export function summarizeStructuredValue(value: unknown): string[] {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return [];
  }
  const object = value as Record<string, unknown>;
  const lines: string[] = [];

  if (hasKey(object, "output")) {
    lines.push(`Salida escrita en ${String(object.output)}.`);
  }
  if (hasKey(object, "row_count")) {
    lines.push(`Filas validadas: ${String(object.row_count)}.`);
  }
  if (hasKey(object, "conforms")) {
    lines.push(`Conformidad: ${yesNo(object.conforms)}.`);
  }
  if (hasKey(object, "tables_detected")) {
    lines.push(`Tablas detectadas: ${String(object.tables_detected)}.`);
  }

  lines.push(...summarizePrereqs(object));
  lines.push(...summarizeBootstrap(object));
  lines.push(...summarizeJsonLd(object));

  const workflow = getObject(object, "workflow");
  if (workflow) {
    lines.push(...summarizeWorkflow(workflow));
  }
  const sync = getObject(object, "sync");
  if (sync) {
    lines.push(...summarizeSync(sync));
  }
  const exportSummary = getObject(object, "export");
  if (exportSummary) {
    lines.push(...summarizeValidation(exportSummary, "Exportación"));
  }
  const validation = getObject(object, "validation");
  if (validation) {
    lines.push(...summarizeValidation(validation, "Validación SHACL"));
  }
  const runtimeValidation = getObject(object, "runtime_validation");
  if (runtimeValidation) {
    lines.push(...summarizeRuntime(runtimeValidation, "Estado vivo"));
  } else {
    lines.push(...summarizeRuntime(object));
  }
  const idempotence = getObject(object, "idempotence");
  if (idempotence && hasKey(idempotence, "conforms")) {
    lines.push(`Idempotencia: conformidad=${yesNo(idempotence.conforms)}.`);
  }
  const firstWorkflow = getObject(object, "first_workflow");
  const firstSync = firstWorkflow ? getObject(firstWorkflow, "sync") : null;
  if (firstSync) {
    lines.push(...summarizeSync(firstSync, "Primera ejecución"));
  }
  const secondWorkflow = getObject(object, "second_workflow");
  const secondSync = secondWorkflow ? getObject(secondWorkflow, "sync") : null;
  if (secondSync) {
    lines.push(...summarizeSync(secondSync, "Segunda ejecución"));
  }

  return unique(lines).slice(0, 12);
}

export function extractLastJsonObject(text: string): unknown | null {
  let start = -1;
  let depth = 0;
  let inString = false;
  let escaped = false;
  let last: unknown | null = null;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (char === "\\") {
        escaped = true;
      } else if (char === "\"") {
        inString = false;
      }
      continue;
    }
    if (char === "\"") {
      inString = true;
      continue;
    }
    if (char === "{") {
      if (depth === 0) {
        start = index;
      }
      depth += 1;
      continue;
    }
    if (char === "}") {
      depth -= 1;
      if (depth === 0 && start >= 0) {
        const candidate = text.slice(start, index + 1);
        try {
          last = JSON.parse(candidate) as unknown;
        } catch {
          // Ignore non-JSON fragments found in command output.
        }
        start = -1;
      }
    }
  }

  return last;
}

function summarizeCsv(content: string): string[] {
  const lines = content.split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (lines.length === 0) {
    return ["CSV vacío."];
  }
  const separator = lines[0].includes(";") ? ";" : ",";
  const headers = lines[0].replace(/^\uFEFF/, "").split(separator);
  return [`CSV: ${Math.max(lines.length - 1, 0)} filas de datos.`, `Columnas: ${headers.join(", ")}.`];
}

function summarizeTextArtifact(content: string, extension: string): string[] {
  const lines = content.split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (extension === ".ttl") {
    return [`TTL: ${lines.length} líneas no vacías.`];
  }
  if (extension === ".yaml" || extension === ".yml") {
    return [`YAML: ${lines.length} líneas no vacías.`];
  }
  return [`Texto: ${lines.length} líneas no vacías.`];
}

export function summarizeArtifact(relativePath: string): JobArtifactResult {
  const normalized = relativePath.replaceAll("\\", "/");
  const absolutePath = repoPath(...normalized.split("/"));
  const viewable = artifactFiles.includes(normalized);
  const extension = path.extname(normalized).toLowerCase();
  const kind = extension ? extension.slice(1).toUpperCase() : "archivo";

  if (!fs.existsSync(absolutePath)) {
    return {
      path: normalized,
      exists: false,
      size: 0,
      updatedAt: null,
      viewable,
      kind,
      summary: ["No existe al terminar el job."],
    };
  }

  const stat = fs.statSync(absolutePath);
  const base = {
    path: normalized,
    exists: true,
    size: stat.size,
    updatedAt: stat.mtime.toISOString(),
    viewable,
    kind,
  };

  if (extension === ".sql") {
    return {
      ...base,
      summary: [`Snapshot SQL generado. Tamaño: ${stat.size} bytes.`],
    };
  }

  try {
    const content = fs.readFileSync(absolutePath, "utf8");
    if (extension === ".json" || extension === ".jsonld") {
      const parsed = JSON.parse(content) as unknown;
      const preview = truncate(JSON.stringify(parsed, null, 2));
      return {
        ...base,
        summary: summarizeStructuredValue(parsed),
        preview: redactSecrets(preview),
      };
    }
    if (extension === ".csv") {
      return {
        ...base,
        summary: summarizeCsv(content),
        preview: redactSecrets(truncate(content)),
      };
    }
    return {
      ...base,
      summary: summarizeTextArtifact(content, extension),
      preview: redactSecrets(truncate(content)),
    };
  } catch (error) {
    return {
      ...base,
      summary: [`Artefacto generado, pero no se pudo resumir: ${error instanceof Error ? error.message : "error desconocido"}.`],
    };
  }
}

function durationMs(job: JobForResult): number | undefined {
  if (!job.startedAt || !job.finishedAt) {
    return undefined;
  }
  const started = Date.parse(job.startedAt);
  const finished = Date.parse(job.finishedAt);
  if (Number.isNaN(started) || Number.isNaN(finished)) {
    return undefined;
  }
  return Math.max(0, finished - started);
}

export function buildJobResult(operation: Operation, job: JobForResult): JobResult {
  const ok = job.status === "success";
  const artifacts = operation.artifacts.map((artifact) => summarizeArtifact(artifact));
  const generatedArtifacts = artifacts.filter((artifact) => artifact.exists);
  const consoleJson = extractLastJsonObject(job.log);
  const consoleSummary = summarizeStructuredValue(consoleJson);
  const duration = durationMs(job);
  const details = unique([
    ...consoleSummary,
    operation.artifacts.length > 0
      ? `Artefactos generados: ${generatedArtifacts.length}/${operation.artifacts.length}.`
      : "La operación no declara artefactos persistentes; la evidencia principal es el log.",
    duration !== undefined ? `Duración: ${(duration / 1000).toFixed(1)} s.` : "",
    job.exitCode !== undefined ? `Código de salida: ${job.exitCode ?? "sin código"}.` : "",
    job.error ? `Error: ${job.error}` : "",
  ]);

  return {
    ok,
    message: ok
      ? `${operation.title} finalizó correctamente.`
      : `${operation.title} terminó con errores. Revisa el log y los artefactos parciales.`,
    details,
    durationMs: duration,
    artifacts,
  };
}
