import { describe, expect, it } from "vitest";

import { excludedOperations, operations } from "./operations";

describe("operations catalog", () => {
  it("contains the scoped executable demo operations", () => {
    expect(operations.map((operation) => operation.id)).toEqual([
      "check-prereqs",
      "status-infra",
      "backup-openmetadata-state",
      "restore-openmetadata-state",
      "deploy-postgres-k8s",
      "launch-infra",
      "delete-cluster-preserve-state",
      "reset-poc-clean",
      "run-full-flow",
      "ingest-postgres",
      "bootstrap-governance",
      "validate-governance-sheet",
      "workflow-dry-run",
      "workflow-apply",
      "export-dcat",
      "validate-dcat",
      "validate-runtime",
      "run-validation-suite",
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
    const destructiveIds = ["restore-openmetadata-state", "delete-cluster-preserve-state", "reset-poc-clean"];
    for (const id of destructiveIds) {
      const operation = operations.find((item) => item.id === id);
      expect(operation?.risk).toBeTruthy();
      expect(operation?.confirmText).toBeTruthy();
    }
  });
});
