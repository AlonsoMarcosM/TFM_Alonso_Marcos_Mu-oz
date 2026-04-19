import fsp from "node:fs/promises";

import { allowedHvdCategoryValues, allowedThemeValues } from "../shared/governanceOptions";
import { repoPath } from "./repoPaths";

export const governanceColumns = [
  "publicar",
  "schema_name",
  "table_name",
  "table_fqn",
  "titulo_dataset",
  "descripcion_dataset",
  "publicador",
  "tematica_dcat",
  "categoria_hvd",
  "access_url_distribucion",
] as const;

export type GovernanceColumn = (typeof governanceColumns)[number];
export type GovernanceRow = Record<GovernanceColumn, string>;

const readonlyColumns = new Set<GovernanceColumn>(["schema_name", "table_name", "table_fqn"]);

export function governanceSheetPath(): string {
  return repoPath("tfm_ingestor", "config", "gold_governance.csv");
}

function parseCsvLine(line: string): string[] {
  const out: string[] = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && quoted && next === '"') {
      current += '"';
      index += 1;
      continue;
    }
    if (char === '"') {
      quoted = !quoted;
      continue;
    }
    if (char === ";" && !quoted) {
      out.push(current);
      current = "";
      continue;
    }
    current += char;
  }
  out.push(current);
  return out;
}

function escapeCsvValue(value: string): string {
  if (!/[;"\r\n]/.test(value)) {
    return value;
  }
  return `"${value.replaceAll('"', '""')}"`;
}

export async function readGovernanceSheet(): Promise<GovernanceRow[]> {
  const raw = await fsp.readFile(governanceSheetPath(), "utf8");
  const clean = raw.replace(/^\uFEFF/, "").trimEnd();
  const lines = clean.split(/\r?\n/).filter(Boolean);
  const header = parseCsvLine(lines[0] ?? "");
  const missing = governanceColumns.filter((column) => !header.includes(column));
  if (missing.length > 0) {
    throw new Error(`Faltan columnas requeridas: ${missing.join(", ")}`);
  }

  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    const row = {} as GovernanceRow;
    governanceColumns.forEach((column) => {
      const index = header.indexOf(column);
      row[column] = values[index] ?? "";
    });
    return row;
  });
}

export function validateGovernanceRows(rows: GovernanceRow[]): string[] {
  const errors: string[] = [];
  rows.forEach((row, index) => {
    const line = index + 2;
    const publish = row.publicar.trim().toLowerCase();
    if (!["si", "no"].includes(publish)) {
      errors.push(`Fila ${line}: publicar debe ser si o no.`);
    }
    if (publish === "si") {
      if (!row.titulo_dataset.trim()) {
        errors.push(`Fila ${line}: titulo_dataset es obligatorio.`);
      }
      if (!row.descripcion_dataset.trim()) {
        errors.push(`Fila ${line}: descripcion_dataset es obligatoria.`);
      }
      if (!row.tematica_dcat.trim()) {
        errors.push(`Fila ${line}: tematica_dcat es obligatoria.`);
      } else if (!allowedThemeValues.includes(row.tematica_dcat.trim())) {
        errors.push(`Fila ${line}: tematica_dcat debe ser una de: ${allowedThemeValues.join(", ")}.`);
      }
      if (!row.categoria_hvd.trim()) {
        errors.push(`Fila ${line}: categoria_hvd es obligatoria.`);
      } else if (!allowedHvdCategoryValues.includes(row.categoria_hvd.trim())) {
        errors.push(`Fila ${line}: categoria_hvd debe ser una de: ${allowedHvdCategoryValues.join(", ")}.`);
      }
      try {
        const url = new URL(row.access_url_distribucion);
        if (!["http:", "https:"].includes(url.protocol)) {
          errors.push(`Fila ${line}: access_url_distribucion debe ser http(s).`);
        }
      } catch {
        errors.push(`Fila ${line}: access_url_distribucion debe ser una URL válida.`);
      }
    }
  });
  return errors;
}

export async function writeGovernanceSheet(rows: GovernanceRow[]): Promise<void> {
  const current = await readGovernanceSheet();
  const currentByFqn = new Map(current.map((row) => [row.table_fqn, row]));
  const errors = validateGovernanceRows(rows);
  if (errors.length > 0) {
    throw new Error(errors.join("\n"));
  }

  const normalizedRows = rows.map((row) => {
    const existing = currentByFqn.get(row.table_fqn);
    const out = { ...row };
    for (const column of readonlyColumns) {
      if (existing) {
        out[column] = existing[column];
      }
    }
    return out;
  });

  const lines = [
    governanceColumns.join(";"),
    ...normalizedRows.map((row) => governanceColumns.map((column) => escapeCsvValue(row[column] ?? "")).join(";")),
  ];
  await fsp.writeFile(governanceSheetPath(), `\uFEFF${lines.join("\n")}\n`, "utf8");
}
