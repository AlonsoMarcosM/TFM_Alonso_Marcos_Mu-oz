import { describe, expect, it } from "vitest";

import { redactSecrets } from "./redactSecrets";

describe("redactSecrets", () => {
  it("removes known secret values from logs", () => {
    const redacted = redactSecrets("token=abc123secret", { OPENMETADATA_JWT_TOKEN: "abc123secret" });
    expect(redacted).toBe("token=[OPENMETADATA_JWT_TOKEN:redacted]");
  });
});
