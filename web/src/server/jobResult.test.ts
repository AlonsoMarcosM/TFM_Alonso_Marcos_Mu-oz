import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { buildJobResult, extractLastJsonObject, summarizeArtifact, summarizeStructuredValue } from "./jobResult";
import { operations } from "./operations";

let previousRepoRoot: string | undefined;
let tempRepoRoot: string;

beforeEach(() => {
  previousRepoRoot = process.env.TFM_REPO_ROOT;
  tempRepoRoot = fs.mkdtempSync(path.join(os.tmpdir(), "tfm-web-job-result-"));
  fs.mkdirSync(path.join(tempRepoRoot, "tmp_pytest"), { recursive: true });
  process.env.TFM_REPO_ROOT = tempRepoRoot;
});

afterEach(() => {
  if (previousRepoRoot === undefined) {
    delete process.env.TFM_REPO_ROOT;
  } else {
    process.env.TFM_REPO_ROOT = previousRepoRoot;
  }
  fs.rmSync(tempRepoRoot, { recursive: true, force: true });
});

describe("job result summaries", () => {
  it("builds a visible success result from console JSON and operation artifacts", () => {
    const workflowResult = {
      workflow: {
        dry_run: true,
        tables_discovered: 2,
        sheet_rows_loaded: 2,
        sheet_valid: true,
      },
      sync: {
        dry_run: true,
        planned: [{ table: "gold.movilidad_resumen_municipio" }],
        applied: 0,
      },
      export: null,
      validation: null,
    };
    fs.writeFileSync(
      path.join(tempRepoRoot, "tmp_pytest", "web_workflow_plan.json"),
      JSON.stringify(workflowResult, null, 2),
      "utf8",
    );

    const operation = operations.find((item) => item.id === "workflow-dry-run");
    if (!operation) {
      throw new Error("Missing workflow-dry-run operation");
    }
    const result = buildJobResult(operation, {
      status: "success",
      startedAt: "2026-04-19T10:00:00.000Z",
      finishedAt: "2026-04-19T10:00:01.500Z",
      exitCode: 0,
      log: `Salida previa\n${JSON.stringify(workflowResult, null, 2)}\n`,
    });

    expect(result.ok).toBe(true);
    expect(result.message).toContain("finalizó correctamente");
    expect(result.details).toContain("Workflow: hoja funcional válida=sí.");
    expect(result.details).toContain("Artefactos generados: 1/1.");
    expect(result.artifacts[0]?.summary).toContain("Sincronización: cambios planificados 1.");
    expect(result.artifacts[0]?.preview).toContain("tables_discovered");
  });

  it("summarizes JSON-LD catalog artifacts as visible evidence", () => {
    fs.writeFileSync(
      path.join(tempRepoRoot, "tmp_pytest", "web_catalog.jsonld"),
      JSON.stringify({
        "@context": {},
        "@graph": [
          { "@id": "catalog", "@type": "dcat:Catalog" },
          { "@id": "dataset-1", "@type": "dcat:Dataset" },
          { "@id": "distribution-1", "@type": "dcat:Distribution" },
          { "@id": "service-1", "@type": "dcat:DataService" },
        ],
      }),
      "utf8",
    );

    const artifact = summarizeArtifact("tmp_pytest/web_catalog.jsonld");

    expect(artifact.exists).toBe(true);
    expect(artifact.viewable).toBe(true);
    expect(artifact.summary).toContain("JSON-LD: nodos en @graph 4.");
    expect(artifact.summary).toContain("JSON-LD: datasets 1, distribuciones 1, data services 1.");
  });

  it("extracts the last structured JSON object from mixed logs", () => {
    const parsed = extractLastJsonObject('log {"first": true}\nmore\n{"second": {"ok": true}}\n');
    expect(parsed).toEqual({ second: { ok: true } });
  });

  it("does not mislabel generic conformance JSON as prereqs or runtime", () => {
    const summary = summarizeStructuredValue({ conforms: true, row_count: 2, errors: [] });

    expect(summary).toContain("Conformidad: sí.");
    expect(summary).toContain("Filas validadas: 2.");
    expect(summary.some((line) => line.startsWith("Prerrequisitos:"))).toBe(false);
    expect(summary.some((line) => line.startsWith("Estado vivo:"))).toBe(false);
  });
});
