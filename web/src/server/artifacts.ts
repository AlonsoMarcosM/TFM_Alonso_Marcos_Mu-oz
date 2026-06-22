import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";

import { isDemoMode } from "./demo";
import { sanitizePublicText } from "./publicSanitization";
import { repoPath } from "./repoPaths";

export const artifactFiles = [
  "tmp_pytest/prereqs_report.json",
  "tmp_pytest/validation_suite_summary.json",
  "tmp_pytest/validation_report.html",
  "tmp_pytest/validation_report.pdf",
  "tmp_pytest/runtime_validation_report.json",
  "tmp_pytest/validation_suite_catalog.jsonld",
  "tmp_pytest/validation_suite_shacl_report.ttl",
  "tmp_pytest/web_catalog.jsonld",
  "tmp_pytest/web_shacl_report.ttl",
  "tmp_pytest/web_runtime_report.json",
  "tmp_pytest/web_workflow_plan.json",
  "tmp_pytest/live_dcat_catalog.jsonld",
  "tmp_pytest/live_dcat_validation_report.ttl",
  "tmp_pytest/workflow_first_plan.json",
  "tmp_pytest/workflow_second_plan.json",
  "tfm_ingestor/src/tfm_ingestor/resources/shacl/manifest.json",
  "tfm_ingestor/config/operational_profile.yaml",
  "tfm_ingestor/config/gold_governance.csv",
];

export async function listArtifacts() {
  return Promise.all(
    artifactFiles.map(async (relativePath) => {
      const absolutePath = repoPath(...relativePath.split("/"));
      if (!fs.existsSync(absolutePath)) {
        return { path: relativePath, exists: false, size: 0, updatedAt: null };
      }
      const stat = await fsp.stat(absolutePath);
      return {
        path: relativePath,
        exists: true,
        size: stat.size,
        updatedAt: stat.mtime.toISOString(),
      };
    }),
  );
}

const CONTENT_TYPES: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".pdf": "application/pdf",
  ".json": "application/json; charset=utf-8",
  ".jsonld": "application/ld+json; charset=utf-8",
  ".ttl": "text/turtle; charset=utf-8",
  ".csv": "text/csv; charset=utf-8",
  ".yaml": "text/yaml; charset=utf-8",
  ".yml": "text/yaml; charset=utf-8",
};

export function artifactContentType(relativePath: string): string {
  const extension = path.extname(relativePath).toLowerCase();
  return CONTENT_TYPES[extension] ?? "text/plain; charset=utf-8";
}

export async function readArtifactRaw(
  relativePath: string,
): Promise<{ buffer: Buffer; contentType: string; filename: string }> {
  const normalized = relativePath.replaceAll("\\", "/");
  if (!artifactFiles.includes(normalized)) {
    throw new Error(`Artefacto no permitido: ${relativePath}`);
  }
  const absolutePath = repoPath(...normalized.split("/"));
  const extension = path.extname(normalized).toLowerCase();
  let buffer = await fsp.readFile(absolutePath);
  if (isDemoMode() && extension !== ".pdf") {
    buffer = Buffer.from(sanitizePublicText(buffer.toString("utf8")), "utf8");
  }
  return {
    buffer,
    contentType: artifactContentType(normalized),
    filename: normalized.split("/").pop() ?? "artefacto",
  };
}

export async function readArtifact(relativePath: string) {
  const normalized = relativePath.replaceAll("\\", "/");
  if (!artifactFiles.includes(normalized)) {
    throw new Error(`Artefacto no permitido: ${relativePath}`);
  }
  const absolutePath = repoPath(...normalized.split("/"));
  const extension = path.extname(normalized).toLowerCase();
  if (extension === ".pdf") {
    // El PDF es binario: no se previsualiza como texto. Se ofrece como
    // evidencia descargable; debe abrirse desde su ruta en disco.
    return {
      path: normalized,
      extension,
      content: `(Documento PDF binario. Ábrelo desde la ruta del repositorio: ${normalized})`,
    };
  }
  const rawContent = await fsp.readFile(absolutePath, "utf8");
  const content = isDemoMode() ? sanitizePublicText(rawContent) : rawContent;
  return {
    path: normalized,
    extension,
    content,
  };
}
