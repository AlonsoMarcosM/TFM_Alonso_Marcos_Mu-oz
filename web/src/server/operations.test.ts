import { describe, expect, it } from "vitest";

import { excludedOperations, operations } from "./operations";

describe("operations catalog", () => {
  it("contains the scoped executable platform operations", () => {
    expect(operations.map((operation) => operation.id)).toEqual([
      "check-prereqs",
      "status-infra",
      "backup-openmetadata-state",
      "restore-openmetadata-state",
      "deploy-postgres-k8s",
      "launch-infra",
      "delete-cluster-preserve-state",
      "reset-platform-clean",
      "run-full-flow",
      "clear-openmetadata-postgres-source",
      "ingest-postgres",
      "bootstrap-governance",
      "refresh-governance-sheet",
      "validate-governance-sheet",
      "apply-governance",
      "workflow-dry-run",
      "workflow-apply",
      "export-dcat",
      "validate-dcat",
      "validate-runtime",
      "run-validation-suite",
      "render-validation-report",
      "validate-live-dcat",
    ]);
  });

  it("does not expose out-of-scope persistent processes or GitHub actions", () => {
    const commandText = operations.map((operation) => [operation.command, ...operation.args].join(" ")).join("\n");

    for (const excluded of excludedOperations) {
      expect(commandText).not.toContain(excluded);
    }
    expect(commandText.toLowerCase()).not.toContain("github");
    expect(commandText).not.toContain("port_forward_openmetadata.ps1");
  });

  it("marks destructive reset operations with confirmation text", () => {
    const destructiveIds = [
      "restore-openmetadata-state",
      "delete-cluster-preserve-state",
      "reset-platform-clean",
      "clear-openmetadata-postgres-source",
    ];
    for (const id of destructiveIds) {
      const operation = operations.find((item) => item.id === id);
      expect(operation?.risk).toBeTruthy();
      expect(operation?.confirmText).toBeTruthy();
    }
  });

  it("uses the double PostgreSQL ingestion route for the validation case", () => {
    const ingest = operations.find((operation) => operation.id === "ingest-postgres");
    const runtime = operations.find((operation) => operation.id === "validate-runtime");

    expect(ingest?.args).toContain(".\\scripts\\infra\\ingest_postgres_double.ps1");
    expect(runtime?.args.join(" ")).toContain("postgres_demo_service,postgres_validation_service");
  });
});
